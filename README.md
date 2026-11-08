# 🧠 Scientific Paper In-Place Translator & Document Rebuilder

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-CPU%2FCUDA-EE4C2C.svg)](https://pytorch.org/)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-1.24%2B-brightgreen.svg)](https://pymupdf.readthedocs.io/)
[![Antigravity Skill](https://img.shields.io/badge/Antigravity-Ready_Skill-9cf.svg)](https://deepmind.google/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Moteur autonome de traduction scientifique in situ et reconstruction documentaire.**  
> Traduit les articles scientifiques et médicaux complexes (PDF, Word DOCX, LaTeX) vers le français (ou toute autre langue) en **conservant à 100% la mise en page d'origine, le double colonnage, les en-têtes et TOUTES les images/figures médicales haute résolution (IRM, TDM, schémas vectoriels)**, sans aucun paragraphe vide ni troncature de texte.

---

## ⚡ Pourquoi ce projet ?

Les outils de traduction standard (DeepL PDF, Google Traduction) dégradent souvent la mise en page scientifique : les figures sont écrasées ou supprimées, les formules mathématiques corrompues et les structures multi-colonnes mélangées.

Ce moteur résout l'ensemble de ces défis grâce à :
* 🖼️ **Conservation intégrale des images (*in situ*)** : les figures raster et vectorielles sont préservées à leur emplacement et résolution natifs via masquage sélectif PyMuPDF (`PDF_REDACT_IMAGE_NONE`).
* 🧩 **Découplage En-tête / Corps de texte** : aucun paragraphe vide résiduel grâce à la détection et la scission systématique des blocs composites.
* 🛡️ **Protection des entités scientifiques** : préservation stricte des paramètres d'acquisition (T1, T2, 3D CISS/SSFP, b=1000, TOF, DWI), des unités de mesure (mm, ms, T, HU), des intervalles statistiques (p < 0.05, IC 95%) et des références bibliographiques.
* 📚 **Glossaires médicaux & neuroradiologiques spécialisés** : substitution rigoureuse de la terminologie anatomique française (*lame criblée, méat acoustique interne, canal facial, foramen rond/ovale/jugulaire, rehaussement, dissémination périneurale*).
* 📝 **Export Word DOCX enrichi** : réinsère automatiquement toutes les figures haute résolution extraites du PDF au-dessus de leurs légendes respectives.

---

## 🚀 Installation rapide

### 1. Cloner le dépôt
```bash
git clone https://github.com/nadimkabaou-sketch/scientific-paper-translator.git
cd scientific-paper-translator
```

### 2. Installer les dépendances
* **Sous Windows** : double-cliquez simplement sur `install.bat`
* **Sous Linux / macOS** : exécutez `bash install.sh`
* **Ou manuellement via pip** :
```bash
pip install -r requirements.txt
```

---

## 🤖 Utilisation dans Antigravity (Intégration Skill 100% Automatique)

Ce projet est nativement conçu comme un **Skill Antigravity**. Tout autre utilisateur d'Antigravity peut l'ajouter à son agent en un clic.

### Méthode 1 : Installation globale dans Antigravity (Recommandée)
L'utilisateur clone simplement ce dépôt dans son dossier de skills Antigravity :

```powershell
git clone https://github.com/nadimkabaou-sketch/scientific-paper-translator.git "$HOME\.gemini\config\skills\scientific-paper-translator"
```

### Méthode 2 : Utilisation directe dans un Workspace
Si le dépôt est cloné dans un projet de travail, Antigravity détecte automatiquement le fichier `.agents/skills/scientific-paper-translator/SKILL.md`.

### Utilisation dans le chat Antigravity
Une fois installé, l'utilisateur n'a qu'à demander dans le chat :
> *"Traduis C:\Chemin\Vers\mon_article.pdf"*  
> ou  
> *"Traduis le dossier C:\Users\...\MonDossier"*

L'agent Antigravity exécutera alors le pipeline de manière totalement autonome et fournira les liens directs vers :
1. Le **PDF réplique exacte** avec toutes les images d'origine.
2. Le **Document Word .docx** avec toutes les figures médicales insérées.
3. Les versions **HTML**, **LaTeX** et **Texte**.

---

## 💻 Utilisation en Ligne de Commande (CLI)

Vous pouvez également lancer la traduction directement depuis votre terminal :

```bash
python translate.py "chemin/vers/mon_article.pdf"
```

### Options disponibles :
```text
usage: translate.py [-h] [-l LANG] [-d DOMAIN] [-o OUTPUT_DIR] [-t THREADS] input

Arguments positionnels :
  input                 Chemin du fichier PDF ou du dossier contenant l'article

Options :
  -l, --lang LANG       Langue cible (par défaut : fr)
  -d, --domain DOMAIN   Glossaire de domaine (par défaut : medicine_radiology)
  -o, --output-dir DIR  Dossier de destination (par défaut : dossier source)
  -t, --threads INT     Nombre de threads CPU PyTorch (par défaut : 8)
```

**Exemple :**
```bash
python translate.py "C:\Users\Kabaou\Downloads\Nouveau dossier (7)" --lang fr --domain medicine_radiology
```

---

## 📁 Livrables générés

Pour un document d'entrée `article.pdf`, le système génère automatiquement :

| Fichier | Description |
| :--- | :--- |
| **`article_FR_integral.pdf`** | **Réplique exacte** : 100% des images/figures d'origine, même mise en page, texte en français. |
| **`article_fr.docx`** | **Document Word complet** : texte éditable + toutes les figures haute résolution insérées. |
| **`article_fr.html`** | Article Web autonome propre avec tables et balises sémantiques. |
| **`article_fr.txt`** | Texte structuré nettoyé pour indexation, RAG ou réutilisation. |
| **`article_fr.tex`** | Code source LaTeX académique standard (`babel[french]`). |

---

## 🏗️ Architecture du Projet

```text
scientific-paper-translator/
├── SKILL.md                          # Définition du Skill racine pour Antigravity
├── .agents/skills/
│   └── scientific-paper-translator/  # Skill workspace Antigravity
│       └── SKILL.md
├── translate.py                      # Point d'entrée CLI universel
├── requirements.txt                  # Dépendances Python
├── install.bat                       # Installateur 1-clic Windows
├── install.sh                        # Installateur 1-clic Linux/macOS
├── README.md                         # Documentation complète
├── .gitignore                        # Exclusion des fichiers temporaires & caches
│
├── backend/
│   ├── config.py                     # Configuration des répertoires et du moteur
│   └── core/
│       ├── extractor.py              # Extracteur multi-colonnes conscient du layout
│       ├── translator.py             # Moteur de traduction neuronale MarianMT
│       ├── entity_protector.py       # Protection des unités, formules et citations
│       ├── glossary.py               # Gestionnaire de glossaires et mémoire de traduction (TM)
│       ├── document_builder.py       # Constructeur multi-formats (PDF, Word, LaTeX)
│       └── quality_controller.py     # Contrôleur d'audit et fidélité scientifique
│
└── data/
    ├── glossaries/
    │   ├── medicine_radiology.json   # Terminologie neuroradiologique française de référence
    │   ├── physics_mathematics.json  # Physique & Mathématiques
    │   ├── biology_genetics.json     # Biologie & Génétique
    │   └── computer_science_ai.json  # Informatique & Intelligence Artificielle
    └── translation_memory/
        └── tm.json                   # Mémoire de traduction persistante
```

---

## 📤 Comment publier ce projet sur votre GitHub ?

Exécutez les commandes suivantes dans votre dossier de projet :

```bash
# 1. Initialiser git
git init
git add .
git commit -m "feat: Initial commit of Scientific Paper Translator Antigravity Skill"

# 2. Créer un dépôt sur github.com (ex: scientific-paper-translator)
# 3. Lier et pousser vers GitHub
git branch -M main
git remote add origin https://github.com/nadimkabaou-sketch/scientific-paper-translator.git
git push -u origin main
```

---

## 📄 Licence
Ce projet est distribué sous licence MIT. Libre d'utilisation pour la recherche médicale, l'enseignement et les projets personnels.
