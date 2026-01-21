# =============================================================================
# ENTITIES.PY - Słowniki mapowań dla NLP (bez danych statycznych)
# Dane restauracji są pobierane z Supabase
# =============================================================================

# -----------------------------------------------------------------------------
# SŁOWNIK KUCHNI (KW_CUISINE)
# Mapuje różne warianty nazw kuchni na ustandaryzowane nazwy
# -----------------------------------------------------------------------------

KW_CUISINE = {
    # === POLSKA ===
    "polska": "Polska",
    "polskie": "Polska",
    "polską": "Polska",
    "polskiej": "Polska",
    "polski": "Polska",
    "polskiego": "Polska",
    "tradycyjna": "Polska",
    "tradycyjne": "Polska",
    "tradycyjną": "Polska",
    "domowe": "Polska",
    "domowa": "Polska",
    "domową": "Polska",
    "schabowy": "Polska",
    "schabowego": "Polska",
    "pierogi": "Polska",
    "pierogów": "Polska",
    "bigos": "Polska",
    "bigosu": "Polska",
    "żurek": "Polska",
    "żurku": "Polska",
    "rosół": "Polska",
    "rosołu": "Polska",
    "kotlet": "Polska",
    "kotleta": "Polska",
    "kuchnia polska": "Polska",
    "kuchni polskiej": "Polska",
    "po polsku": "Polska",
    "a polska": "Polska",
    "regionalna": "Polska",
    "regionalne": "Polska",
    "swojska": "Polska",
    "swojskie": "Polska",
    "babcina": "Polska",
    "babcine": "Polska",
    "narodowa": "Polska",
    
    # === STREETFOOD (Neon) ===
    "streetfood": "StreetFood",
    "street food": "StreetFood",
    "streetfoodu": "StreetFood",
    "street-food": "StreetFood",
    "uliczna": "StreetFood",
    "uliczne": "StreetFood",
    "uliczną": "StreetFood",
    "burger": "StreetFood",
    "burgery": "StreetFood",
    "burgera": "StreetFood",
    "burgerów": "StreetFood",
    "hamburger": "StreetFood",
    "hamburgera": "StreetFood",
    "fast food": "StreetFood",
    "fastfood": "StreetFood",
    "fast-food": "StreetFood",
    "frytki": "StreetFood",
    "frytek": "StreetFood",
    "amerykańska": "StreetFood",
    "amerykańską": "StreetFood",
    "amerykańskie": "StreetFood",
    "hotdog": "StreetFood",
    "hot dog": "StreetFood",
    "hot-dog": "StreetFood",
    "wrap": "StreetFood",
    "wrapy": "StreetFood",
    "a streetfood": "StreetFood",
    "coś szybkiego": "StreetFood",
    "szybkie": "StreetFood",
    "na szybko": "StreetFood",
    "food truck": "StreetFood",
    "foodtruck": "StreetFood",
    "rzemieślnicze": "StreetFood",
    "rzemieślniczy": "StreetFood",
    
    # === ŚRÓDZIEMNOMORSKA (Porto Azzurro) ===
    "śródziemnomorska": "Śródziemnomorska",
    "srodziemnomorska": "Śródziemnomorska",
    "śródziemnomorską": "Śródziemnomorska",
    "śródziemnomorskie": "Śródziemnomorska",
    "śródziemnomorskiej": "Śródziemnomorska",
    "morska": "Śródziemnomorska",
    "morskie": "Śródziemnomorska",
    "grecka": "Śródziemnomorska",
    "grecką": "Śródziemnomorska",
    "greckie": "Śródziemnomorska",
    "ryby": "Śródziemnomorska",
    "ryba": "Śródziemnomorska",
    "rybę": "Śródziemnomorska",
    "rybna": "Śródziemnomorska",
    "rybną": "Śródziemnomorska",
    "owoce morza": "Śródziemnomorska",
    "owoców morza": "Śródziemnomorska",
    "seafood": "Śródziemnomorska",
    "włoska": "Śródziemnomorska",
    "wloska": "Śródziemnomorska",
    "włoską": "Śródziemnomorska",
    "włoskiej": "Śródziemnomorska",
    "wloskiej": "Śródziemnomorska",
    "włoskie": "Śródziemnomorska",
    "pizza": "Śródziemnomorska",
    "pizzę": "Śródziemnomorska",
    "pizzy": "Śródziemnomorska",
    "pizzeria": "Śródziemnomorska",
    "pizzerii": "Śródziemnomorska",
    "spaghetti": "Śródziemnomorska",
    "makaron": "Śródziemnomorska",
    "makaronu": "Śródziemnomorska",
    "makarony": "Śródziemnomorska",
    "pasta": "Śródziemnomorska",
    "pasty": "Śródziemnomorska",
    "italii": "Śródziemnomorska",
    "italia": "Śródziemnomorska",
    "italy": "Śródziemnomorska",
    "italiana": "Śródziemnomorska",
    "a włoska": "Śródziemnomorska",
    "lasagne": "Śródziemnomorska",
    "lasagna": "Śródziemnomorska",
    "risotto": "Śródziemnomorska",
    "penne": "Śródziemnomorska",
    "carbonara": "Śródziemnomorska",
    "bolognese": "Śródziemnomorska",
    "margherita": "Śródziemnomorska",
    "caprese": "Śródziemnomorska",
    "antipasti": "Śródziemnomorska",
    "bruschetta": "Śródziemnomorska",
    "tiramisu": "Śródziemnomorska",
    "piec": "Śródziemnomorska",
    "grill": "Śródziemnomorska",
    "z grilla": "Śródziemnomorska"
}


# -----------------------------------------------------------------------------
# SŁOWNIK RESTAURACJI (KW_RESTAURANTS)
# Mapuje różne warianty nazw restauracji na ustandaryzowane nazwy
# -----------------------------------------------------------------------------

KW_RESTAURANTS = {
    # === NEON ===
    "neon": "Neon",
    "neonie": "Neon",
    "neonu": "Neon",
    "neonem": "Neon",
    "neona": "Neon",
    "restauracja neon": "Neon",
    "restauracji neon": "Neon",
    "lokal neon": "Neon",
    "lokalu neon": "Neon",
    "urban kitchen": "Neon",
    "a w neon": "Neon",
    "w neonie": "Neon",
    "do neonu": "Neon",
    "z neonu": "Neon",
    "o neonie": "Neon",
    "knajpa neon": "Neon",
    "knajpy neon": "Neon",
    "bar neon": "Neon",
    "baru neon": "Neon",
    
    # === ZIELNIK ===
    "zielnik": "Zielnik",
    "zielniku": "Zielnik",
    "zielnika": "Zielnik",
    "zielnikiem": "Zielnik",
    "restauracja zielnik": "Zielnik",
    "restauracji zielnik": "Zielnik",
    "lokal zielnik": "Zielnik",
    "lokalu zielnik": "Zielnik",
    "a w zielnik": "Zielnik",
    "w zielniku": "Zielnik",
    "do zielnika": "Zielnik",
    "z zielnika": "Zielnik",
    "o zielniku": "Zielnik",
    "knajpa zielnik": "Zielnik",
    "knajpy zielnik": "Zielnik",
    
    # === PORTO AZZURRO ===
    "porto": "Porto Azzurro",
    "azzurro": "Porto Azzurro",
    "porto azzurro": "Porto Azzurro",
    "portoazzurro": "Porto Azzurro",
    "porto-azzurro": "Porto Azzurro",
    "u włocha": "Porto Azzurro",
    "u wlocha": "Porto Azzurro",
    "a w porto": "Porto Azzurro",
    "w porto azzurro": "Porto Azzurro",
    "w porto": "Porto Azzurro",
    "do porto azzurro": "Porto Azzurro",
    "do porto": "Porto Azzurro",
    "z porto azzurro": "Porto Azzurro",
    "z porto": "Porto Azzurro",
    "o porto azzurro": "Porto Azzurro",
    "o porto": "Porto Azzurro",
    "restauracja porto": "Porto Azzurro",
    "restauracji porto": "Porto Azzurro",
    "lokal porto": "Porto Azzurro",
    "lokalu porto": "Porto Azzurro",
    "włoska restauracja": "Porto Azzurro",
    "włoskiej restauracji": "Porto Azzurro"
}


# -----------------------------------------------------------------------------
# SŁOWA STOP (COMMON_WORDS) - do ignorowania w heurystyce
# -----------------------------------------------------------------------------

COMMON_WORDS = {
    # Przyimki i spójniki
    "w", "i", "czy", "o", "a", "ale", "lub", "nie", "na", "do", "z", "za", "od",
    "po", "przy", "dla", "bez", "przez", "pod", "nad", "przed", "między", "że",
    
    # Czasowniki posiłkowe i modalne
    "jest", "są", "ma", "mają", "być", "mieć", "może", "mogę", "chcę", "chce",
    "będzie", "było", "był", "była", "były", "byłem", "byłam",
    
    # Zaimki
    "ja", "ty", "on", "ona", "ono", "my", "wy", "oni", "one",
    "mi", "ci", "mu", "jej", "nam", "wam", "im",
    "mnie", "ciebie", "jego", "ją", "nas", "was", "ich",
    "to", "ten", "ta", "te", "ci", "te", "tamten", "tamta",
    "który", "która", "które", "którzy", "jaki", "jaka", "jakie",
    
    # Powitania i grzeczności
    "cześć", "hej", "dzień", "dobry", "wieczór", "witam", "witaj",
    "proszę", "poproszę", "dziękuję", "dzięki",
    
    # Czasowniki pytające
    "pokaż", "powiedz", "opowiedz", "opisz", "znajdź", "szukaj", "sprawdź",
    "podaj", "przedstaw", "wymień", "wypisz",
    
    # Słowa pytające
    "jaka", "jaki", "jakie", "gdzie", "kiedy", "która", "który", "ile",
    "dlaczego", "czemu", "jak", "co", "kto",
    
    # Inne częste słowa
    "się", "sobie", "też", "także", "również", "tylko", "jeszcze", "już",
    "teraz", "dziś", "dzisiaj", "jutro", "wczoraj", "zawsze", "nigdy",
    "bardzo", "trochę", "mało", "dużo", "więcej", "mniej",
    "wolnych", "miejsc", "stolików", "stolik", "miejsca", "miejscu",
    "restauracja", "restauracji", "restauracje", "lokal", "lokalu", "lokale",
    "kuchnia", "kuchni", "kuchnię", "jedzenie", "jedzenia",
    "dobra", "dobry", "dobre", "ok", "okej", "tak", "nie",
    "tutaj", "tam", "tu", "gdzieś", "wszędzie", "nigdzie"
}


# -----------------------------------------------------------------------------
# SYNONIMY INTENCJI - pomocnicze słowa kluczowe dla rozpoznawania intencji
# -----------------------------------------------------------------------------

INTENT_KEYWORDS = {
    "greet": ["cześć", "hej", "witam", "dzień dobry", "siema", "hello", "hi"],
    "check_seats": ["wolne", "miejsca", "stoliki", "dostępność", "dostępne", "ile"],
    "check_hours": ["godziny", "otwarte", "zamknięte", "czynne", "kiedy", "o której"],
    "check_contact": ["adres", "telefon", "numer", "kontakt", "gdzie", "lokalizacja"],
    "restaurant_info": ["opowiedz", "opisz", "co to", "jaki", "jaka", "informacje"],
    "search_cuisine": ["szukam", "chcę zjeść", "głodny", "kuchnia", "jedzenie"],
    "book_table": ["rezerwacja", "zarezerwuj", "bukuj", "zamów stolik"],
    "list_restaurants": ["lista", "wszystkie", "jakie", "wymień", "pokaż"],
    "ask_recommendation": ["polecasz", "polecisz", "doradź", "co wybrać", "najlepsza"]
}