# =============================================================================
# DB_HANDLER.PY - Obsługa bazy danych dla Hotable
# =============================================================================

import sqlite3
import os
from typing import List, Dict, Optional

class DatabaseHandler:
    """
    Klasa obsługująca operacje na bazie danych SQLite.
    Przechowuje informacje o restauracjach i ich dostępności.
    """
    
    def __init__(self, db_path: str = 'hotable.db'):
        """Inicjalizacja połączenia z bazą danych"""
        self.db_path = db_path
        self._initialize_database()
        print("✅ Baza danych załadowana")
    
    def _get_connection(self):
        """Utworzenie nowego połączenia z bazą"""
        return sqlite3.connect(self.db_path)
    
    def _initialize_database(self):
        """Inicjalizacja struktury bazy danych i danych początkowych"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tworzenie tabeli restauracji
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                cuisine TEXT NOT NULL,
                available_tables INTEGER DEFAULT 0,
                max_tables INTEGER DEFAULT 10,
                phone TEXT,
                address TEXT,
                hours TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Dane początkowe restauracji
        initial_data = [
            ('Neon', 'StreetFood', 4, 10, '+48 890 211 403', 'ul. Obłońska 4', '09:00 - 23:00'),
            ('Porto Azzurro', 'Śródziemnomorska', 2, 15, '+48 912 901 733', 'ul. Podwale 7A', '09:00 - 21:00'),
            ('Zielnik', 'Polska', 3, 6, '+48 730 100 200', 'ul. Wiosenna 14', '09:00 - 21:00')
        ]
        
        for data in initial_data:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO restaurants 
                    (name, cuisine, available_tables, max_tables, phone, address, hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', data)
            except sqlite3.IntegrityError:
                pass
        
        conn.commit()
        conn.close()
    
    def get_all_restaurants(self) -> List[Dict]:
        """Pobieranie wszystkich restauracji"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, cuisine, available_tables, max_tables, phone, address, hours
            FROM restaurants
            ORDER BY name
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'name': row[0],
                'cuisine': row[1],
                'available_tables': row[2],
                'max_tables': row[3],
                'phone': row[4],
                'address': row[5],
                'hours': row[6]
            }
            for row in rows
        ]
    
    def get_restaurants_by_cuisine(self, cuisine: str) -> List[Dict]:
        """Pobieranie restauracji według typu kuchni"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, cuisine, available_tables, max_tables, phone, address, hours
            FROM restaurants
            WHERE cuisine = ? OR cuisine LIKE ?
            ORDER BY name
        ''', (cuisine, f'%{cuisine}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'name': row[0],
                'cuisine': row[1],
                'available_tables': row[2],
                'max_tables': row[3],
                'phone': row[4],
                'address': row[5],
                'hours': row[6]
            }
            for row in rows
        ]
    
    def check_availability(self, restaurant_name: str) -> Optional[Dict]:
        """Sprawdzanie dostępności stolików w konkretnej restauracji"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, cuisine, available_tables, max_tables, phone, address, hours
            FROM restaurants
            WHERE LOWER(name) = LOWER(?)
        ''', (restaurant_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'name': row[0],
                'cuisine': row[1],
                'available_tables': row[2],
                'max_tables': row[3],
                'phone': row[4],
                'address': row[5],
                'hours': row[6]
            }
        return None
    
    def update_availability(self, restaurant_name: str, available_tables: int) -> bool:
        """Aktualizacja liczby dostępnych stolików"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE restaurants
            SET available_tables = ?, updated_at = CURRENT_TIMESTAMP
            WHERE LOWER(name) = LOWER(?)
        ''', (available_tables, restaurant_name))
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected_rows > 0
    
    def get_restaurant_details(self, restaurant_name: str) -> Optional[Dict]:
        """Pobieranie szczegółowych informacji o restauracji"""
        return self.check_availability(restaurant_name)


# =============================================================================
# TESTY
# =============================================================================

if __name__ == "__main__":
    print("Test bazy danych...")
    db = DatabaseHandler()
    
    print("\n📋 Wszystkie restauracje:")
    for r in db.get_all_restaurants():
        print(f"  - {r['name']}: {r['available_tables']}/{r['max_tables']} stolików")
    
    print("\n🍕 Restauracje śródziemnomorskie:")
    for r in db.get_restaurants_by_cuisine("Śródziemnomorska"):
        print(f"  - {r['name']}")
    
    print("\n🔍 Szczegóły Neon:")
    details = db.check_availability("Neon")
    if details:
        print(f"  Dostępne stoliki: {details['available_tables']}")
        print(f"  Telefon: {details['phone']}")