# Refonte latec_parsing inspiree de ssalto_llm_code (2026-04-20)

## Objectif
Passer d'un parsing principalement lineaire a un parsing plus structurel et plus robuste pour RAG:
- mieux reconstruire les tableaux OCR,
- reduire les doublons OCR vs texte natif,
- limiter les pertes de chunks courts,
- capter davantage de tableaux PDF sans quadrillage parfait,
- assainir la semantique des extractions Excel.

Cette refonte s'inspire des principes d'architecture observes dans ssalto_llm_code (table_finder, post-processing, split/chunk enrichi), sans copie integrale de code.

## Mapping des principes (ssalto -> latec_parsing)
- table_finder geometrique -> reconstruction layout-aware des blocs OCR RapidOCR.
- extraction multi-strategies des tableaux -> fallback `lines/lines` -> `lines/text` -> `text/text` dans le parseur PDF.
- post-processing de coherence -> fusion OCR/native fuzzy (normalisation + similarite) au lieu du dedupe strict ligne exacte.
- chunk post-processing -> merge de petits chunks adjacents avant filtrage min_tokens.
- traces d'observabilite -> enrichissement de `parser_strategy` avec compteurs layout OCR et fallback table detector.

## Modifications implementees (code)

### 1) OCR layout-aware et tableaux reconstruits
Fichier: `parsing_core/extractors.py`

Ajouts principaux:
- Parsing RapidOCR enrichi avec boites (x0, top, x1, bottom) en plus du texte.
- Reconstruction de tableau markdown a partir des boites OCR:
  - clustering en lignes (axe Y),
  - clustering de colonnes (axe X),
  - controle de densite de matrice,
  - emission `[TABLE_START]... [TABLE_END]`.
- Detection de page "diagramme" OCR (fallback) avec resume de labels `[DIAGRAM_START]... [DIAGRAM_END]`.
- OCR renvoie des metadonnees layout (`table_added`, `diagram_added`, `box_count`).

Nouvelles variables d'environnement:
- `OCR_TABLE_RECONSTRUCTION_ENABLED`
- `OCR_TABLE_MIN_BOXES`
- `OCR_TABLE_MIN_COLUMNS`
- `OCR_TABLE_MIN_DENSITY`
- `OCR_DIAGRAM_SUMMARY_ENABLED`
- `OCR_DIAGRAM_MIN_BOXES`

### 2) Dedup OCR/native plus intelligent
Fichier: `parsing_core/extractors.py`

Evolution:
- Normalisation canonique (lowercase, suppression accents, filtrage alpha-num).
- Similarite texte globale et ligne-a-ligne (SequenceMatcher) pour eviter les faux supplements.
- Conservation des vraies lignes OCR nouvelles seulement.

Nouvelles variables d'environnement:
- `OCR_SUPPLEMENT_LINE_SIMILARITY`
- `OCR_SUPPLEMENT_TEXT_SIMILARITY`

### 3) Detection des tableaux PDF plus robuste
Fichier: `parsing_core/extractors.py`

Evolution:
- Nouveau pipeline `_extract_pdf_tables_with_fallback`:
  - tentative 1: `lines/lines`
  - tentative 2: `lines/text`
  - tentative 3: `text/text`
- Dedup des tableaux extraits par signature de contenu.
- Exposition de la metrique `table_detector_fallback_pages` dans `parser_strategy`.

### 4) Chunking renforce (moins de pertes)
Fichier: `parsing_core/chunking.py`

Evolution:
- Detection markdown corrigee:
  - ignore les pseudo-titres de provenance (`## Page`, `## Sheet`, `## Slide`) pour decider le mode markdown.
- Merge des petits chunks adjacents avant filtrage min_tokens.
- Preservation des chunks de tableau depassant `max_chunk_tokens` (au lieu de drop silencieux).
- Nouveau type de contenu `diagram`.

Nouvelles variables d'environnement:
- `CHUNK_MARKDOWN_MIN_HEADERS`
- `CHUNK_MARKDOWN_IGNORE_PAGE_MARKERS`
- `CHUNK_SHORT_MERGE_ENABLED`
- `CHUNK_SHORT_MERGE_TARGET_TOKENS`
- `CHUNK_SHORT_MERGE_MAX_EXPANSION`

### 5) Nettoyage semantique Excel
Fichier: `parsing_core/extractors.py`

Evolution:
- Nettoyage des en-tetes placeholders (`Unnamed:*`, vides, `nan`, `none`).
- Promotion conditionnelle de la premiere ligne en header quand les colonnes sont majoritairement placeholders.
- Unicite des headers (`_2`, `_3`, ...) pour eviter collisions.

## Validation rapide executee
Validation runtime locale sur echantillons reels:
- `test_results/ocr/assets/ocr_table_middle_pdf_demo.pdf`
  - OCR utilise, tableaux reconstruits layout-aware detectes.
  - Strategy contient `ocr_layout_tables:1`.
- `test_results/ocr/assets/ocr_table_middle_source.png`
  - Reconstruction table OCR active (`layout_table:1`).
- `benchmark_samples/pandas_test1.xlsb`
  - Headers nettoyes (`Column 1` au lieu de `Unnamed:*` quand necessaire).
- Test synthese chunking:
  - petits fragments fusionnes avant filtrage min_tokens.

## Effets attendus sur vos problemes initiaux
- OCR dedouble: reduit via dedupe fuzzy au lieu de comparaisons exactes.
- Tableaux OCR ignores: reduit via reconstruction geometrique OCR + fallback table detector PDF.
- Chunking trop agressif: reduit via merge pre-filtre et preservation des gros tableaux.
- Diagrammes architecture: meilleure captation minimale via resume layout OCR quand non-tabulaire.

## Backlog priorise (etape suivante)
P0:
- Ajouter un mode "structure_only" pour sorties JSON table/diagram et non seulement markdown.
- Ajouter des tests automatiques asserts sur corpus OCR (table present/absent, taux duplication).
- Ajouter score de confiance par tableau reconstruit (qualite clustering) dans metadonnees chunk.

P1:
- Introduire une couche de tracking de pipeline type "pdf_tracker" (etats, cache hash, raisons fallback).
- Ajouter extraction explicite des sections (TOC/headers) avant chunking pour PDFs longs.

P2:
- Ajouter enrichissement hierarchique des chunks (parent/enfant/suivant) pour indexation relationnelle.
- Ajouter mode d'export visible (HTML diagnostique auto) a chaque run benchmark.

## Fichiers modifies dans cette etape
- `parsing_core/constants.py`
- `parsing_core/extractors.py`
- `parsing_core/chunking.py`
- `refonte_ssalto_inspiration_2026-04-20.md`
