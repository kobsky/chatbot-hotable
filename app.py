from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS # Pozwala na komunikację z przeglądarką
from nlp_engine import ChatbotBrain
from db_handler import DatabaseHandler
from entities import RESTAURANT_DESCRIPTIONS, RESTAURANT_DETAILS

app = Flask(__name__)
CORS(app) # Odblokowuje dostęp dla widgetu HTML

# Inicjalizacja komponentów (Mózg + Baza)
print("⏳ Uruchamianie systemu...")
bot = ChatbotBrain()
db = DatabaseHandler()
print("🚀 System gotowy! Serwer działa.")

CONTEXT = {"last_restaurant": None}  # Globalna pamięć (uproszczona dla MVP)

@app.route('/')
def index():
    return send_from_directory('.', 'test_widget.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    # 1. Analiza NLP (L9 - Potok klasyfikacji)
    intent = bot.predict_intent(user_message)
    entities = bot.extract_entities(user_message)
    
    print(f"📩 Msg: '{user_message}' | Intent: {intent} | Entities: {entities}")

    response_text = ""

    # 1. Próba pobrania restauracji z bieżącej wiadomości
    restaurant_name = entities.get("restaurant")
    
    # 2. Zarządzanie Kontekstem
    if restaurant_name:
        CONTEXT["last_restaurant"] = restaurant_name  # Aktualizuj pamięć
    else:
        restaurant_name = CONTEXT["last_restaurant"]  # Użyj pamięci

    # 2. Logika Biznesowa (Router intencji)
    if intent == "list_restaurants":
        response_text = (
            "Aktualnie współpracujemy z 3 wyjątkowymi lokalami:\n"
            "1. 🍔 **Neon** (StreetFood & Bary)"
            "2. 🍝 **Porto Azzurro** (Śródziemnomorska)"
            "3. 🥗 **Zielnik** (Polska & Nowoczesna)"
            "O którym z nich chcesz dowiedzieć się więcej?"
        )
        return jsonify({"response": response_text})
        
    if intent == "restaurant_info":
        # Próba pobrania z kontekstu, jeśli nie ma w wiadomości
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            restaurant_name = CONTEXT["last_restaurant"]
        
        if restaurant_name:
            # Aktualizuj kontekst na wszelki wypadek
            CONTEXT["last_restaurant"] = restaurant_name 
            
            description = RESTAURANT_DESCRIPTIONS.get(restaurant_name)
            if description:
                return jsonify({"response": description})
            else:
                return jsonify({"response": f"Brak opisu dla {restaurant_name}."})
        else:
             return jsonify({"response": "O której restauracji chcesz posłuchać? Mamy Neon, Zielnik i Porto Azzurro."})
    
    if intent == "check_contact":
        if restaurant_name:
            details = RESTAURANT_DETAILS.get(restaurant_name)
            if details:
                return jsonify({"response": f"📍 Adres: {details['address']}\n📞 Telefon: {details['phone']}"})
        return jsonify({"response": "Podaj nazwę restauracji, a podam Ci jej adres i numer telefonu."})

    if intent == "check_hours":
        if restaurant_name:
             details = RESTAURANT_DETAILS.get(restaurant_name)
             if details:
                return jsonify({"response": f"🕒 {restaurant_name} jest otwarte: {details['hours']}"})
        return jsonify({"response": "Większość lokali działa od 9:00 do 21:00. O który konkretnie pytasz?"})

    if intent == "check_capacity":
        if restaurant_name:
             details = RESTAURANT_DETAILS.get(restaurant_name)
             if details:
                return jsonify({"response": f"🏠 {restaurant_name} posiada łącznie {details['max_tables']} stolików."})
        return jsonify({"response": "Każdy lokal ma inną wielkość. O który pytasz?"})
    
    # --- SCENARIUSZ 1: Szukanie po kuchni ---
    if intent == 'search_cuisine':
        cuisine = entities.get('cuisine')
        if cuisine:
            # Pytamy bazę danych (L11 Integration)
            restaurants = db.get_restaurants_by_cuisine(cuisine)
            if restaurants:
                # FIX: Zapamiętaj znalezioną restaurację w kontekście!
                CONTEXT["last_restaurant"] = restaurants[0]['name']
                response_text = f"Mam kilka propozycji w kategorii {cuisine}:<br>"
                for r in restaurants:
                    # Dodajemy info o stolikach
                    seats = r['available_tables']
                    icon = "🟢" if seats > 0 else "🔴"
                    response_text += f"- <b>{r['name']}</b> ({icon} Wolne stoliki: {seats})<br>"
            else:
                response_text = f"Przykro mi, ale nie znalazłem restauracji typu {cuisine} w naszej bazie. 😔"
        else:
            # Bot zrozumiał intencję, ale nie wyłapał nazwy kuchni
            response_text = "Jasne, chętnie coś polecę. Ale na jaką kuchnię masz ochotę? (np. Polska, Włoska, StreetFood)"

    # --- SCENARIUSZ 2: Sprawdzanie dostępności ---
    elif intent == 'check_seats':
        if restaurant_name:
            result = db.check_availability(restaurant_name)
            if result:
                seats = result['available_tables']
                if seats > 0:
                    response_text = f"Tak! W lokalu <b>{result['name']}</b> mamy jeszcze <b>{seats} wolnych stolików</b>. 🔥 Wpadajcie!"
                else:
                    response_text = f"Niestety, <b>{result['name']}</b> jest teraz pełny. 😔 Może poszukamy czegoś innego?"
            else:
                response_text = f"Nie mogę znaleźć restauracji '{restaurant_name}' w bazie. Upewnij się, że wpisałeś poprawną nazwę."
        else:
            response_text = "Mogę sprawdzić dostępność, ale musisz podać nazwę restauracji (np. Zielnik, Neon)."

    # --- RESZTA (Powitanie / Fallback) ---
    else:
        # Pobierz gotową odpowiedź z intents.json
        response_text = bot.get_response(intent)

    # 3. Wysyłka odpowiedzi do frontendu
    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(debug=True, port=5000)