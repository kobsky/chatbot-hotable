# =============================================================================
# NLP_ENGINE.PY - Silnik przetwarzania języka naturalnego dla Hotable
# =============================================================================

import json
import random
import re
from difflib import SequenceMatcher
from entities import KW_CUISINE, KW_RESTAURANTS, COMMON_WORDS, INTENT_KEYWORDS

class ChatbotBrain:
    """
    Główna klasa odpowiedzialna za:
    - Ładowanie i przetwarzanie intencji
    - Predykcję intencji na podstawie tekstu
    - Ekstrakcję encji (restauracje, kuchnie)
    - Generowanie odpowiedzi
    """
    
    def __init__(self, intents_file='intents.json'):
        """Inicjalizacja silnika NLP"""
        self.intents = self._load_intents(intents_file)
        self.confidence_threshold = 0.25  # Próg pewności dla fallback
        
        # Budowanie indeksu słów kluczowych dla szybszego wyszukiwania
        self._build_pattern_index()
        
        print("✅ NLP Engine załadowany pomyślnie")
    
    def _load_intents(self, filepath):
        """Ładowanie intencji z pliku JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('intents', [])
        except FileNotFoundError:
            print(f"❌ Błąd: Nie znaleziono pliku {filepath}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Błąd parsowania JSON: {e}")
            return []
    
    def _build_pattern_index(self):
        """Budowanie indeksu wzorców dla optymalizacji wyszukiwania"""
        self.pattern_index = {}
        for intent in self.intents:
            tag = intent['tag']
            for pattern in intent.get('patterns', []):
                normalized = self._normalize_text(pattern)
                if normalized not in self.pattern_index:
                    self.pattern_index[normalized] = []
                self.pattern_index[normalized].append(tag)
    
    def _normalize_text(self, text):
        """Normalizacja tekstu - lowercase, usunięcie znaków specjalnych"""
        if not text:
            return ""
        # Zamiana na małe litery
        text = text.lower().strip()
        # Usunięcie znaków interpunkcyjnych (zachowanie polskich znaków)
        text = re.sub(r'[^\w\sąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', '', text)
        # Usunięcie wielokrotnych spacji
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _calculate_similarity(self, text1, text2):
        """Obliczanie podobieństwa między dwoma tekstami"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _word_overlap_score(self, user_words, pattern_words):
        """Obliczanie wyniku nakładania się słów"""
        if not pattern_words:
            return 0
        
        # Filtrowanie słów funkcyjnych
        user_significant = [w for w in user_words if w not in COMMON_WORDS and len(w) > 2]
        pattern_significant = [w for w in pattern_words if w not in COMMON_WORDS and len(w) > 2]
        
        if not pattern_significant:
            return 0
        
        matches = sum(1 for word in user_significant if word in pattern_significant)
        
        # Sprawdzanie częściowych dopasowań
        for u_word in user_significant:
            for p_word in pattern_significant:
                if u_word != p_word:
                    if u_word in p_word or p_word in u_word:
                        matches += 0.5
                    elif self._calculate_similarity(u_word, p_word) > 0.8:
                        matches += 0.7
        
        return matches / len(pattern_significant)
    
    def predict_intent(self, user_message):
        """
        Główna metoda predykcji intencji.
        
        Algorytm:
        1. Dokładne dopasowanie do wzorca
        2. Dopasowanie oparte na podobieństwie
        3. Dopasowanie słów kluczowych
        4. Fallback jeśli poniżej progu
        """
        if not user_message or not user_message.strip():
            return "fallback"
        
        normalized_message = self._normalize_text(user_message)
        user_words = set(normalized_message.split())
        
        # === ETAP 1: Dokładne dopasowanie ===
        if normalized_message in self.pattern_index:
            return self.pattern_index[normalized_message][0]
        
        # === ETAP 2: Dopasowanie z obliczeniem wyniku ===
        best_intent = "fallback"
        best_score = 0
        
        for intent in self.intents:
            tag = intent['tag']
            patterns = intent.get('patterns', [])
            
            for pattern in patterns:
                normalized_pattern = self._normalize_text(pattern)
                pattern_words = set(normalized_pattern.split())
                
                # Obliczanie różnych metryk
                similarity = self._calculate_similarity(normalized_message, normalized_pattern)
                word_overlap = self._word_overlap_score(user_words, pattern_words)
                
                # Sprawdzanie czy wzorzec zawiera się w wiadomości lub odwrotnie
                containment_score = 0
                if normalized_pattern in normalized_message:
                    containment_score = 0.9
                elif normalized_message in normalized_pattern:
                    containment_score = 0.7
                
                # Łączny wynik (ważona średnia)
                combined_score = max(
                    similarity,
                    word_overlap * 0.8,
                    containment_score
                )
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_intent = tag
        
        # === ETAP 3: Sprawdzanie słów kluczowych encji ===
        # Jeśli wynik jest niski, sprawdzamy obecność encji
        if best_score < 0.5:
            # Sprawdzenie czy jest nazwa restauracji -> restaurant_info lub check_seats
            for keyword in KW_RESTAURANTS.keys():
                if keyword in normalized_message:
                    # Sprawdzenie kontekstu
                    if any(w in normalized_message for w in ['ile', 'wolne', 'miejsca', 'stoliki', 'dostępność']):
                        return "check_seats"
                    elif any(w in normalized_message for w in ['adres', 'telefon', 'numer', 'kontakt', 'gdzie jest']):
                        return "check_contact"
                    elif any(w in normalized_message for w in ['godziny', 'otwarte', 'czynne', 'kiedy']):
                        return "check_hours"
                    else:
                        return "restaurant_info"
            
            # Sprawdzenie czy jest nazwa kuchni -> search_cuisine
            for keyword in KW_CUISINE.keys():
                if keyword in normalized_message:
                    return "search_cuisine"
        
        # === ETAP 4: Dodatkowe heurystyki ===
        # Sprawdzenie specyficznych fraz
        if any(phrase in normalized_message for phrase in ['ile miejsc', 'ile stolików', 'wolne stoliki', 'czy są miejsca']):
            return "check_seats"
        
        if any(phrase in normalized_message for phrase in ['jaki adres', 'gdzie jest', 'telefon do', 'kontakt do']):
            return "check_contact"
        
        if any(phrase in normalized_message for phrase in ['godziny otwarcia', 'o której', 'do której', 'kiedy otwarte']):
            return "check_hours"
        
        if any(phrase in normalized_message for phrase in ['co polecasz', 'którą polecasz', 'co wybrać', 'nie wiem co']):
            return "ask_recommendation"
        
        if any(phrase in normalized_message for phrase in ['jakie restauracje', 'lista restauracji', 'pokaż lokale', 'jakie lokale']):
            return "list_restaurants"
        
        if any(phrase in normalized_message for phrase in ['jakie kuchnie', 'rodzaje kuchni', 'typy jedzenia', 'co serwujecie']):
            return "list_cuisines"
        
        # === ETAP 5: Fallback jeśli poniżej progu ===
        if best_score < self.confidence_threshold:
            return "fallback"
        
        return best_intent
    
    def extract_entities(self, user_message):
        """
        Ekstrakcja encji z wiadomości użytkownika.
        
        Zwraca słownik z kluczami:
        - restaurant: nazwa restauracji
        - cuisine: typ kuchni
        """
        entities = {
            'restaurant': None,
            'cuisine': None
        }
        
        if not user_message:
            return entities
        
        normalized = self._normalize_text(user_message)
        
        # Ekstrakcja restauracji (szukamy od najdłuższych fraz)
        sorted_restaurants = sorted(KW_RESTAURANTS.keys(), key=len, reverse=True)
        for keyword in sorted_restaurants:
            if keyword in normalized:
                entities['restaurant'] = KW_RESTAURANTS[keyword]
                break
        
        # Ekstrakcja kuchni (szukamy od najdłuższych fraz)
        sorted_cuisines = sorted(KW_CUISINE.keys(), key=len, reverse=True)
        for keyword in sorted_cuisines:
            if keyword in normalized:
                entities['cuisine'] = KW_CUISINE[keyword]
                break
        
        return entities
    
    def get_response(self, intent_tag):
        """
        Pobieranie losowej odpowiedzi dla danej intencji.
        """
        for intent in self.intents:
            if intent['tag'] == intent_tag:
                responses = intent.get('responses', [])
                if responses:
                    return random.choice(responses)
        
        # Domyślna odpowiedź fallback
        return "Przepraszam, nie zrozumiałem. Spróbuj zapytać inaczej."
    
    def get_intent_confidence(self, user_message):
        """
        Zwraca intencję wraz z poziomem pewności.
        Przydatne do debugowania i logowania.
        """
        if not user_message or not user_message.strip():
            return "fallback", 0.0
        
        normalized_message = self._normalize_text(user_message)
        user_words = set(normalized_message.split())
        
        best_intent = "fallback"
        best_score = 0.0
        
        for intent in self.intents:
            tag = intent['tag']
            patterns = intent.get('patterns', [])
            
            for pattern in patterns:
                normalized_pattern = self._normalize_text(pattern)
                pattern_words = set(normalized_pattern.split())
                
                similarity = self._calculate_similarity(normalized_message, normalized_pattern)
                word_overlap = self._word_overlap_score(user_words, pattern_words)
                
                containment_score = 0
                if normalized_pattern in normalized_message:
                    containment_score = 0.9
                elif normalized_message in normalized_pattern:
                    containment_score = 0.7
                
                combined_score = max(similarity, word_overlap * 0.8, containment_score)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_intent = tag
        
        return best_intent, best_score


# =============================================================================
# TESTY JEDNOSTKOWE (uruchamiane przy bezpośrednim wykonaniu pliku)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTY NLP ENGINE")
    print("=" * 60)
    
    brain = ChatbotBrain()
    
    test_cases = [
        # Powitania
        ("Cześć", "greet"),
        ("Dzień dobry", "greet"),
        ("Hej!", "greet"),
        
        # Cel bota
        ("Co potrafisz?", "bot_purpose"),
        ("Kim jesteś?", "bot_purpose"),
        
        # Wyszukiwanie kuchni
        ("Szukam włoskiej", "search_cuisine"),
        ("Gdzie zjem streetfood?", "search_cuisine"),
        ("Mam ochotę na kuchnię polską", "search_cuisine"),
        
        # Sprawdzanie miejsc
        ("Ile miejsc ma Neon?", "check_seats"),
        ("Gdzie są wolne stoliki?", "check_seats"),
        ("Czy są miejsca?", "check_seats"),
        
        # Kontakt
        ("Jaki adres?", "check_contact"),
        ("Numer telefonu do Zielnika", "check_contact"),
        
        # Info o restauracji
        ("Opowiedz o Neonie", "restaurant_info"),
        ("Co to za lokal?", "restaurant_info"),
        
        # Rekomendacje
        ("Co polecasz?", "ask_recommendation"),
        ("Nie wiem co wybrać", "ask_recommendation"),
        
        # Rezerwacja
        ("Zarezerwuj stolik", "book_table"),
        
        # Poza zakresem
        ("Jaka jest pogoda?", "out_of_scope"),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected_intent in test_cases:
        predicted = brain.predict_intent(message)
        intent_with_conf = brain.get_intent_confidence(message)
        
        status = "✅" if predicted == expected_intent else "❌"
        if predicted == expected_intent:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} '{message}'")
        print(f"   Oczekiwano: {expected_intent} | Otrzymano: {predicted} (pewność: {intent_with_conf[1]:.2f})")
        print()
    
    print("=" * 60)
    print(f"WYNIKI: {passed}/{len(test_cases)} testów przeszło pomyślnie")
    print(f"Współczynnik sukcesu: {(passed/len(test_cases))*100:.1f}%")
    print("=" * 60)