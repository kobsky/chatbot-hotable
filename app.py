from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS # Pozwala na komunikację z przeglądarką
from nlp_engine import ChatbotBrain
from db_handler import DatabaseHandler
from entities import RESTAURANT_DESCRIPTIONS

app = Flask(__name__)
CORS(app) # Odblokowuje dostęp dla widgetu HTML

# Inicjalizacja komponentów (Mózg + Baza)
print("⏳ Uruchamianie systemu...")
bot = ChatbotBrain()
db = DatabaseHandler()
print("🚀 System gotowy! Serwer działa.")

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

    # 2. Logika Biznesowa (Router intencji)
    if intent == "restaurant_info":
        restaurant_name = entities.get("restaurant")
        if restaurant_name:
            # Pobierz opis, jeśli brak klucza to daj default
            description = RESTAURANT_DESCRIPTIONS.get(restaurant_name, f"Brak opisu dla {restaurant_name}.")
            return jsonify({"response": description})
        else:
            return jsonify({"response": "O której restauracji chcesz posłuchać? Mamy Neon, Zielnik i Porto Azzurro."})
    
    # --- SCENARIUSZ 1: Szukanie po kuchni ---
    if intent == 'search_cuisine':
        cuisine = entities.get('cuisine')
        if cuisine:
            # Pytamy bazę danych (L11 Integration)
            restaurants = db.get_restaurants_by_cuisine(cuisine)
            if restaurants:
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
        restaurant_name = entities.get('restaurant')
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

    # --- SCENARIUSZ 3: Godziny otwarcia ---
    elif intent == 'check_hours':
        # W MVP upraszczamy - odsyłamy ogólną informację, bo obsługa godzin w bazie jest skomplikowana
        restaurant_name = entities.get('restaurant')
        if restaurant_name:
             response_text = f"Restauracja <b>{restaurant_name}</b> jest zazwyczaj otwarta do późna. Dokładne godziny znajdziesz na ich profilu w aplikacji!"
        else:
             response_text = "O którą restaurację pytasz?"

    # --- RESZTA (Powitanie / Fallback) ---
    else:
        # Pobierz gotową odpowiedź z intents.json
        response_text = bot.get_response(intent)

    # 3. Wysyłka odpowiedzi do frontendu
    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(debug=True, port=5000)