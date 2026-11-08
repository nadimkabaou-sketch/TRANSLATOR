---
name: scientific-paper-translator
description: >-
  Translates complex academic, scientific, and medical papers (PDF, DOCX, LaTeX) into French (or other languages)
  while strictly preserving 100% of the original document layout, multi-column geometry, typography, and ALL embedded
  high-resolution figures, schematics, and imaging (MRI, CT, ultrasound) in place without text truncation or empty paragraphs.
  Trigger when the user asks to translate a scientific paper, PDF, academic article, medical document, or provides a file path or folder to translate.
---

# Scientific Paper In-Place Translator & Document Rebuilder

Autonomous engine to translate peer-reviewed scientific papers and academic articles with publication-grade fidelity.

## RÈGLE FONDAMENTALE : TRADUCTION DIRECTE PAR L'AGENT IA

L'Agent IA (**Senior AI Scientific & Medical Translator**) effectue lui-même directement la traduction scientifique intégrale du document. 
Il ne délègue JAMAIS la traduction à des modèles NMT rudimentaires ou généralistes qui risquent d'altérer le sens ou de commettre des contresens terminologiques.

1. **Traduction par l'Agent IA** :
   - Traduit le contenu textuel intégral vers un français scientifique de niveau publication académique.
   - Respecte scrupuleusement la terminologie de la discipline (médecine, radiologie, biologie, physique, mathématiques).
   - Règle de non-altération absolue : ne pas résumer, ne pas reformuler librement, ne pas supprimer de sections.
   - Préservation à 100 % des chiffres, unités scientifiques, intervalles statistiques ($p < 0.05$, IC 95 %), équations mathématiques et citations bibliographiques `[1]`.

2. **Exact In-Place PDF Replica** :
   - Préserve 100 % de la géométrie originale des pages, en-têtes, pieds de page, colonnes et bordures.
   - Préserve **TOUTES les figures, schémas, graphiques et images médicales haute résolution** (IRM, TDM, échographie, histologie) à leur résolution native, sans aucune suppression ni altération.
   - Remplace le texte original in-situ au moyen d'une typographie vectorielle auto-ajustée (Arial Bold pour les titres, Arial Regular pour le corps, Arial Italic pour les légendes).
   - Garantit **zéro paragraphe vide** grâce au découplage strict des blocs titre et corps de texte.

3. **Enriched Word DOCX Rebuilder** :
   - Reconstruit un document `.docx` entièrement éditable intégrant toutes les figures haute résolution extraites, positionnées précisément en regard de leurs légendes.

4. **Multi-Format Publication Exports** :
   - Génère simultanément : `<stem>_FR_integral.pdf`, `<stem>_fr.docx`, `<stem>_fr.html`, `<stem>_fr.txt`, et `<stem>_fr.tex`.

---

## Antigravity Agent Execution Instructions

Quand l'utilisateur demande de traduire un article ou dossier :

### 1. Traduire Directement le Contenu
L'Agent IA traduit directement l'intégralité du texte en français académique, garantissant une fidélité scientifique absolue à 100 %.

### 2. Injecter et Exécuter le Reconstructeur Documentaire
Injecter les traductions validées dans la mémoire de traduction (`data/translation_memory/tm.json`) et exécuter la reconstruction :

```powershell
python translate.py "<path_to_file_or_folder>" --lang fr --domain medicine_radiology
```

### 3. Livrables Générés
Le moteur produit directement dans le dossier source :
* `<stem>_FR_integral.pdf` : Réplique visuelle vectorielle exacte in-situ avec toutes les images originales et le texte français traduit par l'IA.
* `<stem>_fr.docx` : Document Word modifiable intégrant toutes les figures haute résolution.
* `<stem>_fr.html` : Article Web autonome prêt à la publication.
* `<stem>_fr.txt` : Texte clair structuré.
* `<stem>_fr.tex` : Code source LaTeX académique standard.

### 4. Directives de Réponse
* Présenter des liens markdown cliquables vers `<stem>_FR_integral.pdf` et `<stem>_fr.docx`.
* Résumer les métriques clés de l'article (titre traduit, auteurs, revue, volume, DOI, nombre d'images).
* Fournir le tableau d'audit de contrôle qualité scientifique (conservation 100% chiffres, unités, références).
