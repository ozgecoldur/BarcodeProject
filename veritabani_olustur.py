import sqlite3
import os

DB_FILE = "products.db"

def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Tablo oluştur
        cursor.execute("""
        CREATE TABLE urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barkod TEXT UNIQUE,
            urun_adi TEXT,
            marka TEXT,
            fiyat REAL
        )
        """)
        # Örnek ürünler ekle
        urunler = [
            ("8697471724110004526628", "Namet Soslu Pişmiş Dondurulmuş Dana Misket", "Ülker", 15.0),
            ("0108697471723723100001111111", "Ayran 1L", "Sütaş", 12.5),
            ("012148613", "Çikolata", "Nestle", 10.0),
            ("8690526098723", "Kahve 250g", "Nescafe", 45.0),
            ("8690889098123", "Soda 500ml", "Saka", 8.0)
        ]
        cursor.executemany("INSERT INTO urunler (barkod, urun_adi, marka, fiyat) VALUES (?, ?, ?, ?)", urunler)
        conn.commit()
        conn.close()

def barkod_sorgula(barkod):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT urun_adi, marka, fiyat FROM urunler WHERE barkod=?", (barkod,))
    result = cursor.fetchone()
    conn.close()
    return result
