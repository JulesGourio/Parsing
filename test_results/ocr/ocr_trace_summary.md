# OCR Trace Summary

Source: `test_results/benchmark/benchmark_full_results.json`

## OCR-detected files (via parser_strategy)

- Total files in benchmark: 31
- Files with OCR trace markers: 0

Aucun marqueur OCR trouvé dans les parser_strategy de ce fichier de benchmark.

## Structured OCR fields now available

Depuis la mise à jour du parseur, les champs suivants sont exposés explicitement:
- `ocr_attempted`
- `ocr_used`
- `ocr_engine_trace`
- `ocr_pages`
- `ocr_supplement_pages`

Ces champs sont propagés dans le notebook et la table des fichiers traités.
