import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("   SCIENTIFIC PAPER TRANSLATOR — Multilingual to Academic French")
    print("=" * 70)
    print("Moteur local NMT et Contrôle Qualité Scientifique Strict initialisés.")
    print("Accès Web disponible sur : http://127.0.0.1:8000")
    print("=" * 70)
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
