import json
import random
import numpy as np
# Biblioteki do Machine Learningu (Realizacja L9 i L12)
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Importujemy nasz słownik encji (Realizacja L4)
from entities import KW_CUISINE, KW_RESTAURANTS

class ChatbotBrain:
    def __init__(self):
        self.model = None
        self.intents_data = {}
        self.load_data_and_train()

    def load_data_and_train(self):
        """
        Ładuje dane z intents.json i trenuje model w locie.
        (Realizacja L5 - Pozyskiwanie danych treningowych)
        """
        try:
            with open('intents.json', 'r', encoding='utf-8') as f:
                self.intents_data = json.load(f)
        except FileNotFoundError:
            print("BŁĄD: Nie znaleziono pliku intents.json!")
            return

        training_sentences = []
        training_labels = []

        # Przygotowanie danych do scikit-learn
        for intent in self.intents_data['intents']:
            for pattern in intent['patterns']:
                training_sentences.append(pattern)
                training_labels.append(intent['tag'])

        # TWORZENIE POTOKU (PIPELINE) - Realizacja L9
        self.model = make_pipeline(CountVectorizer(), MultinomialNB())
        
        # Trenowanie modelu
        self.model.fit(training_sentences, training_labels)
        print("✅ Model AI został wytrenowany pomyślnie!")

    def predict_intent(self, text):
        """
        Przewiduje intencję użytkownika na podstawie tekstu, z progiem pewności.
        """
        if not self.model:
            return "fallback"

        # Używamy predict_proba zamiast predict
        probabilities = self.model.predict_proba([text])[0]
        max_proba = np.max(probabilities)
        best_intent_index = np.argmax(probabilities)
        
        # Debug print (pomocny przy testach)
        print(f"DEBUG: Text='{text}', Max Proba={max_proba:.2f}, Intent={self.model.classes_[best_intent_index]}")

        if max_proba < 0.25:
            return "fallback"
        else:
            return self.model.classes_[best_intent_index]

    def extract_entities(self, text):
        """
        Wyciąga słowa kluczowe (kuchnia, restauracja) metodą słownikową.
        (Realizacja L4 - Plik domeny)
        """
        text_lower = text.lower()
        found_entities = {}

        # 1. Szukamy kuchni (np. "polska")
        for word, canonical_name in KW_CUISINE.items():
            if word in text_lower:
                found_entities['cuisine'] = canonical_name
                break # Znaleziono, przerywamy szukanie kuchni

        # 2. Szukamy restauracji (np. "zielniku")
        for word, canonical_name in KW_RESTAURANTS.items():
            if word in text_lower:
                found_entities['restaurant'] = canonical_name
                break

        return found_entities

    def get_response(self, intent_tag):
        """
        Pobiera losową odpowiedź z intents.json dla danej intencji.
        """
        for intent in self.intents_data['intents']:
            if intent['tag'] == intent_tag:
                return random.choice(intent['responses'])
        return "Przepraszam, coś poszło nie tak."

# --- TESTOWANIE LOKALNE (Tylko gdy uruchamiasz ten plik bezpośrednio) ---
if __name__ == "__main__":
    bot = ChatbotBrain()
    
    print("\n--- TEST SILNIKA NLP ---")
    test_phrases = [
        "Cześć, jestem głodny",
        "Szukam kuchni włoskiej",
        "Czy są miejsca w Zielniku?",
        "O której zamykają Neon?",
        "jaka jest pogoda?"
    ]
    
    for text in test_phrases:
        intent = bot.predict_intent(text)
        entities = bot.extract_entities(text)
        response = bot.get_response(intent)
        print(f"Tekst: '{text}' -> Intencja: {intent} | Encje: {entities} | Odpowiedź: {response}")
