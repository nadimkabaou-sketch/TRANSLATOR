import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"
CACHE_DIR = DATA_DIR / "cache"
GLOSSARY_DIR = DATA_DIR / "glossaries"
TM_DIR = DATA_DIR / "translation_memory"
SAMPLES_DIR = BASE_DIR / "samples"

for directory in [UPLOAD_DIR, OUTPUT_DIR, CACHE_DIR, GLOSSARY_DIR, TM_DIR, SAMPLES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Default Translation Engine Settings
DEFAULT_SOURCE_LANG = "auto"
TARGET_LANG = "fr"
TRANSLATION_ENGINE = os.getenv("TRANSLATION_ENGINE", "hybrid")  # 'hybrid', 'marian', 'google_direct', 'deepl'
DEVICE = "cpu"  # or 'cuda' if GPU available

# QC Thresholds
QC_MAX_NUMBER_DISCREPANCY = 0
QC_MAX_UNTRANSLATED_THRESHOLD = 0.05
