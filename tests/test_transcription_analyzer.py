from analyzers.transcription_analyzer import TranscriptionAnalyzer


def test_extract_species_caridina():
    ta = TranscriptionAnalyzer()
    text = "This video talks about Amano shrimp and caridina multidentata in a planted tank."
    species = ta.extract_species(text)
    assert "Caridina multidentata" in species
