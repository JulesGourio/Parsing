# Parsing Reports Index

Ce fichier centralise les rapports et artefacts produits par le pipeline de parsing/OCR.

## Rapports benchmark
- [benchmark_full_results.json](benchmark/benchmark_full_results.json)
- [benchmark_chunks_visible.md](benchmark/benchmark_chunks_visible.md)
- [benchmark_chunks_visible.html](benchmark/benchmark_chunks_visible.html)
- [benchmark_chunks_all.jsonl](benchmark/benchmark_chunks_all.jsonl)

## Rapports OCR
- [ocr_analysis_report.md](ocr/ocr_analysis_report.md)
- [ocr_previews_and_parsed_content.md](ocr/ocr_previews_and_parsed_content.md)
- [ocr_table_examples_report.md](ocr/ocr_table_examples_report.md)
- [ocr_table_examples_results.json](ocr/ocr_table_examples_results.json)
- [ocr_trace_summary.md](ocr/ocr_trace_summary.md)
- [ocr_trace_examples.md](ocr/ocr_trace_examples.md)

## Assets OCR (aperçus)
- [attention_is_all_you_need_preview.png](ocr/assets/attention_is_all_you_need_preview.png)
- [ocr_demo_invoice.png](ocr/assets/ocr_demo_invoice.png)
- [ocr_demo_scanned_invoice.pdf](ocr/assets/ocr_demo_scanned_invoice.pdf)
- [ocr_demo_scanned_invoice_preview.png](ocr/assets/ocr_demo_scanned_invoice_preview.png)
- [ocr_table_middle_source.png](ocr/assets/ocr_table_middle_source.png)
- [ocr_table_middle_pdf_demo.pdf](ocr/assets/ocr_table_middle_pdf_demo.pdf)
- [ocr_table_middle_pdf_page2_preview.png](ocr/assets/ocr_table_middle_pdf_page2_preview.png)
- [ocr_table_middle_docx_demo.docx](ocr/assets/ocr_table_middle_docx_demo.docx)

## Rapports techniques du dépôt
- [audit_parsing_rag_complet.md](../audit_parsing_rag_complet.md)
- [suivi_points_ameliorations.md](../suivi_points_ameliorations.md)

## Conseils d’utilisation
- Pour une lecture humaine rapide: commencer par [ocr_table_examples_report.md](ocr/ocr_table_examples_report.md), puis [ocr_previews_and_parsed_content.md](ocr/ocr_previews_and_parsed_content.md) et [benchmark_chunks_visible.md](benchmark/benchmark_chunks_visible.md).
- Pour analyse automatisée: utiliser `benchmark_full_results.json` et `benchmark_chunks_all.jsonl`.
