# OCR Trace Examples

Ce rapport montre les champs OCR structurés directement renvoyés par le parseur.

## Synthetic image (png)
- Source: `/tmp/ocr_trace_demo.png`
- parser_strategy: `ocr_image:png|engines:rapidocr,tesseract|libs:pillow=12.2.0,rapidocr-onnxruntime=1.4.4,pytesseract=0.3.13|rapidocr|lines:4|avg_conf:0.99`
- parser_error: `None`
- ocr_attempted: `True`
- ocr_used: `True`
- ocr_pages: `1`
- ocr_supplement_pages: `1`
- ocr_engine_trace: `rapidocr|lines:4|avg_conf:0.99`

```text
INVOICE 2026-APR-20
ClientDEMO
Amount 1532 EUR
Ref OCR-TRACE-01
```

## Born-digital PDF
- Source: `benchmark_samples/attention_is_all_you_need.pdf`
- parser_strategy: `pdfplumber:pdf|table_text_excluded:1|libs:pdfplumber=0.11.5|ocr_pages:1|ocr_supplement_pages:1|ocr_trace:p14:rapidocr|lines:86|avg_conf:0.94`
- parser_error: `None`
- ocr_attempted: `True`
- ocr_used: `True`
- ocr_pages: `1`
- ocr_supplement_pages: `1`
- ocr_engine_trace: `p14:rapidocr|lines:86|avg_conf:0.94`

```text
## Page 1

Provided proper attribution is provided, Google hereby grants permission to
reproduce the tables and figures in this paper solely for use in journalistic or
scholarly works.
Attention Is All You Need
Ashish Vaswani∗ Noam Shazeer∗ Niki Parmar∗ Jakob Uszkoreit∗
Google Brain Google Brain Google Research Google Research
avaswani@google.com noam@google.com nikip@google.com usz@google.com
Llion Jones∗ Aidan N. Gomez∗ † Łukasz Kaiser∗
Google Research University of Toronto Google Brain
llion@google.com aidan@cs.toronto.edu lukaszkaiser@google.com
Illia Polosukhin∗ ‡
illia.polosukhin@gmail.com
Abstract
The dominant sequence transduction models are based on complex recurrent or
convolutiona...
```
