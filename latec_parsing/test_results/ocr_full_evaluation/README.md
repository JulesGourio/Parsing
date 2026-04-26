# OCR Full Evaluation Outputs

Generated artifacts:

- full_report.html: browser view with full text/chunks for OCR ON and OCR OFF
- full_report.md: markdown integral dump
- full_results.json: complete structured payload (per-file full text + full chunks)
- chunks_ocr_on.jsonl: flat chunk dataset for OCR ON
- chunks_ocr_off.jsonl: flat chunk dataset for OCR OFF
- documents_ocr_on/: one full text file per source document
- documents_ocr_off/: one full text file per source document

Suggested default for downstream processing: full_results.json + chunks_ocr_on.jsonl/chunks_ocr_off.jsonl.