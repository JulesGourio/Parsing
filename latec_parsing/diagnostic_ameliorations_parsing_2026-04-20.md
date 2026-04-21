# Diagnostic parsing latec_parsing - 2026-04-20

## Resume executif

Ce diagnostic confirme vos 4 douleurs principales sur la version actuelle:
- Tables OCR encore non structurees en tableau dans plusieurs cas.
- Risque de contenu OCR dedouble avec le texte natif (dedupe trop strict).
- Chunking encore trop court sur certains documents, avec perte potentielle de contexte.
- Diagrammes d architecture non modelises en structure (texte OCR seulement).

Le pipeline est deja robuste sur la couverture de formats, mais la qualite RAG reste penalisee sur la structuration du contenu OCR et sur la strategie de segmentation.

## Findings prioritaires (P0)

### P0-1: OCR table -> texte plat (pas de schema tabulaire reconstruit)

Preuves:
- [Parsing RapidOCR en lignes textuelles](parsing_core/extractors.py#L474)
- [Assemblage ordered_lines sans reconstruction de colonnes](parsing_core/extractors.py#L505)
- [Retour texte plat normalize](parsing_core/extractors.py#L507)
- [Appel OCR RapidOCR puis consommation texte direct](parsing_core/extractors.py#L540)
- [Aucune encapsulation TABLE_START/TABLE_END pour OCR image](parsing_core/extractors.py#L1037)
- [Sortie OCR embedded images en texte libre](parsing_core/extractors.py#L1040)
- [Exemple OCR PDF: colonnes item/qte/prix/total extraites mais non tabularisees](test_results/ocr/ocr_table_examples_results.json#L20)
- [Exemple OCR DOCX idem, contenu table en liste de lignes](test_results/ocr/ocr_table_examples_results.json#L44)

Impact:
- Les tables scannees sont lisibles humainement mais perdent la structure colonnes/lignes.
- Le retrieval semantique (RAG) degrade sur les requetes metier de type item, quantite, total.

Recommandation:
- Ajouter une reconstruction tabulaire OCR a partir des bounding boxes RapidOCR (clustering par lignes/colonnes, puis emission markdown TABLE_START/TABLE_END).
- Garder le texte libre seulement comme fallback si reconstruction incertaine.

### P0-2: Dedup OCR/natif insuffisant (match exact ligne a ligne)

Preuves:
- [Heuristique dedupe exacte ocr in native](parsing_core/extractors.py#L600)
- [Heuristique exacte native in ocr](parsing_core/extractors.py#L602)
- [Set de lignes exactes native_lines](parsing_core/extractors.py#L605)
- [Supplement OCR base sur egalite stricte de lignes](parsing_core/extractors.py#L607)

Impact:
- Variantes OCR mineures (espaces, ponctuation, segmentation) ne sont pas dedoublonnees.
- Perception de contenu repete dans la sortie finale.

Recommandation:
- Passer a une dedupe canonique (normalisation forte alphanumerique) + seuil de similarite.
- Ajouter une protection anti-duplication sur blocs OCR complets, pas seulement ligne a ligne.

### P0-3: Chunking encore trop court / trop fragmente sur certains flux

Preuves:
- [Ajout de marqueurs de page en tete du texte](parsing_core/extractors.py#L833)
- [Detection markdown tres simple par nombre d en-tetes](parsing_core/chunking.py#L31)
- [Regle header_count >= 2 active split markdown](parsing_core/chunking.py#L33)
- [Split markdown par headers H1/H2/H3](parsing_core/chunking.py#L115)
- [Filtre qui drop les chunks sous min_chunk_tokens](parsing_core/chunking.py#L157)
- [Config notebook min chunk a 80 tokens](notebook_databricks.py#L82)
- [Build chunk avec min/max imposes](notebook_databricks.py#L1100)

Impact:
- Documents courts ou pages OCR pauvres produisent des chunks de petite taille.
- Avec min_chunk_tokens, certaines pages peuvent etre supprimees au lieu d etre fusionnees.

Recommandation:
- Ne pas traiter les en-tetes techniques page/sheet/slide comme markdown semantique.
- Fusionner les petits chunks adjacents avant filtre min_tokens.
- Introduire un objectif de taille de chunk (target range) plutot qu un simple seuil de suppression.

### P0-4: Diagrammes non structures (OCR texte uniquement)

Preuves:
- [Pipeline PDF focalise texte + tables pdfplumber](parsing_core/extractors.py#L850)
- [Extraction texte PDF layout false/true](parsing_core/extractors.py#L861)
- [Extraction tables PDF native uniquement](parsing_core/extractors.py#L903)
- [AI fallback desactive globalement](notebook_databricks.py#L76)
- [Local fail route vers AI mais mode SKIPPED par config](notebook_databricks.py#L1022)

Impact:
- Les schemas d architecture (boites, fleches, graphes) ne sont pas reconstruits en relations.
- Le parser recupere du texte OCR mais pas la structure du diagramme.

Recommandation:
- Activer un fallback vision cible pour pages detectees comme diagrammes (faible texte + forte densite graphique).
- Emettre une representation structuree minimale: noeuds, labels, liens directionnels estimes.

## Findings importants (P1)

### P1-1: Colonnes Excel Unnamed recurrentes

Preuves:
- [Headers repris tels quels depuis dataframe.columns](parsing_core/extractors.py#L1154)
- [Preview benchmark montre Unnamed: 0 et variantes](test_results/benchmark/benchmark_full_results.json#L65)
- [Cas multi-index avec Unnamed multiplies](test_results/benchmark/benchmark_full_results.json#L275)

Impact:
- Bruit semantique dans les chunks table.
- Ambiguite sur la colonne d index et les vraies colonnes metier.

Recommandation:
- Normaliser les headers auto-generes Unnamed vers index ou colonnes explicites.
- Detecter automatiquement les lignes de faux headers et nettoyer les nan en tete.

### P1-2: Incoherence de reporting OCR entre rapports

Preuves:
- [Summary OCR annonce 0 fichiers avec trace OCR](test_results/ocr/ocr_trace_summary.md#L8)
- [Mais exemples OCR contiennent bien des traces ocr_pages et ocr_trace](test_results/ocr/ocr_table_examples_results.json#L12)

Impact:
- Diagnostic qualite OCR trompeur en exploitation.

Recommandation:
- Mettre a jour les scripts de reporting pour consommer les champs structures ocr_attempted, ocr_used, ocr_pages, ocr_engine_trace.

### P1-3: AI fallback utile mais desactive en production notebook

Preuves:
- [Flag global desactive](notebook_databricks.py#L76)
- [Branche AI existe mais est bypass](notebook_databricks.py#L844)

Impact:
- Aucun secours sur documents complexes (diagrammes, scans difficiles) quand local parsing est limite.

Recommandation:
- Activer fallback de maniere selective et budgetee (seulement parse_status ERROR ou score de confiance faible).

## Evolution architecture (P2)

### P2-1: Strategie parser orientee qualite

Objectif:
- Passer d une extraction brute a une extraction qualifiee par type de contenu.

Proposition:
- Etape 1: classify page as text, table, diagram, mixed.
- Etape 2: route vers extracteur specialise.
- Etape 3: fusionner en format intermediaire unique (blocs structures).

### P2-2: KPI qualite et regression continue

Ajouter des KPI obligatoires:
- Table structure recovery rate.
- OCR duplicate ratio.
- Chunk size distribution p10/p50/p90.
- Diagram relation capture rate.

Et un corpus de regression versionne:
- Tables image complexes.
- Diagrammes d architecture.
- PDF scans multi-pages.

## Plan d action concret

### Sprint 1 (impact immediat, faible risque)
- Reconstruction de tables OCR RapidOCR dans [parsing_core/extractors.py](parsing_core/extractors.py).
- Dedupe OCR/natif robuste dans [parsing_core/extractors.py](parsing_core/extractors.py).
- Ajustement du split markdown pour ignorer headers techniques dans [parsing_core/chunking.py](parsing_core/chunking.py).
- Fusion des petits chunks adjacents dans [parsing_core/chunking.py](parsing_core/chunking.py).

### Sprint 2 (qualite metier)
- Normalisation headers Excel dans [parsing_core/extractors.py](parsing_core/extractors.py).
- Reporting OCR coherent dans [test_results/ocr/ocr_trace_summary.md](test_results/ocr/ocr_trace_summary.md) via script dedie.
- Activation selective AI fallback dans [notebook_databricks.py](notebook_databricks.py).

### Sprint 3 (diagrammes)
- Detection des pages diagrammes.
- Extraction noeuds/liens minimaux (vision ou heuristique layout).
- Validation sur benchmark architecture reel.

## Criteres d acceptation proposes

- OCR table image: au moins 80 pourcent des exemples doivent sortir en bloc TABLE_START structure.
- Dedup OCR: moins de 2 pourcent de lignes dupliquees apres fusion native plus OCR.
- Chunking: p50 tokens dans la cible 300 a 800 sans perte de contenu critique.
- Diagrammes: presence d une structure exploitable (noeuds + relations) sur cas de test architecture.

## Note de gouvernance

Ce document est volontairement oriente qualite parsing et priorise ce qui impacte directement la qualite RAG. Il est compatible avec votre demande audit only: aucune modification de code n a ete appliquee.
