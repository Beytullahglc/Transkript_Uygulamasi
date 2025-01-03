from flask import Flask, request, jsonify
from flask_cors import CORS
import whisper
import os
import torch
from pyannote.audio import Pipeline
from pathlib import Path
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)

models_cache = {}
speaker_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")

def check_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")

def get_or_load_model(model_type):
    if model_type not in models_cache:
        try:
            device = check_device()
            print(f"Model {model_type} için {device} kullanılıyor...")
            models_cache[model_type] = whisper.load_model(model_type).to(device)
        except Exception as e:
            raise RuntimeError(f"Model yüklenemedi: {str(e)}")
    else:
        print(f"Model {model_type} önbellekten (cache) yükleniyor.")
    return models_cache[model_type]

def format_transcript_with_speakers(segments, diarization):
    formatted_transcript = ""
    previous_speaker = None

    for segment in segments:
        segment_start = segment['start']
        segment_end = segment['end']
        segment_text = segment['text']

        current_speaker = None
        for turn, _, speaker in diarization:
            if turn.start <= segment_start <= turn.end or turn.start <= segment_end <= turn.end:
                current_speaker = speaker
                break

        # Konuşmacı değişimi durumunda alt satıra geç
        if current_speaker != previous_speaker:
            if formatted_transcript:  # Önceki bir metin varsa boş bir satır ekle
                formatted_transcript += "\n"
            previous_speaker = current_speaker

        # Segment metnini ekle
        formatted_transcript += f"{segment_text.strip()}\n"

    return formatted_transcript

def perform_speaker_diarization(audio_file):
    try:
        diarization = speaker_pipeline(audio_file)
        return list(diarization.itertracks(yield_label=True))
    except Exception as e:
        raise RuntimeError(f"Konuşmacı ayrımı hatası: {str(e)}")

def convert_to_wav(input_file, output_file):
    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_channels(1).set_frame_rate(16000)  # Pyannote için mono ve 16kHz ayarı
        audio.export(output_file, format="wav")
        print(f"Dosya başarıyla {output_file} olarak dönüştürüldü.")
    except Exception as e:
        raise RuntimeError(f"Dosya dönüştürme hatası: {str(e)}")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "Ses dosyası yüklenmedi"}), 400

    audio_file = request.files["audio"]
    language = request.form.get("language", "en")
    model_type = request.form.get("model", "base")

    try:
        model = get_or_load_model(model_type)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, audio_file.filename)
    audio_file.save(file_path)

    # Dosya uzantısını kontrol et ve gerekirse dönüştür
    wav_file_path = file_path if file_path.lower().endswith(".wav") else os.path.join(temp_dir, "temp_audio.wav")
    
    if not file_path.lower().endswith(".wav"):
        try:
            convert_to_wav(file_path, wav_file_path)
        except Exception as e:
            return jsonify({"error": f"Dosya dönüştürme hatası: {str(e)}"}), 500

    try:
        diarization = perform_speaker_diarization(wav_file_path)
        result = model.transcribe(wav_file_path, language=language)

        formatted_transcript = format_transcript_with_speakers(result['segments'], diarization)

        return jsonify({"transcript": formatted_transcript})
    except Exception as e:
        return jsonify({"error": f"Transkript başarısız: {str(e)}"}), 500
    finally:
        # Geçici dosyayı sil
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_file_path):
            os.remove(wav_file_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
