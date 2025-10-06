import os
import subprocess
from flask import Flask, request, render_template, send_file
import cv2
import numpy as np
import sqlite3

# -------------------- Veritabanı --------------------
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
            ("8698643321543", "Ayran 1L", "Sütaş", 12.5),
            ("8690812410012", "Çikolata", "Nestle", 10.0),
            ("8690526098723", "Kahve 250g", "Nescafe", 45.0),
            ("8690889098123", "Soda 500ml", "Saka", 8.0)
        ]
        cursor.executemany(
            "INSERT INTO urunler (barkod, urun_adi, marka, fiyat) VALUES (?, ?, ?, ?)",
            urunler
        )
        conn.commit()
        conn.close()

def barkod_sorgula(barkod):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT urun_adi, marka, fiyat FROM urunler WHERE barkod=?",
        (barkod.strip(),)  # boşluk ve satır sonlarını temizle
    )
    result = cursor.fetchone()
    conn.close()
    return result

# Veritabanını başlat
init_db()

# -------------------- Flask Uygulaması --------------------
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "Dosya seçilmedi", 400
    file = request.files["file"]
    if file.filename == "":
        return "Dosya seçilmedi", 400

    filepath = os.path.abspath(os.path.join(UPLOAD_FOLDER, file.filename)).replace("\\", "/")
    file.save(filepath)

    # -------------------- Java ZXing ile barkod okuma --------------------
    classpath = "lib/core-3.5.3.jar;lib/javase-3.5.3.jar;lib/jcommander-1.81.jar;."
    try:
        result = subprocess.run(
            ["java", "-cp", classpath, "DecodeBarcode", filepath],
            capture_output=True,
            text=True,
            check=True,
        )
        barcode_value = None
        for line in result.stdout.splitlines():
            if "Parsed result:" in line:
                barcode_value = line.split("Parsed result:")[1].strip()
                break

        if barcode_value:
            barcode_value = barcode_value.strip()  # boşluk ve satır sonlarını kaldır
        else:
            barcode_value = "⚠️ Barkod değeri okunamadı"

    except subprocess.CalledProcessError as e:
        return f"Hata: {e.stderr}", 500

    # -------------------- Barkod kutusu çizimi (OpenCV) --------------------
    img = cv2.imread(filepath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0)
    gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1)
    gradient = cv2.subtract(gradX, gradY)
    gradient = cv2.convertScaleAbs(gradient)
    blurred = cv2.GaussianBlur(gradient, (9, 9), 0)
    _, thresh = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    closed = cv2.erode(closed, None, iterations=4)
    closed = cv2.dilate(closed, None, iterations=4)
    contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
        box = box.astype(np.int32)
        cv2.drawContours(img, [box], -1, (0, 255, 0), 2)

    processed_filename = os.path.splitext(file.filename)[0] + "_processed.jpeg"
    processed_path = os.path.join(UPLOAD_FOLDER, processed_filename)
    cv2.imwrite(processed_path, img)

    # -------------------- Veritabanından ürün bilgisi çek --------------------
    urun_adi, marka, fiyat = ("-", "-", "-")
    if barcode_value and not barcode_value.startswith("⚠️"):
        veri = barkod_sorgula(barcode_value)
        if veri:
            urun_adi, marka, fiyat = veri
        else:
            urun_adi = "Ürün bulunamadı"

    return render_template(
        "result.html",
        original_filename=file.filename,
        processed_filename=processed_filename,
        barcode_value=barcode_value,
        urun_adi=urun_adi,
        marka=marka,
        fiyat=fiyat
    )

@app.route("/show/<filename>")
def show_image(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

if __name__ == "__main__":
    app.run(debug=True)
