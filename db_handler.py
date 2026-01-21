# =============================================================================
# DB_HANDLER.PY - Obsługa bazy danych Supabase dla Hotable (REST API)
# =============================================================================

import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Ładowanie zmiennych środowiskowych
load_dotenv()

class DatabaseHandler:
    """
    Klasa obsługująca operacje na bazie danych Supabase przez REST API.
    Przechowuje informacje o restauracjach i ich dostępności.
    """
    
    def __init__(self):
        """Inicjalizacja połączenia z Supabase"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("❌ Brak SUPABASE_URL lub SUPABASE_KEY w zmiennych środowiskowych!")
        
        # Bazowy URL dla REST API
        self.rest_url = f"{self.supabase_url}/rest/v1"
        
        # Nagłówki dla wszystkich zapytań
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Test połączenia
        if self._test_connection():
            print("✅ Połączono z Supabase")
        else:
            print("⚠️ Supabase dostępne, ale tabela może być pusta")
    
    def _test_connection(self) -> bool:
        """Test połączenia z bazą danych"""
        try:
            response = requests.get(
                f"{self.rest_url}/restaurants?select=count",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Błąd połączenia: {e}")
            return False
    
    def _make_request(self, endpoint: str, method: str = "GET", params: dict = None, data: dict = None) -> Optional[List[Dict]]:
        """Wykonanie zapytania do Supabase REST API"""
        try:
            url = f"{self.rest_url}/{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, params=params, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, params=params, timeout=10)
            else:
                return None
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"⚠️ API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Timeout połączenia z Supabase")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Błąd zapytania: {e}")
            return None
    
    def get_all_restaurants(self) -> List[Dict]:
        """Pobieranie wszystkich restauracji z Supabase"""
        result = self._make_request("restaurants", params={"select": "*", "order": "name"})
        return result if result else []
    
    def get_restaurants_by_cuisine(self, cuisine: str) -> List[Dict]:
        """Pobieranie restauracji według typu kuchni (ignoruje wielkość liter)."""
        result = self._make_request(
            "restaurants",
            params={"select": "*", "cuisine": f"ilike.%{cuisine}%"}
        )
        return result if result else []
    
    def check_availability(self, restaurant_name: str) -> Optional[Dict]:
        """Sprawdzanie dostępności stolików w konkretnej restauracji"""
        # Próba dokładnego dopasowania (case-insensitive)
        result = self._make_request(
            "restaurants",
            params={"select": "*", "name": f"ilike.{restaurant_name}"}
        )
        
        if result and len(result) > 0:
            return result[0]
        
        # Próba częściowego dopasowania
        result = self._make_request(
            "restaurants",
            params={"select": "*", "name": f"ilike.%{restaurant_name}%"}
        )
        
        if result and len(result) > 0:
            return result[0]
        
        return None
    
    def get_restaurant_details(self, restaurant_name: str) -> Optional[Dict]:
        """Pobieranie szczegółowych informacji o restauracji"""
        return self.check_availability(restaurant_name)
    
    def get_restaurant_description(self, restaurant_name: str) -> Optional[str]:
        """Pobieranie opisu restauracji"""
        result = self._make_request(
            "restaurants",
            params={"select": "description", "name": f"ilike.{restaurant_name}"}
        )
        
        if result and len(result) > 0:
            return result[0].get('description')
        return None
    
    def update_availability(self, restaurant_name: str, available_tables: int) -> bool:
        """Aktualizacja liczby dostępnych stolików"""
        result = self._make_request(
            "restaurants",
            method="PATCH",
            params={"name": f"ilike.{restaurant_name}"},
            data={"available_tables": available_tables}
        )
        
        return result is not None and len(result) > 0


# =============================================================================
# TESTY POŁĄCZENIA
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("TEST POŁĄCZENIA Z SUPABASE")
    print("=" * 50)
    
    try:
        db = DatabaseHandler()
        
        print("\n📋 Wszystkie restauracje:")
        restaurants = db.get_all_restaurants()
        if restaurants:
            for r in restaurants:
                name = r.get('name', 'N/A')
                available = r.get('available_tables', 'N/A')
                max_t = r.get('max_tables', 'N/A')
                print(f"  - {name}: {available}/{max_t} stolików")
        else:
            print("  Brak danych lub pusta tabela")
        
        print("\n🍕 Test pobierania po kuchni (Polska):")
        polish = db.get_restaurants_by_cuisine("polska")
        if polish:
            for r in polish:
                print(f"  - {r.get('name')}")
        else:
            print("  Brak wyników")
        
        print("\n🔍 Test sprawdzania dostępności (Neon):")
        neon = db.check_availability("Neon")
        if neon:
            print(f"  Dostępne stoliki: {neon.get('available_tables')}")
            print(f"  Telefon: {neon.get('phone')}")
        else:
            print("  Nie znaleziono")
            
        print("\n✅ Test zakończony!")
        
    except Exception as e:
        print(f"\n❌ Błąd testu: {e}")
