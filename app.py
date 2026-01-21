# =============================================================================
# APP.PY - Główna aplikacja Flask dla chatbota Hotable
# Dane pobierane z Supabase
# =============================================================================

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from nlp_engine import ChatbotBrain
from db_handler import DatabaseHandler
from entities import KW_RESTAURANTS, KW_CUISINE, COMMON_WORDS

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


# =============================================================================
# FUNKCJE POMOCNICZE
# =============================================================================

def get_active_venues():
    """Pobieranie listy aktywnych lokali z bazy"""
    restaurants = db.get_all_restaurants()
    return [r.get('name') for r in restaurants if r.get('name')]


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
        clean_word = word.strip('.,?!:;\"\'-')
        if clean_word and len(clean_word) > 2 and clean_word not in known_keywords:
            # Sprawdzenie czy to nie jest część znanej frazy
            if not any(clean_word in kw for kw in known_keywords):
                return True
    
    return False


def format_restaurant_description(restaurant_data):
    """Formatowanie opisu restauracji z danych bazy"""
    if not restaurant_data:
        return None
    
    name = restaurant_data.get('name', 'Nieznana')
    cuisine = restaurant_data.get('cuisine', '')
    description = restaurant_data.get('description', '')
    
    # Ikony dla typów kuchni
    cuisine_icons = {
        "StreetFood": "🍔",
        "Śródziemnomorska": "🍝",
        "Polska": "🥗"
    }
    icon = cuisine_icons.get(cuisine, "🍽️")
    
    if description:
        return f"{icon} **{name}** ({cuisine})\n\n{description}"
    else:
        return f"{icon} **{name}** - Restauracja z kuchnią {cuisine}."


def format_restaurant_details(restaurant_data):
    """Formatowanie szczegółów kontaktowych restauracji"""
    if not restaurant_data:
        return None
    
    name = restaurant_data.get('name', 'Nieznana')
    phone = restaurant_data.get('phone', 'Brak danych')
    address = restaurant_data.get('address', 'Brak danych')
    hours = restaurant_data.get('hours', 'Brak danych')
    
    return {
        'name': name,
        'phone': phone,
        'address': address,
        'hours': hours,
        'max_tables': restaurant_data.get('max_tables', 'N/A'),
        'features': restaurant_data.get('features', [])
    }


def get_seats_response(restaurant_name=None):
    """Generowanie odpowiedzi o dostępnych miejscach"""
    if restaurant_name:
        target = db.check_availability(restaurant_name)
        if target:
            count = target.get('available_tables', 0)
            status = "🟢" if count > 0 else "🔴"
            CONTEXT["last_restaurant"] = target.get('name', restaurant_name)
            return f"{status} W restauracji **{target.get('name')}** mamy obecnie **{count}** wolnych stolików."
        else:
            return f"❌ Nie znalazłem restauracji o nazwie {restaurant_name}."
    else:
        # Pokaż wszystkie restauracje
        all_rest = db.get_all_restaurants()
        if not all_rest:
            return "❌ Nie udało mi się pobrać informacji o dostępności. Spróbuj ponownie później."
        
        lines = ["📊 **Stan dostępności stolików:**\n"]
        for r in all_rest:
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
        "active_venues": get_active_venues(),
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

    # --- SONDA DIAGNOSTYCZNA v2: INSPEKTOR KOLUMN ---
    if user_message.strip().upper() == "DIAGNOZA":
        print("\n" + "="*50)
        print("🕵️ INSPEKTOR KOLUMN BAZY DANYCH")
        print("="*50)
        
        try:
            # Pobieramy 1 rekord, żeby zobaczyć strukturę
            all_rows = db.get_all_restaurants()
            
            if all_rows and len(all_rows) > 0:
                first_record = all_rows[0]
                print("✅ Udało się pobrać przykładowy rekord.")
                print("\n🔑 DOSTĘPNE KOLUMNY (KLUCZE) W BAZIE:")
                print(list(first_record.keys()))
                
                print("\n📄 PRZYKŁADOWE DANE:")
                print(first_record)
            else:
                print("⚠️ Baza zwróciła pustą listę. Czy tabela 'restaurants' ma dane?")

        except Exception as e:
            print(f"❌ BŁĄD KRYTYCZNY: {e}")
        
        print("="*50 + "\n")
        return jsonify({"response": "Sprawdź terminal - wypisałem dostępne kolumny."})
    
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
            details = db.get_restaurant_details(restaurant_name)
            if details and details.get('phone'):
                response += f"\n\n📞 Telefon do {details.get('name')}: {details.get('phone')}"
        return jsonify({"response": response})
    
    # --- UNAVAILABLE_CUISINE (Niedostępna kuchnia) ---
    if intent == "unavailable_cuisine":
        return jsonify({"response": bot.get_response(intent)})
    
    # --- LIST_RESTAURANTS (Lista lokali) ---
    if intent == "list_restaurants":
        reset_context()
        
        # Pobieranie listy restauracji z bazy
        restaurants = db.get_all_restaurants()
        
        # --- FILTR: Lista dozwolonych restauracji ---
        ACTIVE_VENUES = ["Neon", "Zielnik", "Porto Azzurro"]
        
        if restaurants:
            cuisine_icons = {
                "StreetFood": "🍔",
                "Śródziemnomorska": "🍝",
                "Polska": "🥗"
            }
            
            lines = ["🍽️ **Aktualnie dostępne restauracje:**\n"]
            
            # Używamy licznika ręcznie, żeby numeracja była ciągła po filtracji
            counter = 1
            
            for r in restaurants:
                name = r.get('name', 'Nieznana')
                
                # --- FILTRACJA: Pomiń jeśli nie ma na liście ---
                if name not in ACTIVE_VENUES:
                    continue
                
                cuisine = r.get('cuisine', '')
                icon = cuisine_icons.get(cuisine, "🍽️")
                
                # Dodajemy do listy tylko zweryfikowane lokale
                lines.append(f"{counter}. {icon} **{name}** - {cuisine}")
                counter += 1
            
            lines.append("\nNapisz nazwę wybranego lokalu, aby sprawdzić szczegóły lub dostępność.")
            response = "\n".join(lines)
        else:
            response = "Nie udało się pobrać listy restauracji. Spróbuj ponownie później."
        
        return jsonify({"response": response})
    
    # --- LIST_CUISINES (Rodzaje kuchni) ---
    if intent == "list_cuisines":
        # Pobieranie unikalnych kuchni z bazy
        restaurants = db.get_all_restaurants()
        cuisines = set()
        cuisine_restaurants = {}
        
        for r in restaurants:
            cuisine = r.get('cuisine')
            name = r.get('name')
            if cuisine:
                cuisines.add(cuisine)
                if cuisine not in cuisine_restaurants:
                    cuisine_restaurants[cuisine] = []
                cuisine_restaurants[cuisine].append(name)
        
        if cuisines:
            cuisine_icons = {
                "StreetFood": "🍔",
                "Śródziemnomorska": "🍝",
                "Polska": "🥗"
            }
            
            lines = ["Mamy szeroki wybór smaków! 🌍\n\nOferujemy kuchnię:"]
            for cuisine in sorted(cuisines):
                icon = cuisine_icons.get(cuisine, "🍽️")
                restaurants_list = ", ".join(cuisine_restaurants.get(cuisine, []))
                lines.append(f"{icon} **{cuisine}** → {restaurants_list}")
            
            lines.append("\nKtóra Cię interesuje?")
            response = "\n".join(lines)
        else:
            response = bot.get_response(intent)
        
        return jsonify({"response": response})
    
    # --- ASK_RECOMMENDATION (Rekomendacja) ---
    if intent == "ask_recommendation":
        # Pobieranie restauracji z bazy do rekomendacji
        restaurants = db.get_all_restaurants()
        
        if restaurants:
            cuisine_icons = {
                "StreetFood": "🍔",
                "Śródziemnomorska": "🍝",
                "Polska": "🥗"
            }
            
            lines = ["Zależy, na co masz ochotę! 😋\n"]
            for r in restaurants:
                name = r.get('name', '')
                cuisine = r.get('cuisine', '')
                icon = cuisine_icons.get(cuisine, "🍽️")
                lines.append(f"• {icon} **{cuisine}** → {name}")
            
            lines.append("\nNa co się skusisz?")
            response = "\n".join(lines)
        else:
            response = bot.get_response(intent)
        
        return jsonify({"response": response})
    
    # --- SEARCH_CUISINE (Szukanie po typie kuchni) ---
    if intent == "search_cuisine":
        if cuisine:
            results = db.get_restaurants_by_cuisine(cuisine)
            
            if results:
                lines = [f"🔎 Oto lokale z kategorią **{cuisine}**:",]
                for r in results:
                    icon = "🟢" if r.get('available_tables', 0) > 0 else "🔴"
                    lines.append(f"{icon} **{r['name']}**")
                
                if results:
                    CONTEXT["last_restaurant"] = results[0]['name']
                    
                return jsonify({"response": "\n".join(lines)})
            else:
                return jsonify({"response": f"😔 Przepraszam, nie znalazłem aktywnych restauracji typu **{cuisine}** w naszej bazie."})
        else:
            # Fallback to listing cuisines
            return jsonify({"response": "Mamy szeroki wybór smaków! 😋\nOferujemy kuchnię:\n🇵🇱 **Polska** (Zielnik)\n🍝 **Śródziemnomorska** (Porto Azzurro)\n🍔 **StreetFood** (Neon)"})

    
    # --- RESTAURANT_INFO (Informacje o restauracji) ---
    if intent == "restaurant_info":
        # Próba użycia kontekstu jeśli brak nazwy
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            restaurant_name = CONTEXT["last_restaurant"]
        
        if restaurant_name:
            # Pobieranie danych z bazy
            restaurant_data = db.get_restaurant_details(restaurant_name)
            
            if restaurant_data:
                CONTEXT["last_restaurant"] = restaurant_data.get('name')
                
                # Formatowanie odpowiedzi
                description = format_restaurant_description(restaurant_data)
                details = format_restaurant_details(restaurant_data)
                
                response = description
                if details:
                    response += f"\n\n📍 **Adres:** {details['address']}"
                    response += f"\n🕒 **Godziny:** {details['hours']}"
                
                return jsonify({"response": response})
            else:
                return jsonify({"response": f"❌ Nie znalazłem restauracji o nazwie {restaurant_name}."})
        else:
            # Pobierz listę restauracji z bazy
            restaurants = db.get_all_restaurants()
            names = [r.get('name') for r in restaurants if r.get('name')]
            
            response = (
                "O której restauracji chcesz posłuchać? 🤔\n\n"
                "Dostępne lokale:\n" +
                "\n".join([f"• {name}" for name in names])
            )
            return jsonify({"response": response})
    
    # --- CHECK_SEATS (Sprawdzanie wolnych miejsc) ---
    if intent == "check_seats":
        # Obsługa nieznanej nazwy
        if potential_unknown and not restaurant_name:
            restaurants = db.get_all_restaurants()
            names = [r.get('name') for r in restaurants if r.get('name')]
            
            response = (
                "🧐 Wygląda na to, że pytasz o lokal, którego nie mam w bazie.\n\n"
                "Obsługuję tylko:\n" +
                "\n".join([f"• {name}" for name in names])
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
            details_data = db.get_restaurant_details(restaurant_name)
            if details_data:
                details = format_restaurant_details(details_data)
                CONTEXT["last_restaurant"] = details['name']
                response = (
                    f"📍 **{details['name']} - Dane kontaktowe:**\n\n"
                    f"🏠 **Adres:** {details['address']}\n"
                    f"📞 **Telefon:** {details['phone']}\n"
                    f"🕒 **Godziny otwarcia:** {details['hours']}"
                )
                return jsonify({"response": response})
            else:
                return jsonify({"response": f"❌ Nie mam danych kontaktowych dla {restaurant_name}."})
        else:
            restaurants = db.get_all_restaurants()
            
            # --- FILTR: Lista dozwolonych restauracji ---
            ACTIVE_VENUES = ["Neon", "Zielnik", "Porto Azzurro"]
            
            # Tworzymy listę nazw TYLKO dla aktywnych lokali
            names = [r.get('name') for r in restaurants if r.get('name') in ACTIVE_VENUES]
            
            response = (
                "📞 Podaj nazwę restauracji, a podam Ci dane kontaktowe.\n\n"
                "Dostępne lokale: " + ", ".join(names)
            )
            return jsonify({"response": response})
    
    # --- CHECK_HOURS (Godziny otwarcia) ---
    if intent == "check_hours":
        # Próba użycia kontekstu
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            restaurant_name = CONTEXT["last_restaurant"]
        
        if restaurant_name:
            details_data = db.get_restaurant_details(restaurant_name)
            if details_data:
                CONTEXT["last_restaurant"] = details_data.get('name')
                response = f"🕒 **{details_data.get('name')}** jest otwarte: **{details_data.get('hours', 'Brak danych')}**"
                return jsonify({"response": response})
            else:
                return jsonify({"response": f"❌ Nie mam informacji o godzinach dla {restaurant_name}."})
        else:
            # Pobierz godziny wszystkich restauracji
            restaurants = db.get_all_restaurants()
            
            lines = ["🕒 **Godziny otwarcia naszych lokali:**\n"]
            for r in restaurants:
                name = r.get('name', 'Nieznana')
                hours = r.get('hours', 'Brak danych')
                lines.append(f"• {name}: {hours}")
            
            lines.append("\nO który lokal pytasz konkretnie?")
            response = "\n".join(lines)
            return jsonify({"response": response})
    
    # --- CHECK_CAPACITY (Pojemność lokalu) ---
    if intent == "check_capacity":
        # Próba użycia kontekstu
        if not restaurant_name and CONTEXT.get("last_restaurant"):
            restaurant_name = CONTEXT["last_restaurant"]
        
        if restaurant_name:
            details_data = db.get_restaurant_details(restaurant_name)
            if details_data:
                CONTEXT["last_restaurant"] = details_data.get('name')
                max_tables = details_data.get('max_tables', 'N/A')
                features = details_data.get('features', [])
                
                response = f"🏠 **{details_data.get('name')}** posiada łącznie **{max_tables}** stolików."
                
                if features and isinstance(features, list):
                    response += f"\n\nCechy lokalu: {', '.join(features)}"
                
                return jsonify({"response": response})
            else:
                return jsonify({"response": f"❌ Nie mam danych o pojemności dla {restaurant_name}."})
        else:
            # Pobierz pojemność wszystkich restauracji
            restaurants = db.get_all_restaurants()
            
            lines = ["🏠 **Pojemność naszych lokali:**\n"]
            for r in restaurants:
                name = r.get('name', 'Nieznana')
                max_tables = r.get('max_tables', 'N/A')
                lines.append(f"• {name}: {max_tables} stolików")
            
            lines.append("\nO który lokal pytasz?")
            response = "\n".join(lines)
            return jsonify({"response": response})
    
    # --- DOMYŚLNA OBSŁUGA NIEZNANEJ ENCJI ---
    if potential_unknown and not restaurant_name:
        restaurants = db.get_all_restaurants()
        names = [r.get('name') for r in restaurants if r.get('name')]
        
        response = (
            "🧐 Przepraszam, nie rozpoznaję tej nazwy.\n\n"
            "Obsługuję następujące lokale:\n" +
            "\n".join([f"• {name}" for name in names]) +
            "\n\nCzy chodziło Ci o jeden z nich?"
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
