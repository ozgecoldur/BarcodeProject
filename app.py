import os
import subprocess
from flask import Flask, request, render_template

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

    # Dosyayı kaydet
    filepath = os.path.abspath(os.path.join(UPLOAD_FOLDER, file.filename))
    filepath = filepath.replace("\\", "/")  # Windows uyumluluğu
    file.save(filepath)

    try:
        # Windows için classpath
        classpath = "lib/core-3.5.3.jar;lib/javase-3.5.3.jar;lib/jcommander-1.81.jar;."

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

        if barcode_value:
            return f"<h2>Barkod Değeri:</h2><p>{barcode_value}</p>"
        else:
            return f"<pre>{result.stdout}</pre>"

    except subprocess.CalledProcessError as e:
        return f"Hata: {e.stderr}", 500

if __name__ == "__main__":
    app.run(debug=True)
