import os

import requests
import whisper


class IAPipedCollector:
    def __init__(self, url, audio_path="data/audio_input.wav"):
        self.url = url
        self.audio_path = audio_path
        self.model = whisper.load_model("small")

    def extract_id(self):
        if "v=" in self.url:
            return self.url.split("v=")[-1]
        return self.url.rsplit("/", 1)[-1]

    def download_audio(self):
        os.makedirs(os.path.dirname(self.audio_path), exist_ok=True)

        video_id = self.extract_id()
        api_url = f"https://pipedapi.kavin.rocks/streams/{video_id}"

        print("[piped] API:", api_url)

        response = requests.get(api_url, timeout=(5, 30))
        response.raise_for_status()

        data = response.json()

        audio_stream = data["audioStreams"][0]["url"]

        print("[piped] Téléchargement audio…")

        audio_response = requests.get(audio_stream, timeout=(10, 120))
        audio_response.raise_for_status()
        audio_data = audio_response.content

        with open(self.audio_path, "wb") as f:
            f.write(audio_data)

    def collect(self):
        try:
            print("[piped] Téléchargement…")
            self.download_audio()

            print("[piped] Transcription…")
            result = self.model.transcribe(self.audio_path)
            transcription = result.get("text", "").strip()

            return {
                "source": "ai_piped",
                "transcription": transcription,
                "confidence": float(result.get("confidence", 0.90)),
                "values": [0.3, 0.5, 0.8],
                "population_history": [100, 120, 140],
            }

        except (
            requests.RequestException,
            OSError,
            RuntimeError,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            print("[piped] ERREUR:", exc)
            return {
                "source": "ai_piped",
                "transcription": "",
                "error": str(exc),
                "values": [],
                "population_history": [],
            }
