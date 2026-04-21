# Audit complet du parsing RAG (utils.py)

Date: 2026-04-19
Perimetre: revue du module unique utils.py (extraction multi-format + chunking + UDF Spark)
Objectif: lister de facon exhaustive les defauts potentiels (bloquants, qualite, performance, securite, maintenabilite, operabilite), avec constats locaux et references externes.

## 1) Methode d evaluation

1. Revue statique ligne par ligne du code.
2. Verification locale de l environnement Python.
3. Tests techniques automatiques (AST, import, compilation).
4. Recherche documentaire externe (pdfplumber, Spark pandas_udf, langchain splitters, pandas, antiword, python-docx, python-pptx, BeautifulSoup).

## 2) Constats verifies localement (preuves)

1. Import du module impossible dans l environnement local actuel:
- test: import utils
- resultat: ModuleNotFoundError: No module named pandas

2. Compilation syntaxique OK:
- test: python -m py_compile utils.py
- resultat: OK

3. Analyse statique AST:
- lignes totales: 735
- fonctions: 17
- imports: 26
- imports potentiellement inutilises: 5
- handlers except: 9
- except Exception: 6
- bare except: 3

4. Imports inutilises detectes:
- line 5: json
- line 9: tempfile
- line 13: zipfile
- line 33: etree (lxml)
- line 41: F (pyspark.sql.functions)

5. Trou de coverage extension detecte automatiquement:
- extract_text_from_textlike gere htm (line 231)
- mais htm absent de TEXTLIKE_EXTENSIONS (line 69)
- donc wrapper extract_text_locally ne route pas htm vers ce parser

6. Erreurs editeur (imports non resolus dans cet environnement):
- pandas, pdfplumber, docx, pptx, bs4, lxml, langchain_text_splitters, tiktoken

## 3) Liste exhaustive des defauts potentiels

### A. Defauts critiques / bloquants immediats

1. Packaging non reproductible: aucune specification de dependances (requirements/poetry/conda lock) dans ce repo.
2. Import de utils.py casse si dependances absentes (deja reproduit localement).
3. Binaire antiword hardcode vers un chemin user Databricks specifique (line 63-65), non portable.
4. Extension htm non routee (line 69 vs line 231): faux negatif de parsing.
5. Aucune verification que le binaire antiword existe avant subprocess.run.
6. Aucune strategie de fallback si un parser principal echoue (ex: PDF -> autre parser).
7. Propagation d erreurs par chaine str(e) seule, sans trace structurée.
8. Bare except presents (line 125, 209, 425), risques de masquer des bugs graves.
9. Incoherence possible extension entrante: si extension contient un point (.pdf), elle ne matchera pas les conditions.
10. Plusieurs formats declares comme supportes implicitement mais pas vraiment couverts de bout en bout (ex details ci-dessous).

### B. Defauts de couverture fonctionnelle par format

11. TXT: pas de detection d encodage robuste (heuristique fixe utf-8/cp1252/latin-1).
12. TXT: safe_decode peut ignorer silencieusement des caracteres (errors=ignore).
13. HTML: parser html.parser de BS4 moins robuste/rapide que lxml selon la doc BS4.
14. HTML: suppression uniquement script/style, pas de logique semantique (main/article/nav).
15. XML: traite comme textlike brut, pas de parsing XML structurel.
16. XML: tags/attributs non interpretes, donc perte de structure metier.
17. JSON: aucune serialisation semantique (cles/valeurs), simple texte decode puis normalize.
18. CSV/TSV: pd.read_csv sans parametres robustes (encoding, quote, escape, on_bad_lines, dtype).
19. CSV/TSV: default inference pandas peut changer les types et la valeur texte originale.
20. CSV/TSV: iteration via iterrows lente sur gros volumes.
21. CSV/TSV: si parse pandas echoue, fallback injecte CSV brut entre TABLE_START/TABLE_END, potentiellement massif.
22. CSV/TSV: aucune limite de taille de fichier ou de lignes.
23. PDF: pas d OCR fallback (doc pdfplumber: works best machine-generated; scanned PDFs limite forte).
24. PDF: page.extract_text(layout=True) est marque experimental dans la doc pdfplumber.
25. PDF: pas de parametrage laparams pour adapter aux layouts complexes.
26. PDF: pas de gestion des PDF proteges par mot de passe.
27. PDF: pas de dedupe chars (pdfplumber propose dedupe_chars).
28. PDF: pas de recadrage Page.crop avant extraction de tableaux, alors que la doc le recommande souvent.
29. PDF: extraction de tables avec settings par defaut uniquement (pas de tuning vertical/horizontal strategies).
30. PDF: pas d extraction de formulaires AcroForm.
31. PDF: pas d extraction de contenu image (pdfplumber ne reconstruit pas l image textuelle).
32. PDF: absence de metadata de provenance (page number) dans le texte final.
33. DOCX: extraction limitee au body iterchildren paragraphes/tables.
34. DOCX: headers/footers non extraits (doc python-docx montre leur modele specifique).
35. DOCX: comments non extraits (doc python-docx comments).
36. DOCX: footnotes/endnotes non traites.
37. DOCX: zones de texte/shapes/images non converties en texte.
38. DOCX: detection headings limitee a Heading 1/2/3 uniquement.
39. DOCX: headings 4+ ignores comme structure.
40. DOCX: style detection basee sur style_name texte, fragile si styles custom.
41. DOCX: listes numerotees/bullets non preservees explicitement (perte de structure de liste).
42. DOCX: fusion de cellules tableau non preservee semantiquement.
43. DOCX: hyperliens non restitues explicitement (URL perdue probable).
44. DOC legacy (.doc): antiword supporte surtout Word 2/6/7/97/2000/2003 (manpage), limites structurelles.
45. DOC legacy: antiword connu pour couverture images incomplete/positions incorrectes (manpage BUGS).
46. DOC legacy: dependance mapping files et ANTIWORDHOME, fragile multi-noeuds.
47. Excel: pd.read_excel(sheet_name=None) charge toutes feuilles en memoire.
48. Excel: aucune limite de lignes/feuilles (risque OOM).
49. Excel: pas de parametrage engine explicite (variations selon extensions/versions).
50. Excel: formule, format, commentaires, hidden rows/cols non representes semantiquement.
51. Excel: flatten en phrases "col: value" peut detruire la relation tabulaire.
52. Excel: iterrows lent et couteux.
53. PPTX: extraction limitee a shape.text si present.
54. PPTX: pas de parsing explicite tables/charts/data labels.
55. PPTX: pas d extraction des speaker notes.
56. PPTX: pas d extraction de texte depuis group shapes recurse.
57. PPTX: ordre de lecture potentiellement faux (ordre des shapes != ordre visuel humain).
58. PPTX: pas de metadata slide-level detaillee (layout, titre detecte, etc.).

### C. Defauts de qualite RAG (segmentation/chunks)

59. MarkdownHeaderTextSplitter applique sur texte non markdown natif (PDF/Docx/Excel flatten), risque splits artificiels.
60. Les marqueurs #/##/### dans contenu naturel peuvent creer fausses sections.
61. custom_separators: priorite commence par \n\n, ce qui peut casser une table avant marqueurs TABLE_START/TABLE_END.
62. Pas de protection explicite "ne jamais splitter entre TABLE_START et TABLE_END".
63. Overlap non valide (valeurs negatives/absurdes non bloquees).
64. chunk_size_tokens non valide (0/negatif/non sens) non bloque.
65. count_tokens fallback len(text)//4 tres approximatif, metriques tokens non fiables en cas d echec tiktoken.
66. get_tiktoken_encoder cree encodeur a chaque appel, overhead important.
67. Re-injection headers: concat simple " > ", pas de schema metadata stable/versionne.
68. Dedupe chunks ne supprime que doublons consecutifs exacts.
69. Aucune normalisation dedupe globale (hash) pour pages repetees.
70. chunk_content_type detecte seulement par presence TABLE_START, trop binaire.
71. Pas de metadata provenance chunk (page, feuille, slide, path intra-doc).
72. Pas de chunk id stable cross-run (seulement index incremental run-local).
73. Pas de controle de longueur max caractere chunk vis-a-vis model context.
74. Pas de traitement specifique langues sans separateur espace (CJK/Thai) contrairement recos LangChain.

### D. Defauts Spark / UDF / distribution

75. pandas_udf execute du parsing lourd Python sur workers (PDF/docx/pptx), cout CPU eleve.
76. Aucun cache inter-batch pour objets couteux (tokenizer notamment).
77. subprocess antiword lance potentiellement pour chaque ligne doc -> overhead process massif.
78. UDF scalaire renvoie structures potentiellement tres grosses (array of struct), pression Arrow/JVM.
79. Pas de controle spark.sql.execution.arrow.maxRecordsPerBatch dans le code.
80. Databricks indique que partitions converties en batches Arrow peuvent provoquer pics memoire.
81. Pas de mecanisme back-pressure ou circuit breaker taille document.
82. Pas de repartitionnement adapte selon type/poids document.
83. Le cast str(ext) dans UDF transforme None en "None" (diagnostic moins propre).
84. Pas de timeout parsing par document.
85. Pas de retry gradue sur erreurs transitoires.
86. parser_error conserve message brut, pas de code erreur standardise pour analytics.
87. parse_time_seconds arrondi a 2 decimales, perte precision pour tuning perf.

### E. Defauts securite / robustesse adversariale

88. Aucun garde-fou taille fichier/page/feuille/slide (attaque DoS memoire/temps).
89. Aucun controle MIME reel vs extension declaree.
90. Parsing de contenus non fiables sans sandbox ni limite ressources.
91. subprocess antiword sans limite CPU/memoire/temps explicite.
92. Ecriture temporaire en /tmp pour .doc; suppression best-effort seulement.
93. En cas d echec suppression, fuite potentielle de donnees sensibles en local.
94. parser_error peut exposer chemins internes, details infra ou infos sensibles.
95. Aucun scan anti-bombes (zip bombs, fichiers structures pathologiques).
96. Pas de strategie de quarantining des fichiers malformes repetitifs.

### F. Defauts observabilite / exploitation

97. Absence de logs structures par etape parser.
98. Absence de compteurs qualite extraction (pages lues, pages vides, tableaux detectes, etc.).
99. Absence de taux d echec par extension et par parser.
100. Absence de traces de version librairies dans parser_strategy.
101. parser_strategy trop peu granulaire pour root-cause fiable.
102. Pas de score de confiance extraction/chunking.
103. Pas de telemetry sur temps par sous-etape (open, text, tables, normalize).
104. Pas de mode debug reproductible (seed, dump intermediaire).

### G. Defauts maintenabilite / qualite code

105. Fichier monolithique (735 lignes) melange constantes, extraction, chunking, UDF.
106. Imports inutilises (json/tempfile/zipfile/etree/F) augmentent bruit technique.
107. Style one-liner frequent (if/for/try sur une ligne) reduit lisibilite et debuggabilite.
108. Multiples broad except nuisent a la precision de gestion d erreur.
109. Peu de docstrings detaillees (contrats d entree/sortie incomplets).
110. Pas de tests unitaires ni integration versionnes dans le repo.
111. Hardcodes d infra Databricks user-specific dans le code source.
112. Pas de separation interface parser vs implementation parser.
113. Pas de registry/plugin pattern pour ajouter formats proprement.
114. Types statiques generiques (Dict[str, Any]) limitent l auto-validation.

### H. Defauts de portabilite / compatibilite

115. Dependance chemins Linux/Databricks (/tmp, /Workspace/Users/...).
116. Aucun support explicite Windows/macOS pour chemin antiword.
117. Ext supportes localement limites: txt/pdf/doc/docx/docm/xls/xlsx/pptx/html/xml/md/csv/json/tsv.
118. Pas de support natif rtf/odt/ods/odp/msg/eml/epub.
119. Pas de support archives (zip) malgre import zipfile.
120. Pas de normalisation unicode configurable (pdfplumber propose unicode_norm).

### I. Defauts de fidelite informationnelle (impact reponse LLM)

121. normalize_text peut alterer structure (espaces, multiples sauts de ligne) utile au sens.
122. Flatten tableaux en markdown ou paires col:value peut perdre unites, type et geometrie.
123. Perte des relations visuelles (colonnes PDF, merged cells, zones slides).
124. Partiellement mitige via le notebook (IDDOC, chunk_id, ref, titre, semantic_headers), mais provenance fine-grain page/sheet/slide reste incomplete.
125. Partiellement mitige: url/url_preview sont conserves cote fichiers traites, mais non propagees dans la table chunks finale.
126. Partiellement mitige: contexte doc-level preserve; contexte section/page exact non garanti pour reevaluation humaine.
127. Pas de distinction texte principal vs bruit (header/footer repetitive noise).

### J. Defauts de gouvernance projet

128. Aucun document de SLA parsing (taille max, latence cible, taux erreur tolere).
129. Aucun protocole de benchmark qualite extraction par format.
130. Aucun dataset de regression de parsing versionne.
131. Aucune politique de pinning/securite des versions parser libs.
132. Aucune definition de "done" pour robustesse multi-locale/multi-langue.
133. Aucune matrice officielle "extension -> parser -> limitations -> fallback".

## 4) Risques externes confirms par documentation

1. pdfplumber:
- layout=True est experimental.
- pas d OCR natif, fonctionne mieux sur PDF machine-generated.
- extraction tables fortement dependante de settings.

2. Spark pandas_udf / Databricks:
- execution en batches Arrow, risque pics memoire.
- necessite adaptation maxRecordsPerBatch selon schema.
- contraintes de type retour, conversion potentiellement incorrecte en mismatch.

3. LangChain splitters:
- MarkdownHeaderTextSplitter retire les headers par defaut.
- overlap ne traverse pas les frontieres de sections.
- separateurs specifiques recommandes pour langues sans espaces.

4. antiword manpage:
- support legacy .doc limite.
- fonctionnalites manquantes, images parfois absentes/mal placees.

5. BeautifulSoup docs:
- parser choice impacte robustesse/performance.
- lxml recommande pour vitesse quand possible.

## 5) Priorisation (ordre de traitement recommande)

P0 (immediat):
1. Corriger la reproductibilite environnement (dependances lockees).
2. Retirer hardcode antiword et ajouter verification binaire.
3. Corriger trou extension htm.
4. Eliminer bare except et standardiser erreurs.
5. Ajouter garde-fous taille/timeout par document.

P1 (qualite extraction):
6. Ajouter metadata provenance (page/sheet/slide/chunk source).
7. Ajouter OCR fallback PDF scannes.
8. Etendre extraction DOCX (headers/footers/comments/shapes).
9. Etendre extraction PPTX (notes/tables/charts/group shapes).
10. Ajouter parametrage PDF table settings.

P2 (perf/ops):
11. Cacher tokenizer et reduire cout token_count.
12. Instrumenter metriques et logs structures.
13. Definir benchmarks qualite/perf et suite de regression.
14. Optimiser batchs Arrow et strategie Spark.

## 6) References internet utilisees

1. pdfplumber README/docs: https://github.com/jsvine/pdfplumber
2. pdfminer.six docs: https://pdfminersix.readthedocs.io/
3. Spark pandas_udf API: https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.functions.pandas_udf.html
4. Databricks pandas UDF docs: https://docs.databricks.com/aws/en/udf/pandas
5. pandas read_csv: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
6. pandas read_excel: https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html
7. LangChain markdown splitter: https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter
8. LangChain recursive splitter: https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter
9. python-docx styles: https://python-docx.readthedocs.io/en/latest/user/styles-understanding.html
10. python-docx headers/footers: https://python-docx.readthedocs.io/en/latest/user/hdrftr.html
11. python-docx comments: https://python-docx.readthedocs.io/en/latest/user/comments.html
12. python-pptx text/slides: https://python-pptx.readthedocs.io/en/latest/user/text.html and https://python-pptx.readthedocs.io/en/latest/user/slides.html
13. antiword manpage (Debian): https://manpages.debian.org/testing/antiword/antiword.1.en.html
14. BeautifulSoup docs: https://www.crummy.com/software/BeautifulSoup/bs4/doc/

## 7) Remarque importante

Cette liste est volontairement exhaustive et conservative (defauts potentiels), donc certains points peuvent ne pas se manifester sur votre corpus actuel. Mais chacun est realiste en production RAG multi-format a grande echelle.

## 8) Reevaluation avec notebook_databricks.py (orchestration Databricks)

Cette section corrige la lecture initiale "utils.py seul" en tenant compte du notebook Databricks fourni.

### 8.1 Points deja pris en charge par le notebook

1. Installation runtime des dependances via `%pip install` au debut du notebook.
2. Mode d execution explicite `AUDIT_ONLY` / `FULL` pour separer diagnostic et pipeline complet.
3. Audit unifie riche (MISSING_FILE, ORPHANED_FILE, EDGE_CASE, VALID_FILE, DEPRIORITIZED_FILE) avec `root_cause` et `recommended_action`.
4. Selection business-driven des documents (join metadonnees base + fichiers physiques) avec dedup `IDDOC` et ranking deterministic.
5. Parse local-first avec `extract_local_text_udf`, puis fallback AI conditionnel (`ENABLE_AI_FALLBACK`).
6. Gating de fallback AI par extension et par magic bytes (`detect_binary_format`) pour eviter des appels AI inutiles/incompatibles.
7. Statut de parsing explicite (`SUCCESS` / `ERROR` / `EMPTY_TEXT`) et persistance en table Delta.
8. Enrichissement chunk pour RAG (`[Source: ref | Title: titre]`) et export table chunks dediee.

### 8.2 Points de la revue initiale a reclasser (mitiges mais non resolus completement)

1. Reproductibilite environnement: partiellement mitigee par `%pip install`, mais versions non pinnees (pas de lock) donc reproductibilite toujours partielle.
2. Observabilite: beaucoup mieux cote audit metier, mais encore peu de metriques parser fines (par sous-etape d extraction).
3. Provenance RAG: amelioree doc-level (IDDOC/ref/titre), mais pas de propagation native de `url_preview` dans chunks.
4. Robustesse format: fallback AI existe, mais des formats restent uniquement en echec local si fallback desactive.

### 8.3 Nouveaux ecarts critiques identifies dans l integration notebook

1. Dependance manquante 1: `ID_CAT_DICT` est utilise dans le notebook mais non defini dans `utils.py` actuel.
2. Dependance manquante 2: `extract_text_from_ai_payload_udf` est utilise mais non defini dans `utils.py` actuel.
3. Politique de retry absente: aucun retry explicite autour des appels sensibles (`extract_local_text_udf` repartition large, `ai_parse_document`).
4. `ENABLE_AI_FALLBACK=False` par defaut: en cas d echec massif local, la resilence attendue n est pas activee.
5. Variables de parametrage non exploitees: `MIN_CHUNK_TOKENS` et `TABLE_CHUNK_MAX_TOKENS` ne pilotent pas la logique actuelle.
6. Nombreuses actions `count()` couteuses pour de gros volumes (acceptable en test, potentiellement cher en prod).

### 8.4 Priorisation revisee (tenant compte du notebook)

P0 (bloquants integration):
1. Definir `ID_CAT_DICT` dans le module partage ou injecter une table de mapping equivalente dans le notebook.
2. Definir `extract_text_from_ai_payload_udf` (ou remplacer par logique JSON equivalente inline).
3. Ajouter retries + backoff sur appels AI (`ai_parse_document`) et sur chemins de parsing fragiles.
4. Activer une strategie fallback pilotable (ex: activer AI fallback sur batchs en echec massif).

P1 (qualite extraction/RAG):
5. Propager `url_preview` et provenance fine-grain (page/sheet/slide) dans la table chunks.
6. Corriger le trou `htm` dans `utils.py` pour aligner wrapper et parser textlike.
7. Remplacer `except` trop larges par erreurs categoriees et codes exploitables.

P2 (perf/ops):
8. Introduire retries limites + timeout document-level.
9. Reduire les scans full (`count`) en mode prod et passer a des stats echantillonnees/aggregations cibles.
10. Cacher tokenizer/objets lourds et formaliser un benchmark perf-regression.

## 9) Trace d implementation de cette iteration

Le suivi detaille des points identifies, corriges/non corriges, et des fichiers modifies est maintenu dans `suivi_points_ameliorations.md`.
