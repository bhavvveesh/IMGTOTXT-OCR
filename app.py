import os
import io
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OCR_API_KEY")
OCR_URL = "https://api.ocr.space/parse/image"

app = Flask(__name__)

# Optional: Resize large images
def resize_image_if_large(image_bytes, max_size=1000):
    image = Image.open(io.BytesIO(image_bytes))
    image.thumbnail((max_size, max_size))
    buffer = io.BytesIO()
    image.save(buffer, format=image.format)
    return buffer.getvalue()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/extract", methods=["POST"])
def extract_text():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    image_bytes = file.read()

    # Resize if too large
    if len(image_bytes) > 2_000_000:  # 2 MB limit
        image_bytes = resize_image_if_large(image_bytes)

    try:
        response = requests.post(
            OCR_URL,
            files={"filename": (file.filename, image_bytes)},
            data={"apikey": API_KEY, "language": "eng", "isOverlayRequired": False}
        )
        result = response.json()
        print(result)  # Debug

        if result.get("OCRExitCode") != 1:
            error_msg = result.get("ErrorMessage", ["Unknown OCR error"])[0]
            return jsonify({"error": error_msg}), 500

        text = ""
        if result.get("ParsedResults"):
            text = result["ParsedResults"][0]["ParsedText"]

        if not text.strip():
            text = "No text found!"

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
