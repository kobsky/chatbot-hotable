import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Ładowanie kluczy z pliku .env
load_dotenv()

class DatabaseHandler:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            print("❌ BŁĄD: Brak kluczy Supabase w pliku .env!")
            self.supabase = None
        else:
            try:
                self.supabase: Client = create_client(url, key)
            except Exception as e:
                print(f"❌ Błąd połączenia z Supabase: {e}")
                self.supabase = None

    def get_restaurants_by_cuisine(self, cuisine_name):
        """
        Szuka restauracji po typie kuchni.
        Zwraca listę słowników.
        """
        if not self.supabase: return []
        
        try:
            response = self.supabase.table('restaurants') \
                .select("name, description, price_range, available_tables, cuisine_type") \
                .contains('cuisine_type', [cuisine_name]) \
                .execute()
            
            results = response.data
            # Filtr wykluczający nieaktywną restaurację "Trawnik"
            results = [r for r in results if r['name'] != 'Trawnik']
            
            return results
        except Exception as e:
            print(f"Błąd DB (kuchnia): {e}")
            return []

    def check_availability(self, restaurant_name):
        """
        Sprawdza liczbę wolnych stolików w konkretnej restauracji.
        """
        if not self.supabase: return None

        try:
            response = self.supabase.table('restaurants') \
                .select("name, available_tables") \
                .ilike('name', f"%{restaurant_name}%") \
                .execute()
            
            data = response.data
            if data and len(data) > 0:
                return data[0]
            return None
        except Exception as e:
            print(f"Błąd DB (dostępność): {e}")
            return None

# --- TESTOWANIE LOKALNE ---
if __name__ == "__main__":
    db = DatabaseHandler()
    
    print("\n--- TEST 1: Sprawdzenie dostępności (Zielnik) ---")
    lokal = "Zielnik"
    wynik = db.check_availability(lokal)
    
    if wynik:
        print(f"✅ SUKCES! Znaleziono lokal: {wynik['name']}")
        print(f"   Wolne stoliki: {wynik['available_tables']}") 
    else:
        print(f"❌ Nie znaleziono lokalu: {lokal}")

    print("\n--- TEST 2: Szukanie po kuchni (Polska) ---")
    # Teraz powinno zadziałać, bo szukamy elementu ["Polska"] w tablicy
    kuchnia = "Polska"
    wynik_kuchnia = db.get_restaurants_by_cuisine(kuchnia)
    
    if wynik_kuchnia:
        print(f"✅ SUKCES! Znaleziono {len(wynik_kuchnia)} restauracji:")
        for r in wynik_kuchnia:
            # cuisine_type może być listą, więc bezpiecznie wyświetlamy
            print(f"   - {r['name']} (Tagi: {r.get('cuisine_type')})")
    else:
        print(f"⚠️ Nie znaleziono restauracji dla kuchni: {kuchnia}")