# LOGIC_AUDIT.md

## 1. Analiza intents.json

- **Zdefiniowane intencje**: W pliku `intents.json` zdefiniowano następujące intencje:
  - `greet`
  - `search_cuisine`
  - `check_seats`
  - `check_hours`
  - `fallback`

- **Zgodność z wymaganiami**:
  - Intencja `search_restaurants` ze specyfikacji jest zaimplementowana jako `search_cuisine`. Funkcjonalnie odpowiada to wymaganiom, jest to jedynie różnica w nazewnictwie.
  - Intencja `check_hours` **istnieje** w pliku, wbrew pierwotnym podejrzeniom.
  - Wszystkie pozostałe wymagane intencje (`greet`, `check_availability` jako `check_seats`) są obecne.

- **Analiza intencji `fallback`**: Intencja `fallback` istnieje, ale jej treść odpowiedzi jest **niezgodna ze specyfikacją**.
  - **Obecna treść**: `["Sorki, nie do końca zrozumiałem. 🧐 Możesz zapytać o konkretną kuchnię (np. włoską) albo dostępność w lokalu.", "Jeszcze się uczę i tego nie złapałem. Szukasz restauracji czy wolnego stolika?"]`
  - **Oczekiwana treść**: `"Przykro mi nie mogę Ci jeszcze w tym pomóc, jestem w fazie prototypu."`

## 2. Analiza Jakości Danych

- **Różnorodność wzorców (patterns)**: Wzorce w `intents.json` są stosunkowo różnorodne. Na przykład intencja `search_cuisine` zawiera zarówno frazy z konkretną kuchnią ("Szukam kuchni włoskiej"), jak i ogólne pytania ("Co polecasz na obiad?"). To dobra podstawa do treningu modelu.

- **Wyciąganie encji**: Plik `entities.py` zawiera słowniki `KW_CUISINE` i `KW_RESTAURANTS`, które mapują różne warianty słów (np. "neonie", "urban kitchen") na jedną, kanoniczną nazwę ("Neon"). Jest to solidne i kluczowe dla działania bota rozwiązanie.

## 3. Analiza Logiki (nlp_engine.py)

- **Mechanizm Fallback**: Fallback jest zrealizowany jako **dedykowana intencja w `intents.json`**. Nie ma mechanizmu "hardcoded" opartego o próg pewności (confidence score) w `nlp_engine.py`. Funkcja `predict_intent` zawsze zwraca jakąś etykietę, której nauczył się model.
  - **Problem**: Intencja `fallback` ma pustą listę wzorców (`"patterns": []`). Oznacza to, że model AI **nigdy się jej nie nauczy** i w rezultacie **nigdy jej nie przewidzi**. Domyślne odpowiedzi "fallback" są więc w praktyce nie do osiągnięcia. Bot, zamiast użyć tej intencji, zawsze wybierze którąś z pozostałych, nawet jeśli z niską pewnością.

- **Obsługa encji**: **TAK**. Logika wyciągania encji jest zaimplementowana w funkcji `extract_entities` w `nlp_engine.py`. Funkcja ta iteruje po słownikach zdefiniowanych w `entities.py` i szuka słów kluczowych w tekście użytkownika, co jest zgodne z założeniami projektu dla intencji `search_cuisine` (`search_restaurants`) i `check_seats`.
