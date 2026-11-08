@echo off
echo ======================================================================
echo    Scientific Paper In-Place Translator - Installation Script
echo ======================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH! Please install Python 3.10+.
    pause
    exit /b 1
)

echo [1/3] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/3] Installing scientific translation dependencies...
python -m pip install -r requirements.txt

echo.
echo [3/3] Pre-caching neural translation model (Helsinki-NLP/opus-mt-en-fr)...
python -c "from transformers import MarianMTModel, MarianTokenizer; m='Helsinki-NLP/opus-mt-en-fr'; MarianTokenizer.from_pretrained(m); MarianMTModel.from_pretrained(m); print('[OK] Neural Model ready for offline use!')"

echo.
echo ======================================================================
echo    Installation Complete! You can now translate papers using:
echo    python translate.py "path\to\article.pdf"
echo ======================================================================
pause
