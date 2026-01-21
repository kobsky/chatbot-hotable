# =============================================================================
# APP.PY - Główna aplikacja Flask dla chatbota Hotable
# =============================================================================

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from nlp_engine import ChatbotBrain
from db_handler import DatabaseHandler
from entities import (
    RESTAURANT_DESCRIPTIONS, 
    RESTAURANT_DETAILS, 
    KW_RESTAURANTS, 
    KW_CUISINE,
    COMMON_WORDS,
    CUISINE_TO_RESTAURANT
)

# =============================================================================
# INICJALIZACJA APLIKACJI
# =============================================================================

app = Flask(__name__)
CORS(app)

print("⏳ Uruchamianie systemu Hotable...")
bot = ChatbotBrain()
db = DatabaseHandler()
print("🚀 System gotowy! Serwer działa na porcie 5000")

# Kontekst konwersacji (prosty system pamięci)
CONTEXT = {
    "last_restaurant": None,
    "last_cuisine": None,
    "conversation_count": 0
}

# Lista aktywnych lokali w systemie
ACTIVE_VENUES = ["Neon", "Zielnik", "Porto Azzurro"]


# =============================================================================
# FUNKCJE POMOCNICZE
# =============================================================================

def reset_context():
    """Resetowanie kontekstu konwersacji"""
    CONTEXT["last_restaurant"] = None
    CONTEXT["last_cuisine"] = None

def detect_unknown_entity(message, restaurant_name):
    """
    Wykrywanie potencjalnych nieznanych nazw w wiadomości.
    Zwraca True jeśli wykryto słowo, które może być nieznaną nazwą restauracji.
    """
    if restaurant_name:
        return False
    
    words = message.lower().split()
    known_keywords = set(KW_RESTAURANTS.keys()) | set(KW_CUISINE.keys()) | COMMON_WORDS
    
    for word in words:
        clean_word = word.strip('.,?!:;"\'-')
        if clean_word and len(clean_word) > 2 and clean_word not in known_keywords:
            # Sprawdzenie czy to nie jest część znanej frazy
            if not any(clean_word in kw for kw in known_keywords):
                return True
    
    return False

def format_restaurant_list(restaurants):
    """Formatowanie listy restauracji do wyświetlenia"""
    if not restaurants:
        return "Brak dostępnych restauracji."
    
    lines = ["Oto dostępne restauracje:\n"]
    
    cuisine_icons = {
        "StreetFood": "🍔",
        "Śródziemnomorska": "🍝",
        "Polska": "🥗"
    }
    
    for r in restaurants:
        name = r.get('name', 'Nieznana')
        cuisine = r.get('cuisine', '')
        icon = cuisine_icons.get(cuisine, "🍽️")
        seats = r.get('available_tables', 0)
        status = "🟢" if seats > 0 else "🔴"
        
        lines.append(f"{icon} **{name}** ({cuisine}) - {status} {seats} wolnych stolików")
    
    lines.append("\nNapisz nazwę lokalu, aby poznać szczegóły.")
    return "\n".join(lines)

def get_seats_response(restaurant_name=None):
    """Generowanie odpowiedzi o dostępnych miejscach"""
    if restaurant_name:
        target = db.check_availability(restaurant_name)
        if target:
            count = target.get('available_tables', 0)
            status = "🟢" if count > 0 else "🔴"
            CONTEXT["last_restaurant"] = restaurant_name
            return f"{status} W restauracji **{restaurant_name}** mamy obecnie **{count}** wolnych stolików."
        else:
            return f"❌ Nie znalazłem restauracji o nazwie {restaurant_name}."
    else:
        # Pokaż wszystkie restauracje
        all_rest = db.get_all_restaurants()
        if not all_rest:
            return "❌ Nie udało mi się pobrać informacji o dostępności. Spróbuj ponownie później."
        
        lines = ["📊 **Stan dostępności stolików:**\n"]
        for r in all_rest:
            if r.get('name') not in ACTIVE_VENUES:
                continue
            seats = r.get('available_tables', 0)
            icon = "🟢" if seats > 0 else "🔴"
            lines.append(f"{icon} **{r.get('name')}**: {seats} wolnych")
        
        lines.append("\n💡 Podaj nazwę lokalu, aby sprawdzić szczegóły.")
        return "\n".join(lines)


# =============================================================================
# ENDPOINTY API
# =============================================================================

@app.route('/')
def index():
    """Serwowanie strony testowej"""
    return send_from_directory('.', 'test_widget.html')


@app.route('/health')
def health_check():
    """Endpoint do sprawdzania stanu aplikacji"""
    return jsonify({
        "status": "healthy",
        "active_venues": ACTIVE_VENUES,
        "context": CONTEXT
    })


@app.route('/chat', methods=['POST'])
def chat():
    """
    Główny endpoint obsługujący konwersację.
    
    Przyjmuje JSON z polem 'message'.
    Zwraca JSON z polem 'response'.
    """
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"response": "Nie otrzymałem wiadomości. Spróbuj ponownie."})
    
    # Inkrementacja licznika konwersacji
    CONTEXT["conversation_count"] += 1
    
    # Predykcja intencji i ekstrakcja encji
    intent = bot.predict_intent(user_message)
    entities = bot.extract_entities(user_message)
    
    # Logowanie dla debugowania
    print(f"📩 [{CONTEXT['conversation_count']}] Msg: '{user_message}'")
    print(f"   ➤ Intent: {intent} | Entities: {entities}")
    
    # Pobieranie encji
    restaurant_name = entities.get("restaurant")
    cuisine = entities.get('cuisine')
    
    # Wykrywanie nieznanych nazw
    potential_unknown = detect_unknown_entity(user_message, restaurant_name)
    
    # ==========================================================================
    # OBSŁUGA INTENCJI
    # ==========================================================================
    
    # --- OUT OF SCOPE ---
    if intent == "out_of_scope":
        return jsonify({"response": bot.get_response(intent)})
    
    # --- FALLBACK ---
    if intent == "fallback":
        response = (
            "Przepraszam, nie zrozumiałem. 🤔\n\n"
            "Spróbuj zapytać np.:\n"
            "• \"Szukam włoskiej restauracji\"\n"
            "• \"Gdzie są wolne miejsca?\"\n"
            "• \"Pokaż listę lokali\"\n"
            "• \"Opowiedz o Neonie\""
        )
        return jsonify({"response": response})
    
    # --- GREET (Powitanie) ---
    if intent == "greet":
        reset_context()
        return jsonify({"response": bot.get_response(intent)})
    
    # --- BOT_PURPOSE (Kim jesteś) ---
    if intent == "bot_purpose":
        return jsonify({"response": bot.get_response(intent)})
    
    # --- THANKS (Podziękowanie) ---
    if intent == "thanks":
        return jsonify({"response": bot.get_response(intent)})
    
    # --- GOODBYE (Pożegnanie) ---
    if intent == "goodbye":
        reset_context()
        return jsonify({"response": bot.get_response(intent)})
    
    # --- BOOK_TABLE (Rezerwacja - informacja o braku funkcji) ---
    if intent == "book_table":
        response = bot.get_response(intent)
        if restaurant_name:
            details = RESTAURANT_DETAILS.get(restaurant_name)
            if details:
                response += f"\n\n📞 Telefon do {restaurant_name}: {details['phone']}"
        return jsonify({"response": response})
    
    # --- UNAVAILABLE_CUISINE (Niedostępna kuchnia) ---
    if intent == "unavailable_cuisine":
        return jsonify({"response": bot.get_response(intent)})
    
    # --- LIST_RESTAURANTS (Lista lokali) ---
    if intent == "list_restaurants":
        reset_context()
        response = (
            "🍽️ **Aktualnie dostępne restauracje:**\n\n"
            "1. 🍔 **Neon** - StreetFood, burgery, kuchnia uliczna\n"
            "2. 🍝 **Porto Azzurro** - Kuchnia śródziemnomorska, włoska\n"
            "3. 🥗 **Zielnik** - Tradycyjna kuchnia polska\n\n"
            "Napisz nazwę wybranego lokalu, aby sprawdzić szczegóły lub dostępność."
        )
        return jsonify({"response": response})
    
    # --- LIST_CUISINES (Rodzaje kuchni) ---
    if intent == "list_cuisines":
        return jsonify({"response": bot.get_response(intent)})
    
    # --- ASK_RECOMMENDATION (Rekomendacja) ---
    if intent == "ask_recommendation":
        return jsonify({"response": bot.get_response(intent)})
    
    # --- SEARCH_CUISINE (Szukanie po typie kuchni) ---
    if intent == "search_cuisine":
        reset_context()
        
        if cuisine:
            restaurants = db.get_restaurants_by_cuisine(cuisine)
            if restaurants:
                CONTEXT["last_restaurant"] = restaurants[0]['name']
                CONTEXT["last_cuisine"] = cuisine
                
                lines = [f"🍴 Restauracje z kuchnią **{cuisine}**:\n"]
                for r in restaurants:
                    seats = r.get('available_tables', 0)
                    icon = "🟢" if seats > 0 else "🔴"
                    lines.append(f"• **{r['name']}** ({icon} Wolne stoliki: {seats})")
                
                lines.append("\n💡 Chcesz poznać szczegóły któregoś lokalu?")
                response = "\n".join(lines)
            else:
                response = f"😔 Przepraszam, nie znalazłem restauracji typu **{cuisine}** w naszej bazie."
        else:
            response = (
                "🤔 Jakiej kuchni szukasz?\n\n"
                "Mamy do wyboru:\n"
                "• 🇵🇱 **Polską** (Zielnik)\n"
                "• 🍝 **Włoską/Śródziemnomorską** (Porto Azzurro)\n"
                "• 🍔 **StreetFood** (Neon)"
            )
        
        return jsonify({"response": response})
    
    # --- RESTAURANT_INFO (Informacje o restauracji) ---
    if intent == "restaurant_info":
        # Próba użycia kontekstu jeśli brak nazwy
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            restaurant_name = CONTEXT["last_restaurant"]
        
        if restaurant_name:
            CONTEXT["last_restaurant"] = restaurant_name
            description = RESTAURANT_DESCRIPTIONS.get(restaurant_name)
            
            if description:
                details = RESTAURANT_DETAILS.get(restaurant_name, {})
                response = description
                
                # Dodanie podstawowych informacji
                if details:
                    response += f"\n\n📍 **Adres:** {details.get('address', 'Brak danych')}"
                    response += f"\n🕒 **Godziny:** {details.get('hours', 'Brak danych')}"
                
                return jsonify({"response": response})
            else:
                return jsonify({"response": f"❌ Brak opisu dla restauracji {restaurant_name}."})
        else:
            response = (
                "O której restauracji chcesz posłuchać? 🤔\n\n"
                "Dostępne lokale:\n"
                "• 🍔 Neon\n"
                "• 🍝 Porto Azzurro\n"
                "• 🥗 Zielnik"
            )
            return jsonify({"response": response})
    
    # --- CHECK_SEATS (Sprawdzanie wolnych miejsc) ---
    if intent == "check_seats":
        # Obsługa nieznanej nazwy
        if potential_unknown and not restaurant_name:
            response = (
                "🧐 Wygląda na to, że pytasz o lokal, którego nie mam w bazie.\n\n"
                "Obsługuję tylko:\n"
                "• Neon\n"
                "• Zielnik\n"
                "• Porto Azzurro"
            )
            return jsonify({"response": response})
        
        # Próba użycia kontekstu
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            restaurant_name = CONTEXT["last_restaurant"]
        
        response = get_seats_response(restaurant_name)
        return jsonify({"response": response})
    
    # --- CHECK_CONTACT (Dane kontaktowe) ---
    if intent == "check_contact":
        # Próba użycia kontekstu
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            restaurant_name = CONTEXT["last_restaurant"]
        
        if restaurant_name:
            details = RESTAURANT_DETAILS.get(restaurant_name)
            if details:
                CONTEXT["last_restaurant"] = restaurant_name
                response = (
                    f"📍 **{restaurant_name} - Dane kontaktowe:**\n\n"
                    f"🏠 **Adres:** {details['address']}\n"
                    f"📞 **Telefon:** {details['phone']}\n"
                    f"🕒 **Godziny otwarcia:** {details['hours']}"
                )
                return jsonify({"response": response})
            else:
                return jsonify({"response": f"❌ Nie mam danych kontaktowych dla {restaurant_name}."})
        else:
            response = (
                "📞 Podaj nazwę restauracji, a podam Ci dane kontaktowe.\n\n"
                "Dostępne lokale: Neon, Zielnik, Porto Azzurro"
            )
            return jsonify({"response": response})
    
    # --- CHECK_HOURS (Godziny otwarcia) ---
    if intent == "check_hours":
        # Próba użycia kontekstu
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            restaurant_name = CONTEXT["last_restaurant"]
        
        if restaurant_name:
            details = RESTAURANT_DETAILS.get(restaurant_name)
            if details:
                CONTEXT["last_restaurant"] = restaurant_name
                response = f"🕒 **{restaurant_name}** jest otwarte: **{details['hours']}**"
                return jsonify({"response": response})
            else:
                return jsonify({"response": f"❌ Nie mam informacji o godzinach dla {restaurant_name}."})
        else:
            response = (
                "🕒 **Typowe godziny otwarcia naszych lokali:**\n\n"
                "• Neon: 09:00 - 23:00\n"
                "• Porto Azzurro: 09:00 - 21:00\n"
                "• Zielnik: 09:00 - 21:00\n\n"
                "O który lokal pytasz konkretnie?"
            )
            return jsonify({"response": response})
    
    # --- CHECK_CAPACITY (Pojemność lokalu) ---
    if intent == "check_capacity":
        # Próba użycia kontekstu
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            restaurant_name = CONTEXT["last_restaurant"]
        
        if restaurant_name:
            details = RESTAURANT_DETAILS.get(restaurant_name)
            if details:
                CONTEXT["last_restaurant"] = restaurant_name
                response = (
                    f"🏠 **{restaurant_name}** posiada łącznie "
                    f"**{details['max_tables']}** stolików.\n\n"
                    f"Cechy lokalu: {', '.join(details.get('features', []))}"
                )
                return jsonify({"response": response})
            else:
                return jsonify({"response": f"❌ Nie mam danych o pojemności dla {restaurant_name}."})
        else:
            response = (
                "🏠 **Pojemność naszych lokali:**\n\n"
                "• Neon: 10 stolików\n"
                "• Porto Azzurro: 15 stolików\n"
                "• Zielnik: 6 stolików\n\n"
                "O który lokal pytasz?"
            )
            return jsonify({"response": response})
    
    # --- DOMYŚLNA OBSŁUGA NIEZNANEJ ENCJI ---
    if potential_unknown and not restaurant_name:
        response = (
            "🧐 Przepraszam, nie rozpoznaję tej nazwy.\n\n"
            "Obsługuję następujące lokale:\n"
            "• 🍔 Neon\n"
            "• 🍝 Porto Azzurro\n"
            "• 🥗 Zielnik\n\n"
            "Czy chodziło Ci o jeden z nich?"
        )
        return jsonify({"response": response})
    
    # --- FALLBACK DLA NIEOBSŁUŻONYCH PRZYPADKÓW ---
    response = bot.get_response(intent)
    if not response or response.strip() == "":
        response = (
            "Przepraszam, nie jestem pewien jak odpowiedzieć. 🤔\n\n"
            "Mogę pomóc w:\n"
            "• Wyszukiwaniu restauracji\n"
            "• Sprawdzaniu dostępności stolików\n"
            "• Podaniu informacji o lokalach"
        )
    
    return jsonify({"response": response})


# =============================================================================
# URUCHOMIENIE APLIKACJI
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')