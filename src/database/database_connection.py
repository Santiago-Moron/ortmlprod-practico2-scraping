import sqlite3

from src.settings.settings import load_settings
from src.structs.property import Property

settings = load_settings(key="Scraper")
DB_PATH = settings["DBpath"]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            link       TEXT    NOT NULL,
            type       REAL    NOT NULL,
            neighborhood    TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_properties(properties: list[Property]):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR IGNORE INTO properties (name, link, type, neighborhood)
            VALUES (:name, :link, :type, :neighborhood)
        """, [
            {
                "name":          p.id,
                "link":         p.link,
                "type":         p.type.value,         
                "neighborhood": p.details.neighborhood if p.details else None
            }
            for p in properties
        ])
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting properties: {e}")
        conn.rollback()
    except AttributeError as e:
        print(f"Incorrect data could not be inserted: {e}")
        conn.rollback()
    finally:
        conn.close()

def show_all():
    conn = get_connection()
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM properties")
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            print(dict(row))
    except sqlite3.Error as e:
        print(f"Error showing properties: {e}")
    finally:
        conn.close()
