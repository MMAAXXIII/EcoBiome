# -*- coding: utf-8 -*-
from collector_core.logger import log
import re
import unicodedata

class TranscriptionAnalyzer:
    def __init__(self):
        log("[TranscriptionAnalyzer] Initialized.")

    def clean(self, text: str) -> str:
        log("[TranscriptionAnalyzer] Cleaning transcription...")

#         print("=== RAW TEXT ===")
#         print(text)

        cleaned = text

        # Nettoyage des séquences échappées et backslashes
        cleaned = cleaned.replace("\\\\n", " ")
        cleaned = cleaned.replace("\\\\", " ")
        cleaned = cleaned.replace("\\n", " ")
        cleaned = cleaned.replace("\\", " ")

        # Supprimer caractères invisibles
        cleaned = cleaned.replace("\u2028", " ")
        cleaned = cleaned.replace("\u2029", " ")
        cleaned = cleaned.replace("\u200B", " ")
        cleaned = cleaned.replace("\u200C", " ")
        cleaned = cleaned.replace("\u200D", " ")
        cleaned = cleaned.replace("\uFEFF", " ")

        # Normalisation Unicode et collapse des espaces
        cleaned = unicodedata.normalize("NFKC", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

#         print("=== CLEANED TEXT ===")
#         print(cleaned)

        return cleaned

    def extract_species(self, text: str):
        species = []
        t = text.lower()

        if "neocaridina" in t:
            species.append("Neocaridina davidi")
        if "betta" in t:
            species.append("Betta splendens")
        if "dendrobates" in t:
            species.append("Dendrobates sp.")
        if "monstera" in t:
            species.append("Monstera deliciosa")
        if "anubias" in t:
            species.append("Anubias sp.")
        if "nemo" in t or "poisson clown" in t or "clownfish" in t:
            species.append("Amphiprion ocellaris")

        # Détection Amano / Caridina
        if "caridina multidentata" in t or "amano shrimp" in t or "yamato shrimp" in t:
            species.append("Caridina multidentata")

        return species

    def extract_parameters(self, text: str):
        params = {}
        t = text.lower()

        if "ph" in t:
            if "6.8" in t:
                params["ph"] = 6.8
            if "7.0" in t:
                params["ph"] = 7.0

        if "température" in t or "temperature" in t:
            if "24" in t:
                params["temperature"] = 24
            if "25" in t:
                params["temperature"] = 25

        if "humidité" in t or "humidity" in t:
            if "80%" in t:
                params["humidity"] = 80

        return params

    def extract_events(self, text: str):
        events = []
        t = text.lower()

        if "naissance" in t or "birth" in t:
            events.append("birth")
        if "mort" in t or "death" in t:
            events.append("death")
        if "floraison" in t or "flowering" in t:
            events.append("flowering")
        if "reproduction" in t or "breeding" in t:
            events.append("breeding")

        if "attaque" in t or "attack" in t or "predation" in t or "crabe" in t:
            events.append("danger")
            events.append("predation")

        return events

    def extract_context(self, text: str):
        context = {}
        t = text.lower()

        if "aquarium" in t:
            context["biome"] = "aquarium"
        if "terrarium" in t:
            context["biome"] = "terrarium"
        if "paludarium" in t:
            context["biome"] = "paludarium"

        return context

    def analyze(self, text: str) -> dict:
        log("[TranscriptionAnalyzer] Analyzing transcription...")
        cleaned = self.clean(text)

        return {
            "species": self.extract_species(cleaned),
            "parameters": self.extract_parameters(cleaned),
            "events": self.extract_events(cleaned),
            "context": self.extract_context(cleaned),
            "raw_text": text,
            "cleaned_text": cleaned
        }
