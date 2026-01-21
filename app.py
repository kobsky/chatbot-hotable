from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from nlp_engine import ChatbotBrain
from db_handler import DatabaseHandler
from entities import RESTAURANT_DESCRIPTIONS, RESTAURANT_DETAILS, KW_RESTAURANTS, KW_CUISINE

app = Flask(__name__)
CORS(app)

print("⏳ Uruchamianie systemu...")
bot = ChatbotBrain()
db = DatabaseHandler()
print("🚀 System gotowy! Serwer działa.")

CONTEXT = {"last_restaurant": None}
ACTIVE_VENUES = ["Neon", "Zielnik", "Porto Azzurro"]

# Prosta lista słów funkcyjnych do ignorowania przy heurystyce
COMMON_WORDS = {
    "w", "jest", "i", "czy", "ma", "ile", "są", "wolnych", "miejsc", "w", "o", "a", "ale", "lub", "nie", "się",
    "cześć", "hej", "dzień", "dobry", "poproszę", "pokaż", "powiedz", "jaka", "jaki", "jakie", "gdzie", "kiedy", "która"
}

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

    # --- GUARD CLAUSE: Pytania poza zakresem tematycznym ---
    if intent == "out_of_scope":
        return jsonify({"response": bot.get_response(intent)})

    if intent == "fallback":
        return jsonify({"response": "Przepraszam, nie zrozumiałem. 🤔\nCzy możesz zapytać inaczej? Spróbuj np.:\n- 'Szukam włoskiej'\n- 'Gdzie są wolne miejsca?'\n- 'Pokaż listę lokali'"})

    response_text = ""
    restaurant_name = entities.get("restaurant")
    cuisine = entities.get('cuisine')

    # --- ROZBUDOWANA LOGIKA WYKRYWANIA NIEZNANYCH NAZW (ENTITY GUARD v2) ---
    potential_new_entity = False
    if not restaurant_name:
        words = user_message.lower().split()
        known_keywords = set(KW_RESTAURANTS.keys()) | set(KW_CUISINE.keys()) | COMMON_WORDS
        
        for word in words:
            clean_word = word.strip('.,?!:')
            if clean_word and clean_word not in known_keywords:
                potential_new_entity = True
                break

    # FIX: Nie przywracaj kontekstu, jeśli wykryto potencjalną nową nazwę!
    if not restaurant_name and not potential_new_entity and CONTEXT.get("last_restaurant") and intent not in ["search_cuisine", "list_restaurants", "greet", "list_cuisines", "ask_recommendation", "check_seats", "bot_purpose"]:
        restaurant_name = CONTEXT["last_restaurant"]

    if intent == "greet":
        CONTEXT["last_restaurant"] = None
        response_text = bot.get_response(intent)
        return jsonify({"response": response_text})

    if intent == "bot_purpose":
        response_text = bot.get_response(intent)
        return jsonify({"response": response_text})

    if intent == "book_table":
        return jsonify({"response": "Przykro mi, to zadanie wykracza poza mój zakres."})

    if intent == 'search_cuisine':
        CONTEXT["last_restaurant"] = None
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
             # Jeśli brak encji 'cuisine', pytamy o preferencje
            response_text = "Zależy, na co masz ochotę! 😋 Celujesz w kuchnię Polską 🥟, Włoską 🍝 czy może soczysty StreetFood 🍔?"
        return jsonify({"response": response_text})

    if intent == "restaurant_info":
        response_prefix = ""
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            if intent != "book_table":
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
        CONTEXT["last_restaurant"] = None
        
        response_text = (
            "Aktualnie dostępne restauracje to:\n"
            "1. 🍔 **Neon** (StreetFood)\n"
            "2. 🍝 **Porto Azzurro** (Śródziemnomorska)\n"
            "3. 🥗 **Zielnik** (Polska)\n\n"
            "Napisz nazwę wybranego lokalu, aby sprawdzić szczegóły."
        )
        return jsonify({"response": response_text})
    
    if intent == "ask_recommendation":
        # Logika dla: "Co polecasz?"
        return jsonify({"response": "Zależy, na co masz ochotę! 😋 Celujesz w kuchnię Polską 🥟, Włoską 🍝 czy może soczysty StreetFood 🍔?"})

    if intent == "list_cuisines":
        # Logika dla: "Jakie rodzaje kuchni?"
        return jsonify({"response": "Mamy szeroki wybór smaków! Oferujemy kuchnię:\n🇵🇱 **Polską** (Zielnik)\n🇮🇹 **Włoską/Śródziemnomorską** (Porto Azzurro)\n🍔 **StreetFood** (Neon)\n\nNa co się skusisz?"})

    if intent == "check_seats":
        if potential_new_entity and not restaurant_name:
            return jsonify({"response": "Wygląda na to, że pytasz o lokal, którego nie mam w bazie. 🧐\nObsługuję tylko: Neon, Zielnik i Porto Azzurro."})

        if restaurant_name:
            target = db.check_availability(restaurant_name)
            if target:
                count = target.get('available_tables', 0)
                CONTEXT["last_restaurant"] = restaurant_name
                return jsonify({"response": f"W restauracji <b>{restaurant_name}</b> mamy obecnie <b>{count}</b> wolnych stolików."})
            else:
                return jsonify({"response": f"Nie znalazłem restauracji o nazwie {restaurant_name}."})
        
        else:
            all_rest = db.get_all_restaurants()
            all_rest = [r for r in all_rest if r.get('name') != 'Trawnik']
            
            if not all_rest:
                return jsonify({"response": "Nie udało mi się pobrać informacji o dostępności. Spróbuj ponownie później."})

            response_lines = ["Oto stan dostępności w naszych lokalach:<br>"]
            for r in all_rest:
                if r['name'] not in ACTIVE_VENUES:
                    continue
                seats = r.get('available_tables', 0)
                icon = "🟢" if seats > 0 else "🔴"
                response_lines.append(f"{icon} <b>{r.get('name')}</b>: {seats} wolnych")
            return jsonify({"response": "<br>".join(response_lines)})

    # Fallback dla wszystkich innych intencji, jeśli jest potencjalna nowa encja
    if potential_new_entity and not restaurant_name:
        return jsonify({"response": "Wygląda na to, że pytasz o lokal, którego nie mam w bazie. 🧐\nObsługuję tylko: Neon, Zielnik i Porto Azzurro."})


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
