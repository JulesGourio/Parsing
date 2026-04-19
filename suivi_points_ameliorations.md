# Suivi exhaustif des 133 points d audit

Source de reference: audit_parsing_rag_complet.md (section 3, points 1 a 133).
Base de progression: ancien monolithe old_utils.py compare a la base actuelle (parsing_core + notebook_databricks.py).

## Synthese

- Total points suivis: 133
- Corriges: 63
- Partiels: 34
- Non corriges: 36

## Tableau de suivi 1-133

| ID | Point d audit initial | Statut | Avancement | Preuve principale |
|---:|---|---|---|---|
| 1 | Packaging non reproductible: aucune specification de dependances (requirements/poetry/conda lock) dans ce repo. | Corrige | Implementation confirmee dans le code actuel. | requirements.txt |
| 2 | Import de utils.py casse si dependances absentes (deja reproduit localement). | Partiel | Mitigation partielle; reste a finaliser. | requirements.txt |
| 3 | Binaire antiword hardcode vers un chemin user Databricks specifique (line 63-65), non portable. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 4 | Extension htm non routee (line 69 vs line 231): faux negatif de parsing. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 5 | Aucune verification que le binaire antiword existe avant subprocess.run. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 6 | Aucune strategie de fallback si un parser principal echoue (ex: PDF -> autre parser). | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 7 | Propagation d erreurs par chaine str(e) seule, sans trace structurée. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 8 | Bare except presents (line 125, 209, 425), risques de masquer des bugs graves. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 9 | Incoherence possible extension entrante: si extension contient un point (.pdf), elle ne matchera pas les conditions. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 10 | Plusieurs formats declares comme supportes implicitement mais pas vraiment couverts de bout en bout (ex details ci-dessous). | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 11 | TXT: pas de detection d encodage robuste (heuristique fixe utf-8/cp1252/latin-1). | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 12 | TXT: safe_decode peut ignorer silencieusement des caracteres (errors=ignore). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 13 | HTML: parser html.parser de BS4 moins robuste/rapide que lxml selon la doc BS4. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 14 | HTML: suppression uniquement script/style, pas de logique semantique (main/article/nav). | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 15 | XML: traite comme textlike brut, pas de parsing XML structurel. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 16 | XML: tags/attributs non interpretes, donc perte de structure metier. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 17 | JSON: aucune serialisation semantique (cles/valeurs), simple texte decode puis normalize. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 18 | CSV/TSV: pd.read_csv sans parametres robustes (encoding, quote, escape, on_bad_lines, dtype). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 19 | CSV/TSV: default inference pandas peut changer les types et la valeur texte originale. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 20 | CSV/TSV: iteration via iterrows lente sur gros volumes. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 21 | CSV/TSV: si parse pandas echoue, fallback injecte CSV brut entre TABLE_START/TABLE_END, potentiellement massif. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 22 | CSV/TSV: aucune limite de taille de fichier ou de lignes. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 23 | PDF: pas d OCR fallback (doc pdfplumber: works best machine-generated; scanned PDFs limite forte). | Non corrige | A traiter dans une prochaine iteration. | - |
| 24 | PDF: page.extract_text(layout=True) est marque experimental dans la doc pdfplumber. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 25 | PDF: pas de parametrage laparams pour adapter aux layouts complexes. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 26 | PDF: pas de gestion des PDF proteges par mot de passe. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 27 | PDF: pas de dedupe chars (pdfplumber propose dedupe_chars). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 28 | PDF: pas de recadrage Page.crop avant extraction de tableaux, alors que la doc le recommande souvent. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 29 | PDF: extraction de tables avec settings par defaut uniquement (pas de tuning vertical/horizontal strategies). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 30 | PDF: pas d extraction de formulaires AcroForm. | Non corrige | A traiter dans une prochaine iteration. | - |
| 31 | PDF: pas d extraction de contenu image (pdfplumber ne reconstruit pas l image textuelle). | Non corrige | A traiter dans une prochaine iteration. | - |
| 32 | PDF: absence de metadata de provenance (page number) dans le texte final. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 33 | DOCX: extraction limitee au body iterchildren paragraphes/tables. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 34 | DOCX: headers/footers non extraits (doc python-docx montre leur modele specifique). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 35 | DOCX: comments non extraits (doc python-docx comments). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 36 | DOCX: footnotes/endnotes non traites. | Non corrige | A traiter dans une prochaine iteration. | - |
| 37 | DOCX: zones de texte/shapes/images non converties en texte. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 38 | DOCX: detection headings limitee a Heading 1/2/3 uniquement. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 39 | DOCX: headings 4+ ignores comme structure. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 40 | DOCX: style detection basee sur style_name texte, fragile si styles custom. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 41 | DOCX: listes numerotees/bullets non preservees explicitement (perte de structure de liste). | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 42 | DOCX: fusion de cellules tableau non preservee semantiquement. | Non corrige | A traiter dans une prochaine iteration. | - |
| 43 | DOCX: hyperliens non restitues explicitement (URL perdue probable). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 44 | DOC legacy (.doc): antiword supporte surtout Word 2/6/7/97/2000/2003 (manpage), limites structurelles. | Non corrige | A traiter dans une prochaine iteration. | - |
| 45 | DOC legacy: antiword connu pour couverture images incomplete/positions incorrectes (manpage BUGS). | Non corrige | A traiter dans une prochaine iteration. | - |
| 46 | DOC legacy: dependance mapping files et ANTIWORDHOME, fragile multi-noeuds. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 47 | Excel: pd.read_excel(sheet_name=None) charge toutes feuilles en memoire. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 48 | Excel: aucune limite de lignes/feuilles (risque OOM). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 49 | Excel: pas de parametrage engine explicite (variations selon extensions/versions). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 50 | Excel: formule, format, commentaires, hidden rows/cols non representes semantiquement. | Non corrige | A traiter dans une prochaine iteration. | - |
| 51 | Excel: flatten en phrases "col: value" peut detruire la relation tabulaire. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 52 | Excel: iterrows lent et couteux. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 53 | PPTX: extraction limitee a shape.text si present. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 54 | PPTX: pas de parsing explicite tables/charts/data labels. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/extractors.py |
| 55 | PPTX: pas d extraction des speaker notes. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 56 | PPTX: pas d extraction de texte depuis group shapes recurse. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 57 | PPTX: ordre de lecture potentiellement faux (ordre des shapes != ordre visuel humain). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 58 | PPTX: pas de metadata slide-level detaillee (layout, titre detecte, etc.). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/extractors.py |
| 59 | MarkdownHeaderTextSplitter applique sur texte non markdown natif (PDF/Docx/Excel flatten), risque splits artificiels. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 60 | Les marqueurs #/##/### dans contenu naturel peuvent creer fausses sections. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/chunking.py |
| 61 | custom_separators: priorite commence par \n\n, ce qui peut casser une table avant marqueurs TABLE_START/TABLE_END. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 62 | Pas de protection explicite "ne jamais splitter entre TABLE_START et TABLE_END". | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 63 | Overlap non valide (valeurs negatives/absurdes non bloquees). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 64 | chunk_size_tokens non valide (0/negatif/non sens) non bloque. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 65 | count_tokens fallback len(text)//4 tres approximatif, metriques tokens non fiables en cas d echec tiktoken. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/chunking.py |
| 66 | get_tiktoken_encoder cree encodeur a chaque appel, overhead important. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 67 | Re-injection headers: concat simple " > ", pas de schema metadata stable/versionne. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 68 | Dedupe chunks ne supprime que doublons consecutifs exacts. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 69 | Aucune normalisation dedupe globale (hash) pour pages repetees. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 70 | chunk_content_type detecte seulement par presence TABLE_START, trop binaire. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 71 | Pas de metadata provenance chunk (page, feuille, slide, path intra-doc). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 72 | Pas de chunk id stable cross-run (seulement index incremental run-local). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 73 | Pas de controle de longueur max caractere chunk vis-a-vis model context. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 74 | Pas de traitement specifique langues sans separateur espace (CJK/Thai) contrairement recos LangChain. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/chunking.py |
| 75 | pandas_udf execute du parsing lourd Python sur workers (PDF/docx/pptx), cout CPU eleve. | Non corrige | A traiter dans une prochaine iteration. | - |
| 76 | Aucun cache inter-batch pour objets couteux (tokenizer notamment). | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 77 | subprocess antiword lance potentiellement pour chaque ligne doc -> overhead process massif. | Non corrige | A traiter dans une prochaine iteration. | - |
| 78 | UDF scalaire renvoie structures potentiellement tres grosses (array of struct), pression Arrow/JVM. | Non corrige | A traiter dans une prochaine iteration. | - |
| 79 | Pas de controle spark.sql.execution.arrow.maxRecordsPerBatch dans le code. | Non corrige | A traiter dans une prochaine iteration. | - |
| 80 | Databricks indique que partitions converties en batches Arrow peuvent provoquer pics memoire. | Non corrige | A traiter dans une prochaine iteration. | - |
| 81 | Pas de mecanisme back-pressure ou circuit breaker taille document. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 82 | Pas de repartitionnement adapte selon type/poids document. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 83 | Le cast str(ext) dans UDF transforme None en "None" (diagnostic moins propre). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 84 | Pas de timeout parsing par document. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 85 | Pas de retry gradue sur erreurs transitoires. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 86 | parser_error conserve message brut, pas de code erreur standardise pour analytics. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 87 | parse_time_seconds arrondi a 2 decimales, perte precision pour tuning perf. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 88 | Aucun garde-fou taille fichier/page/feuille/slide (attaque DoS memoire/temps). | Corrige | Implementation confirmee dans le code actuel. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 89 | Aucun controle MIME reel vs extension declaree. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 90 | Parsing de contenus non fiables sans sandbox ni limite ressources. | Non corrige | A traiter dans une prochaine iteration. | - |
| 91 | subprocess antiword sans limite CPU/memoire/temps explicite. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 92 | Ecriture temporaire en /tmp pour .doc; suppression best-effort seulement. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 93 | En cas d echec suppression, fuite potentielle de donnees sensibles en local. | Partiel | Mitigation partielle; reste a finaliser. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 94 | parser_error peut exposer chemins internes, details infra ou infos sensibles. | Corrige | Implementation confirmee dans le code actuel. | parsing_core/udfs.py; parsing_core/extractors.py; notebook_databricks.py |
| 95 | Aucun scan anti-bombes (zip bombs, fichiers structures pathologiques). | Non corrige | A traiter dans une prochaine iteration. | - |
| 96 | Pas de strategie de quarantining des fichiers malformes repetitifs. | Non corrige | A traiter dans une prochaine iteration. | - |
| 97 | Absence de logs structures par etape parser. | Non corrige | A traiter dans une prochaine iteration. | - |
| 98 | Absence de compteurs qualite extraction (pages lues, pages vides, tableaux detectes, etc.). | Non corrige | A traiter dans une prochaine iteration. | - |
| 99 | Absence de taux d echec par extension et par parser. | Partiel | Mitigation partielle; reste a finaliser. | notebook_databricks.py; parsing_core/extractors.py |
| 100 | Absence de traces de version librairies dans parser_strategy. | Corrige | Implementation confirmee dans le code actuel. | notebook_databricks.py; parsing_core/extractors.py |
| 101 | parser_strategy trop peu granulaire pour root-cause fiable. | Corrige | Implementation confirmee dans le code actuel. | notebook_databricks.py; parsing_core/extractors.py |
| 102 | Pas de score de confiance extraction/chunking. | Non corrige | A traiter dans une prochaine iteration. | - |
| 103 | Pas de telemetry sur temps par sous-etape (open, text, tables, normalize). | Non corrige | A traiter dans une prochaine iteration. | - |
| 104 | Pas de mode debug reproductible (seed, dump intermediaire). | Non corrige | A traiter dans une prochaine iteration. | - |
| 105 | Fichier monolithique (735 lignes) melange constantes, extraction, chunking, UDF. | Corrige | Implementation confirmee dans le code actuel. | utils.py; parsing_core/ |
| 106 | Imports inutilises (json/tempfile/zipfile/etree/F) augmentent bruit technique. | Corrige | Implementation confirmee dans le code actuel. | utils.py; parsing_core/ |
| 107 | Style one-liner frequent (if/for/try sur une ligne) reduit lisibilite et debuggabilite. | Corrige | Implementation confirmee dans le code actuel. | utils.py; parsing_core/ |
| 108 | Multiples broad except nuisent a la precision de gestion d erreur. | Partiel | Mitigation partielle; reste a finaliser. | utils.py; parsing_core/ |
| 109 | Peu de docstrings detaillees (contrats d entree/sortie incomplets). | Non corrige | A traiter dans une prochaine iteration. | - |
| 110 | Pas de tests unitaires ni integration versionnes dans le repo. | Non corrige | A traiter dans une prochaine iteration. | - |
| 111 | Hardcodes d infra Databricks user-specific dans le code source. | Partiel | Mitigation partielle; reste a finaliser. | utils.py; parsing_core/ |
| 112 | Pas de separation interface parser vs implementation parser. | Partiel | Mitigation partielle; reste a finaliser. | utils.py; parsing_core/ |
| 113 | Pas de registry/plugin pattern pour ajouter formats proprement. | Non corrige | A traiter dans une prochaine iteration. | - |
| 114 | Types statiques generiques (Dict[str, Any]) limitent l auto-validation. | Non corrige | A traiter dans une prochaine iteration. | - |
| 115 | Dependance chemins Linux/Databricks (/tmp, /Workspace/Users/...). | Partiel | Mitigation partielle; reste a finaliser. | notebook_databricks.py; parsing_core/chunking.py; parsing_core/extractors.py |
| 116 | Aucun support explicite Windows/macOS pour chemin antiword. | Partiel | Mitigation partielle; reste a finaliser. | notebook_databricks.py; parsing_core/chunking.py; parsing_core/extractors.py |
| 117 | Ext supportes localement limites: txt/pdf/doc/docx/docm/xls/xlsx/pptx/html/xml/md/csv/json/tsv. | Partiel | Mitigation partielle; reste a finaliser. | notebook_databricks.py; parsing_core/chunking.py; parsing_core/extractors.py |
| 118 | Pas de support natif rtf/odt/ods/odp/msg/eml/epub. | Partiel | Mitigation partielle; reste a finaliser. | notebook_databricks.py; parsing_core/chunking.py; parsing_core/extractors.py |
| 119 | Pas de support archives (zip) malgre import zipfile. | Non corrige | A traiter dans une prochaine iteration. | - |
| 120 | Pas de normalisation unicode configurable (pdfplumber propose unicode_norm). | Non corrige | A traiter dans une prochaine iteration. | - |
| 121 | normalize_text peut alterer structure (espaces, multiples sauts de ligne) utile au sens. | Non corrige | A traiter dans une prochaine iteration. | - |
| 122 | Flatten tableaux en markdown ou paires col:value peut perdre unites, type et geometrie. | Non corrige | A traiter dans une prochaine iteration. | - |
| 123 | Perte des relations visuelles (colonnes PDF, merged cells, zones slides). | Non corrige | A traiter dans une prochaine iteration. | - |
| 124 | Partiellement mitige via le notebook (IDDOC, chunk_id, ref, titre, semantic_headers), mais provenance fine-grain page/sheet/slide reste incomplete. | Partiel | Mitigation partielle; reste a finaliser. | notebook_databricks.py; parsing_core/chunking.py; parsing_core/extractors.py |
| 125 | Partiellement mitige: url/url_preview sont conserves cote fichiers traites, mais non propagees dans la table chunks finale. | Corrige | Implementation confirmee dans le code actuel. | notebook_databricks.py; parsing_core/chunking.py; parsing_core/extractors.py |
| 126 | Partiellement mitige: contexte doc-level preserve; contexte section/page exact non garanti pour reevaluation humaine. | Partiel | Mitigation partielle; reste a finaliser. | notebook_databricks.py; parsing_core/chunking.py; parsing_core/extractors.py |
| 127 | Pas de distinction texte principal vs bruit (header/footer repetitive noise). | Non corrige | A traiter dans une prochaine iteration. | - |
| 128 | Aucun document de SLA parsing (taille max, latence cible, taux erreur tolere). | Non corrige | A traiter dans une prochaine iteration. | - |
| 129 | Aucun protocole de benchmark qualite extraction par format. | Non corrige | A traiter dans une prochaine iteration. | - |
| 130 | Aucun dataset de regression de parsing versionne. | Non corrige | A traiter dans une prochaine iteration. | - |
| 131 | Aucune politique de pinning/securite des versions parser libs. | Non corrige | A traiter dans une prochaine iteration. | - |
| 132 | Aucune definition de "done" pour robustesse multi-locale/multi-langue. | Non corrige | A traiter dans une prochaine iteration. | - |
| 133 | Aucune matrice officielle "extension -> parser -> limitations -> fallback". | Partiel | Mitigation partielle; reste a finaliser. | audit_parsing_rag_complet.md |
