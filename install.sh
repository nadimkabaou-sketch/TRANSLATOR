#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "   Scientific Paper In-Place Translator - Installation Script"
echo "======================================================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH! Please install Python 3.10+."
    exit 1
fi

echo "[1/3] Upgrading pip..."
python3 -m pip install --upgrade pip

echo ""
echo "[2/3] Installing scientific translation dependencies..."
python3 -m pip install -r requirements.txt

echo ""
echo "[3/3] Pre-caching neural translation model (Helsinki-NLP/opus-mt-en-fr)..."
python3 -c "from transformers import MarianMTModel, MarianTokenizer; m='Helsinki-NLP/opus-mt-en-fr'; MarianTokenizer.from_pretrained(m); MarianMTModel.from_pretrained(m); print('[OK] Neural Model ready for offline use!')"

echo ""
echo "======================================================================"
echo "   Installation Complete! You can now translate papers using:"
echo "   python3 translate.py \"path/to/article.pdf\""
echo "======================================================================"
