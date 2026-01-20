from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from nlp_engine import ChatbotBrain
from db_handler import DatabaseHandler
from entities import RESTAURANT_DESCRIPTIONS, RESTAURANT_DETAILS

app = Flask(__name__)
CORS(app)

print("⏳ Uruchamianie systemu...")
bot = ChatbotBrain()
db = DatabaseHandler()
print("🚀 System gotowy! Serwer działa.")

CONTEXT = {"last_restaurant": None}

@app.route('/')
def index():
    return send_from_directory('.', 'test_widget.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    intent = bot.predict_intent(user_message)
    entities = bot.extract_entities(user_message)
    
    print(f"📩 Msg: '{user_message}' | Intent: {intent} | Entities: {entities}")

    response_text = ""
    restaurant_name = entities.get("restaurant")

    if intent == "greet":
        CONTEXT["last_restaurant"] = None
        response_text = bot.get_response(intent)
        return jsonify({"response": response_text})

    if intent == 'search_cuisine':
        CONTEXT["last_restaurant"] = None
        cuisine = entities.get('cuisine')
        if cuisine:
            restaurants = db.get_restaurants_by_cuisine(cuisine)
            if restaurants:
                CONTEXT["last_restaurant"] = restaurants[0]['name']
                response_text = f"Mam kilka propozycji w kategorii {cuisine}:<br>"
                for r in restaurants:
                    seats = r['available_tables']
                    icon = "🟢" if seats > 0 else "🔴"
                    response_text += f"- <b>{r['name']}</b> ({icon} Wolne stoliki: {seats})<br>"
            else:
                response_text = f"Przykro mi, ale nie znalazłem restauracji typu {cuisine} w naszej bazie. 😔"
        else:
            response_text = "Jasne, chętnie coś polecę. Ale na jaką kuchnię masz ochotę? (np. Polska, Włoska, StreetFood)"
        return jsonify({"response": response_text})

    if intent == "restaurant_info":
        response_prefix = ""
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            if intent != "book_table": # Warunek bezpieczeństwa
                restaurant_name = CONTEXT["last_restaurant"]
                response_prefix = f"(Nawiązując do {restaurant_name}): "

        if restaurant_name:
            CONTEXT["last_restaurant"] = restaurant_name
            description = RESTAURANT_DESCRIPTIONS.get(restaurant_name)
            if description:
                return jsonify({"response": response_prefix + description})
            else:
                return jsonify({"response": f"Brak opisu dla {restaurant_name}."})
        else:
             return jsonify({"response": "O której restauracji chcesz posłuchać? Mamy Neon, Zielnik i Porto Azzurro."})

    if intent == "list_restaurants":
        response_text = (
            "Aktualnie współpracujemy z 3 wyjątkowymi lokalami:\n"
            "1. 🍔 **Neon** (StreetFood & Bary)\n"
            "2. 🍝 **Porto Azzurro** (Śródziemnomorska)\n"
            "3. 🥗 **Zielnik** (Polska & Nowoczesna)\n\n"
            "O którym z nich chcesz dowiedzieć się więcej?"
        )
        return jsonify({"response": response_text})

    if not restaurant_name:
        restaurant_name = CONTEXT.get("last_restaurant")

    if intent == "check_seats":
        if restaurant_name:
            target = db.check_availability(restaurant_name)
            if target:
                count = target.get('available_tables', 0)
                CONTEXT["last_restaurant"] = restaurant_name
                return jsonify({"response": f"W restauracji {restaurant_name} są obecnie {count} wolne miejsca."})
            else:
                return jsonify({"response": f"Nie znalazłem danych dla restauracji {restaurant_name}."})
        else:
             return jsonify({"response": "W której restauracji sprawdzić liczbę wolnych miejsc? (Neon, Zielnik, Porto Azzurro)"})

    if intent == "check_contact":
        if restaurant_name:
            details = RESTAURANT_DETAILS.get(restaurant_name)
            if details:
                CONTEXT["last_restaurant"] = restaurant_name
                return jsonify({"response": f"📍 Adres: {details['address']}\n📞 Telefon: {details['phone']}"})
        return jsonify({"response": "Podaj nazwę restauracji, a podam Ci jej adres i numer telefonu."})

    if intent == "check_hours":
        if restaurant_name:
             details = RESTAURANT_DETAILS.get(restaurant_name)
             if details:
                CONTEXT["last_restaurant"] = restaurant_name
                return jsonify({"response": f"🕒 {restaurant_name} jest otwarte: {details['hours']}"})
        return jsonify({"response": "Większość lokali działa od 9:00 do 21:00. O który konkretnie pytasz?"})

    if intent == "check_capacity":
        if restaurant_name:
             details = RESTAURANT_DETAILS.get(restaurant_name)
             if details:
                CONTEXT["last_restaurant"] = restaurant_name
                return jsonify({"response": f"🏠 {restaurant_name} posiada łącznie {details['max_tables']} stolików."})
        return jsonify({"response": "Każdy lokal ma inną wielkość. O który pytasz?"})
    
    response_text = bot.get_response(intent)
    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(debug=True, port=5000)