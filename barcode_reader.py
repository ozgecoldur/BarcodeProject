import subprocess
import os

ZXING_CORE_JAR = os.path.join("libs", "core-3.5.3.jar")
ZXING_JAVASE_JAR = os.path.join("libs", "javase-3.5.3.jar")
JCOMMANDER_JAR = os.path.join("libs", "jcommander-1.81.jar")

def decode_barcode(image_path):
    classpath = f"{ZXING_CORE_JAR};{ZXING_JAVASE_JAR};{JCOMMANDER_JAR}"

    command = [
        "java",
        "-cp",
        classpath,
        "com.google.zxing.client.j2se.CommandLineRunner",
        image_path
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Hata oluştu:", e.stderr)
        return None

# Örnek kullanım
decoded = decode_barcode("example.png")
print(decoded)


