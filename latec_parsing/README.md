# Parsing OCR pour RAG

## Objectif
Ce dépôt fournit une brique de parsing multi-formats orientée RAG, avec:
- extraction locale de texte,
- chunking prêt pour indexation,
- support OCR hybride (images + fallback PDF),
- UDF Spark pour pipeline distribué.

Formats principaux:
- pdf, doc, docx, docm, xls, xlsx, xlsb, pptx,
- html, htm, xml, md, csv, json, tsv, rtf,
- images OCR: png, jpg, jpeg, tif, tiff, bmp, webp.

## Plateformes et distribution
- OS cible: Linux (x86_64).
- Version Python recommandée: 3.10+.
- Distribution recommandée: Ubuntu 22.04/24.04 (mais compatible Fedora/Arch avec paquets équivalents).

## Prérequis système (par distribution)

### Debian / Ubuntu
- Paquets de base:
  - python3
  - python3-venv
  - python3-pip
  - antiword
  - poppler-utils
  - tesseract-ocr
  - tesseract-ocr-fra
  - tesseract-ocr-eng

Commande:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip antiword poppler-utils tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
```

### Fedora
- Paquets de base:
  - python3
  - python3-pip
  - antiword
  - poppler-utils
  - tesseract
  - tesseract-langpack-fra
  - tesseract-langpack-eng

Commande:

```bash
sudo dnf install -y python3 python3-pip antiword poppler-utils tesseract tesseract-langpack-fra tesseract-langpack-eng
```

### Arch Linux
- Paquets de base:
  - python
  - python-pip
  - antiword
  - poppler
  - tesseract
  - tesseract-data-fra
  - tesseract-data-eng

Commande:

```bash
sudo pacman -S --needed python python-pip antiword poppler tesseract tesseract-data-fra tesseract-data-eng
```

## Installation projet

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Droits et permissions nécessaires

### Droits système
- Lecture sur les fichiers à parser (sources documentaires).
- Écriture sur le workspace pour les artefacts (ex: dossier test_results).
- Écriture sur le répertoire temporaire système (généralement /tmp).
- Exécution des binaires externes si utilisés:
  - antiword
  - tesseract

### Droits recommandés dans un contexte équipe/serveur
- Droit de lecture sur les corpus partagés (NFS/S3 mount/etc.).
- Droit d’écriture sur un répertoire de résultats dédié.
- Droit d’installation de dépendances Python dans un virtualenv local.
- Si Spark/Databricks:
  - droit d’attacher un cluster,
  - droit d’utiliser les UDF Python,
  - droit d’accès aux volumes de données d’entrée/sortie.

## Configuration (variables d’environnement)

Variables clés OCR:
- OCR_ENABLED (défaut 1)
- OCR_PDF_FALLBACK_ENABLED (défaut 1)
- OCR_ENGINE_PRIORITY (défaut rapidocr,tesseract)
- OCR_PDF_RENDER_DPI (défaut 220)
- OCR_MIN_PDF_PAGE_TEXT_CHARS (défaut 80)
- OCR_MAX_PDF_OCR_ATTEMPTS (défaut 32)
- OCR_PDF_OCR_TIME_BUDGET_RATIO (défaut 0.72)
- OCR_MIN_CONFIDENCE (défaut 0.35)
- OCR_TIMEOUT_SECONDS (défaut 25)
- OCR_TESSERACT_LANG (défaut fra+eng)
- OCR_TESSERACT_BIN (défaut tesseract)

Variables parsing global:
- MAX_DOCUMENT_BYTES
- MAX_PDF_PAGES
- MAX_EXCEL_SHEETS
- MAX_EXCEL_ROWS_PER_SHEET
- MAX_CSV_ROWS
- MAX_CSV_TABLE_PREVIEW_ROWS
- PARSE_TIMEOUT_SECONDS
- ANTIWORD_BIN
- ANTIWORD_CPU_SECONDS
- ANTIWORD_MEMORY_MB

## Combinaison OCR + parsing (comment ça s’intègre)

L’OCR ne remplace pas le parsing existant, il le complète:
- Images (png/jpg/jpeg/tiff/bmp/webp): extraction OCR directe.
- PDF natifs: extraction texte standard d’abord, puis OCR sélectif uniquement sur les pages trop pauvres en texte.
- Fusion: le texte OCR est fusionné en supplément du texte natif quand utile, pour éviter de perdre l’info déjà bien extraite.
- Autres formats (docx/xlsx/pptx/csv/json/html…): inchangés, pipeline standard.

Concrètement, le flux reste unique (`extract_text_locally`), et la stratégie OCR est activée conditionnellement selon le type de fichier et les seuils configurés.

## Activation / désactivation OCR

### Désactiver tout OCR

```bash
export OCR_ENABLED=0
```

### Laisser OCR image mais désactiver fallback OCR sur PDF

```bash
export OCR_ENABLED=1
export OCR_PDF_FALLBACK_ENABLED=0
```

### Réactiver OCR complet

```bash
export OCR_ENABLED=1
export OCR_PDF_FALLBACK_ENABLED=1
```

Exemple:

```bash
export OCR_ENABLED=1
export OCR_PDF_FALLBACK_ENABLED=1
export OCR_ENGINE_PRIORITY=rapidocr,tesseract
export OCR_PDF_RENDER_DPI=220
export OCR_MIN_PDF_PAGE_TEXT_CHARS=80
export OCR_MAX_PDF_OCR_ATTEMPTS=32
export OCR_PDF_OCR_TIME_BUDGET_RATIO=0.72
export MAX_CSV_TABLE_PREVIEW_ROWS=80
export OCR_TESSERACT_LANG=fra+eng
```

## Usage local (Python)

```python
from parsing_core import extract_text_locally, split_text_to_chunks

with open("chemin/vers/document.pdf", "rb") as f:
    content = f.read()

parsed = extract_text_locally(content, "pdf")
text = parsed.get("text", "")

chunks = split_text_to_chunks(text, chunk_size_tokens=800, chunk_overlap_tokens=120)
print(parsed.get("parser_strategy"), len(chunks))
```

## Usage Spark (UDF)

Les UDF sont exposées dans le module parsing_core:
- extract_local_text_udf
- build_chunks_udf
- build_chunks_with_limits_udf
- token_count_udf

Import pratique:

```python
from parsing_core import extract_local_text_udf, build_chunks_udf, token_count_udf
```

## Notebook Databricks: alignement OCR

Oui, le notebook est aligné avec ce fonctionnement:
- il consomme `extract_local_text_udf`, donc le même parseur local (et les mêmes règles OCR),
- il expose/persiste les champs OCR structurés (`ocr_attempted`, `ocr_used`, `ocr_engine_trace`, `ocr_pages`, `ocr_supplement_pages`) dans `processed_files`,
- il pousse les flags OCR vers les exécuteurs via `spark.executorEnv.*` pour garantir la cohérence driver/executor.

Fichier concerné: [notebook_databricks.py](notebook_databricks.py)

## Dimensionnement VM recommandé

Le besoin dépend surtout du ratio de PDF scannés/images (OCR coûteux CPU).

| Profil | Usage | vCPU | RAM | Disque | Remarques |
|---|---|---:|---:|---:|---|
| Dev / POC | tests fonctionnels, petits lots | 4 | 16 Go | 100 Go SSD | suffisant pour validation rapide |
| Standard prod | lots moyens, mix natif + OCR | 8 | 32 Go | 200 Go SSD | profil recommandé par défaut |
| OCR intensif | beaucoup de scans/PDF image | 16 | 64 Go | 400+ Go SSD | réduit fortement le temps de traitement |

Notes:
- GPU non requis (RapidOCR fonctionne en CPU),
- privilégier SSD local pour les I/O temporaires,
- ajuster `MAX_*` (pages/lignes/taille doc) pour maîtriser latence et mémoire.

## Résultats de tests et organisation

Les résultats ont été réorganisés dans:
- [test_results/benchmark/benchmark_full_results.json](test_results/benchmark/benchmark_full_results.json)
- [test_results/benchmark/benchmark_chunks_all.jsonl](test_results/benchmark/benchmark_chunks_all.jsonl)
- [test_results/benchmark/benchmark_chunks_visible.md](test_results/benchmark/benchmark_chunks_visible.md)
- [test_results/benchmark/benchmark_chunks_visible.html](test_results/benchmark/benchmark_chunks_visible.html)
- [test_results/ocr/ocr_analysis_report.md](test_results/ocr/ocr_analysis_report.md)
- [test_results/ocr/ocr_previews_and_parsed_content.md](test_results/ocr/ocr_previews_and_parsed_content.md)
- [test_results/ocr/ocr_table_examples_report.md](test_results/ocr/ocr_table_examples_report.md)
- [test_results/ocr/ocr_table_examples_results.json](test_results/ocr/ocr_table_examples_results.json)
- [test_results/ocr/ocr_trace_summary.md](test_results/ocr/ocr_trace_summary.md)
- [test_results/ocr/ocr_trace_examples.md](test_results/ocr/ocr_trace_examples.md)
- [test_results/parsing_reports_index.md](test_results/parsing_reports_index.md)

Artefacts reproductibles:
- [scripts/generate_real_table_ocr_examples.py](scripts/generate_real_table_ocr_examples.py): génère un PDF multi-pages avec tableau image au milieu, un DOCX avec tableau image embarqué, puis un comparatif OCR ON/OFF.
- [scripts/run_folder_ocr_comparison.py](scripts/run_folder_ocr_comparison.py): lance un parsing OCR ON/OFF sur tout un dossier (multi-formats), puis génère un rapport consolidé JSON + Markdown + HTML centré sur la lisibilité et les diagnostics de tables.

## Campagne OCR ON/OFF sur un dossier

Exemple (corpus benchmark):

```bash
/home/n7student/Bureau/IA/Parsing/.venv/bin/python scripts/run_folder_ocr_comparison.py benchmark_samples --output-dir test_results/ocr_comparison --clean-output
```

Sorties générées:
- [test_results/ocr_comparison/comparison_report.html](test_results/ocr_comparison/comparison_report.html)
- [test_results/ocr_comparison/comparison_report.md](test_results/ocr_comparison/comparison_report.md)
- [test_results/ocr_comparison/comparison_results.json](test_results/ocr_comparison/comparison_results.json)

Ce rapport consolide met en avant:
- les erreurs et warnings prioritaires,
- la distinction parser vs dépendances/outillage (ex: antiword),
- les écarts OCR ON vs OCR OFF,
- les gains/pertes sur détection de tables,
- un statut explicite de contrôle table par fichier (pass/warn/fail/blocked),
- des extraits par fichier pour debug rapide.

Fichiers obsolètes retirés:
- benchmark_parsing_results.json
- benchmark_parsing_results.md

## Traçabilité OCR (visible explicitement)

La sortie parser expose maintenant des champs OCR dédiés (et pas uniquement parser_strategy):
- ocr_attempted (bool)
- ocr_used (bool)
- ocr_engine_trace (string)
- ocr_pages (int)
- ocr_supplement_pages (int)

Ces champs sont présents dans le schéma Spark de parsing et propagés dans la table des fichiers traités.

Exemple de lecture en Spark SQL:

```sql
SELECT
  source_file_name,
  parser_strategy,
  ocr_attempted,
  ocr_used,
  ocr_pages,
  ocr_supplement_pages,
  ocr_engine_trace
FROM dev_lab.lab_jules.processed_files
ORDER BY ocr_used DESC, source_file_name;
```

## Résumé qualité actuel
- Benchmark corpus complet: 31 fichiers, 31 succès, 0 erreur, 0 vide.
- OCR:
  - activé sélectivement sur pages/fichiers peu textuels,
  - gain net sur PDF scannés et images,
  - pas de régression sur le taux de succès global.

## Structure du dépôt (utile)
- [parsing_core/](parsing_core/): logique parsing/chunking/config/UDF.
- [utils.py](utils.py): façade de compatibilité.
- [notebook_databricks.py](notebook_databricks.py): intégration notebook.
- [benchmark_samples/](benchmark_samples/): corpus standard.
- [benchmark_samples_hard/](benchmark_samples_hard/): corpus difficile.
- [test_results/](test_results/): résultats consolidés.

## Dépannage rapide
- Erreur antiword:
  - vérifier antiword installé,
  - sinon définir ANTIWORD_BIN vers le binaire.
- OCR tesseract indisponible:
  - RapidOCR reste utilisable,
  - ou installer tesseract et packs langue.
- Import Spark manquant en local:
  - normal hors cluster,
  - utiliser les fonctions locales de parsing sans UDF.

## Bonnes pratiques d’exploitation
- Toujours utiliser un virtualenv isolé.
- Garder les limites de parsing (taille/pages/lignes) activées en production.
- Versionner les résultats de benchmark de référence dans test_results.
- Réexécuter benchmark après changement d’extracteur ou de paramètres OCR.
