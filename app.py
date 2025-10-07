import os
import subprocess
from flask import Flask, request, render_template, send_file
import cv2
import numpy as np
import sqlite3
import pytesseract
import re

# Tesseract yolu
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\pln236\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# -------------------- Veritabanı --------------------
DB_FILE = "product.db"

def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barkod TEXT UNIQUE,
            urun_adi TEXT,
            marka TEXT,
            fiyat REAL
        )
        """)
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
    cursor.execute("SELECT urun_adi, marka, fiyat FROM urunler WHERE barkod=?", (barkod.strip(),))
    result = cursor.fetchone()
    conn.close()
    return result

init_db()

# -------------------- Flask --------------------
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

    # 🔽 Ön işleme
    img = cv2.imread(filepath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite(filepath, thresh)

    # -------------------- OCR ile metin --------------------
    ocr_text = pytesseract.image_to_string(img, lang="tur")

    # -------------------- Barkod çöz --------------------
    barcode_values = []
    classpath = "lib/core-3.5.3.jar;lib/javase-3.5.3.jar;lib/jcommander-1.81.jar;."

    # 1️⃣ Java ZXing
    try:
        result = subprocess.run(
            ["java", "-cp", classpath, "DecodeBarcode", filepath],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if "Parsed result:" in line:
                val = line.split("Parsed result:", 1)[1].strip()  # tüm satırı al
                barcode_values.append(val)
    except subprocess.CalledProcessError:
        pass

    # 2️⃣ OCR’den barkod yakala (boşlukları temizle)
    if ocr_text:
        ocr_barcodes = re.findall(r"\d[\d\s]{8,}", ocr_text)
        ocr_barcodes = [re.sub(r"\s+", "", b) for b in ocr_barcodes]
        barcode_values.extend(ocr_barcodes)

    # 3️⃣ Tekrarlardan temizle
    barcode_values = list(dict.fromkeys(barcode_values))

    # 4️⃣ En uzun barkodu seç
    barcode_value = max(barcode_values, key=len) if barcode_values else "⚠️ Barkod değeri okunamadı"

    # 5️⃣ Eğer hiç barkod yoksa placeholder
    if not barcode_values:
        barcode_values = ["⚠️ Barkod değeri okunamadı"]

    # -------------------- Barkod kutusu çiz --------------------
    img = cv2.imread(filepath)
    if img is not None:
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
    if img is not None:
        cv2.imwrite(processed_path, img)

    # -------------------- Veritabanı sorgusu --------------------
    urun_adi, marka, fiyat = ("-", "-", "-")
    urun_bilgisi = None
    if barcode_value and not barcode_value.startswith("⚠️"):
        veri = barkod_sorgula(barcode_value)
        if veri:
            urun_adi, marka, fiyat = veri
            urun_bilgisi = {
                "Barkod": barcode_value,
                "Ürün Adı": urun_adi,
                "Marka": marka,
                "Fiyat": fiyat
            }
        else:
            urun_bilgisi = {
                "Barkod": barcode_value,
                "Bilgi": "Ürün veritabanında bulunamadı"
            }

    return render_template(
        "result.html",
        original_filename=file.filename,
        processed_filename=processed_filename,
        barcode_values=barcode_values,   # 🔹 tüm barkodlar
        barcode_value=barcode_value,     # 🔹 en uzun barkod
        ocr_text=ocr_text,
        urun_bilgisi=urun_bilgisi
    )

@app.route("/show/<filename>")
def show_image(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

if __name__ == "__main__":
    app.run(debug=True)
