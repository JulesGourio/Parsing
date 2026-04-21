# OCR Analysis Report (Parsing + RAG)

## Scope
- Added hybrid OCR pipeline in parser:
  - OCR on image files (png/jpg/jpeg/tiff/bmp/webp)
  - Conditional OCR fallback on PDF pages with low native text density
  - Engine priority: RapidOCR first, then Tesseract fallback

## Example-based validation

### Example 1: image OCR (synthetic invoice-like PNG)
- Input: /tmp/parsing_ocr_examples/ocr_invoice_like.png
- Strategy:
  - ocr_image:png|engines:rapidocr,tesseract|...|rapidocr|lines:5|avg_conf:0.99|attempts:1
- Output quality:
  - 113 chars extracted
  - Key fields recovered: invoice id, client, amount, due date, reference
- Runtime:
  - OCR enabled: 1.6603s
  - OCR disabled: 0.0031s (expected empty OCR output)

### Example 2: scanned-like PDF (image-only PDF)
- Input: /tmp/parsing_ocr_examples/scanned_invoice_like.pdf
- Strategy:
  - pdfplumber:pdf|...|ocr_pages:1|ocr_supplement_pages:1|ocr_trace:p1:rapidocr|lines:5|avg_conf:0.99|attempts:1
- Output quality:
  - OCR enabled: 118 chars
  - OCR disabled: 9 chars
  - OCR recovers useful business content where native parser has near-empty text
- Runtime:
  - OCR enabled: 1.7339s
  - OCR disabled: 0.0052s

### Example 3: born-digital PDF (Attention Is All You Need)
- Input: benchmark_samples/attention_is_all_you_need.pdf
- Strategy:
  - pdfplumber:pdf|...|ocr_pages:1|ocr_supplement_pages:1|ocr_trace:p14:rapidocr|lines:86|avg_conf:0.94|attempts:1
- Output quality:
  - OCR enabled: 46805 chars
  - OCR disabled: 46099 chars
  - OCR adds supplemental text on sparse page(s) only
- Runtime:
  - OCR enabled: 5.6830s
  - OCR disabled: 4.9860s

## Full corpus check
- Corpus: benchmark_samples + benchmark_samples_hard
- Result:
  - total files: 31
  - success: 31
  - error: 0
  - empty: 0
  - ocr_triggered_files: 8
  - ocr_positive_pages_files: 3

Interpretation:
- No regression in success rate (still 31/31)
- OCR activates selectively on low-text pages/files
- Best gain is on scanned/image-heavy inputs

## Operational tuning knobs (env vars)
- OCR_ENABLED=1
- OCR_PDF_FALLBACK_ENABLED=1
- OCR_ENGINE_PRIORITY=rapidocr,tesseract
- OCR_PDF_RENDER_DPI=220
- OCR_MIN_PDF_PAGE_TEXT_CHARS=80
- OCR_MIN_CONFIDENCE=0.35
- OCR_MAX_PDF_PAGES=120
- OCR_TIMEOUT_SECONDS=25
- OCR_IMAGE_PREPROCESS=1

## Notes
- Tesseract binary is optional; if unavailable, RapidOCR keeps OCR fully operational.
- Parser strategy now records OCR traces (pages, supplementary pages, engine trace) for auditability.
