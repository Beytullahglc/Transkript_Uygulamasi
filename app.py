from flask import Flask, request, jsonify
from flask_cors import CORS
import whisper
import os
import torch

app = Flask(__name__)
CORS(app)

models_cache = {}

# GPU'nun mevcut olup olmadığını kontrol eden fonksiyon
def check_device():
    if torch.cuda.is_available():
        return torch.device("cuda")  # GPU kullan
    else:
        return torch.device("cpu")  # CPU kullan

# Modeli yüklerken GPU veya CPU'yu kullanacak şekilde ayarları yapıyoruz
def get_or_load_model(model_type):
    if model_type not in models_cache:
        try:
            device = check_device()  # Cihazı kontrol et
            print(f"Model {model_type} için {device} kullanılıyor...")
            # Modeli belirtilen cihaza yükle
            models_cache[model_type] = whisper.load_model(model_type).to(device)
        except Exception as e:
            raise RuntimeError(f"Model yüklenemedi: {str(e)}")
    else:
        print(f"Model {model_type} önbellekten (cache) yükleniyor.")
    return models_cache[model_type]

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "Ses dosyası yüklenmedi"}), 400

    audio_file = request.files["audio"]
    language = request.form.get("language", "en")
    model_type = request.form.get("model", "base")

    try:
        model = get_or_load_model(model_type)  # Modeli yükle
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, audio_file.filename)
    audio_file.save(file_path)

    try:
        result = model.transcribe(file_path, language=language)
        return jsonify({"transcript": result["text"]})
    except Exception as e:
        return jsonify({"error": f"Transkript başarısız: {str(e)}"}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
