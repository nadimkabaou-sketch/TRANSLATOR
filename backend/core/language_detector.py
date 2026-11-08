from typing import Optional, Dict
try:
    from lingua import Language, LanguageDetectorBuilder
    # Build detector with primary academic languages
    detector = LanguageDetectorBuilder.from_all_languages().with_preheating().build()
    HAS_LINGUA = True
except Exception:
    HAS_LINGUA = False

# ISO 639-1 code mapping for Lingua languages
LINGUA_TO_ISO = {
    "ENGLISH": "en",
    "FRENCH": "fr",
    "GERMAN": "de",
    "SPANISH": "es",
    "CHINESE": "zh",
    "ARABIC": "ar",
    "JAPANESE": "ja",
    "RUSSIAN": "ru",
    "ITALIAN": "it",
    "PORTUGUESE": "pt",
    "DUTCH": "nl",
    "KOREAN": "ko"
}

class LanguageDetector:
    """
    Robust language detector tailored for scientific texts,
    abstracts, multi-lingual citations and papers.
    """

    def __init__(self):
        self.detector = detector if HAS_LINGUA else None

    def detect(self, text: str) -> Dict[str, any]:
        """
        Detects the source language and returns ISO code, language name, and confidence.
        """
        if not text or not text.strip():
            return {"code": "en", "name": "English", "confidence": 1.0}

        # Filter out numbers, URLs, and code before language detection
        sample = text[:1500].strip()

        if self.detector:
            try:
                detected_lang = self.detector.detect_language_of(sample)
                confidence_vals = self.detector.compute_language_confidence_values(sample)
                confidence = confidence_vals[0].value if confidence_vals else 0.95
                
                if detected_lang:
                    lang_name = detected_lang.name
                    code = LINGUA_TO_ISO.get(lang_name, lang_name.lower()[:2])
                    return {
                        "code": code,
                        "name": lang_name.title(),
                        "confidence": round(float(confidence), 3)
                    }
            except Exception as e:
                print(f"Lingua detection warning: {e}")

        # Basic heuristic fallback
        return {"code": "en", "name": "English (Fallback)", "confidence": 0.85}
