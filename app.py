import os
import subprocess
from flask import Flask, request, render_template, send_file, url_for
import cv2
import numpy as np

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ana sayfa: barkod yükleme
@app.route("/")
def index():
    return render_template("index.html")

# Yükleme ve işleme
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "Dosya seçilmedi", 400
    file = request.files["file"]
    if file.filename == "":
        return "Dosya seçilmedi", 400

    # Dosyayı kaydet
    filepath = os.path.abspath(os.path.join(UPLOAD_FOLDER, file.filename))
    filepath = filepath.replace("\\", "/")  # Windows uyumluluğu
    file.save(filepath)

    # --- Java ile barkod okuma ---
    classpath = "lib/core-3.5.3.jar;lib/javase-3.5.3.jar;lib/jcommander-1.81.jar;."
    try:
        result = subprocess.run(
            [
                "java",
                "-cp",
                classpath,
                "DecodeBarcode",
                filepath,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parsed result satırını çek
        barcode_value = None
        for line in result.stdout.splitlines():
            if "Parsed result:" in line:
                barcode_value = line.split("Parsed result:")[1].strip()
                break
        if not barcode_value:
            barcode_value = "⚠️ Barkod değeri okunamadı"

    except subprocess.CalledProcessError as e:
        return f"Hata: {e.stderr}", 500

    # --- OpenCV ile barkod kutusu çizme ---
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

    # Bulunan alanları işaretle
    for c in contours:
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
        box = box.astype(np.int32)  
        cv2.drawContours(img, [box], -1, (0, 255, 0), 2)

    # İşlenmiş resmi kaydet
    processed_filename = os.path.splitext(file.filename)[0] + "_processed.jpeg"
    processed_path = os.path.join(UPLOAD_FOLDER, processed_filename)
    cv2.imwrite(processed_path, img)

    # Sonuç sayfasını render et
    return render_template(
        "result.html",
        original_filename=file.filename,
        processed_filename=processed_filename,
        barcode_value=barcode_value
    )

# Resimleri göstermek için route
@app.route("/show/<filename>")
def show_image(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

if __name__ == "__main__":
    app.run(debug=True)
