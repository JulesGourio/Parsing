import json
import os
from typing import Dict, List

TOKENIZER_ENCODING = os.getenv("PARSING_TOKENIZER_ENCODING", "cl100k_base")

DEFAULT_DECODE_ENCODINGS = (
    "utf-8",
    "utf-8-sig",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
    "cp1252",
    "latin-1",
)

TEXTLIKE_EXTENSIONS = {"html", "htm", "xml", "md", "csv", "json", "tsv", "rtf"}

ANTIWORD_BIN = os.getenv("ANTIWORD_BIN", "antiword")
ANTIWORD_SHARE_DIR = os.getenv("ANTIWORD_SHARE_DIR", "")

LOCAL_PARSE_MAX_RETRIES = max(1, int(os.getenv("LOCAL_PARSE_MAX_RETRIES", "2")))
LOCAL_PARSE_RETRY_DELAY_SECONDS = max(0.0, float(os.getenv("LOCAL_PARSE_RETRY_DELAY_SECONDS", "0.2")))

MAX_DOCUMENT_BYTES = max(1024 * 1024, int(os.getenv("MAX_DOCUMENT_BYTES", str(60 * 1024 * 1024))))
MAX_EXCEL_SHEETS = max(1, int(os.getenv("MAX_EXCEL_SHEETS", "50")))
MAX_EXCEL_ROWS_PER_SHEET = max(1, int(os.getenv("MAX_EXCEL_ROWS_PER_SHEET", "15000")))
EXCEL_TABLE_PREVIEW_ROWS = max(1, int(os.getenv("EXCEL_TABLE_PREVIEW_ROWS", "40")))
EXCEL_INCLUDE_ROW_CONTEXT = os.getenv("EXCEL_INCLUDE_ROW_CONTEXT", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

MAX_CSV_ROWS = max(1, int(os.getenv("MAX_CSV_ROWS", "50000")))
MAX_CSV_TABLE_PREVIEW_ROWS = max(1, int(os.getenv("MAX_CSV_TABLE_PREVIEW_ROWS", "80")))
MAX_PDF_PAGES = max(1, int(os.getenv("MAX_PDF_PAGES", "300")))
PDF_EXCLUDE_TABLE_TEXT = os.getenv("PDF_EXCLUDE_TABLE_TEXT", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
MAX_PPTX_SLIDES = max(1, int(os.getenv("MAX_PPTX_SLIDES", "400")))

OCR_ENABLED = os.getenv("OCR_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OCR_PDF_FALLBACK_ENABLED = os.getenv("OCR_PDF_FALLBACK_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OCR_ENGINE_PRIORITY = tuple(
    [
        engine.strip().lower()
        for engine in os.getenv("OCR_ENGINE_PRIORITY", "rapidocr,tesseract").split(",")
        if engine.strip()
    ]
)
OCR_MIN_CONFIDENCE = min(1.0, max(0.0, float(os.getenv("OCR_MIN_CONFIDENCE", "0.35"))))
OCR_IMAGE_PREPROCESS = os.getenv("OCR_IMAGE_PREPROCESS", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OCR_MIN_IMAGE_SIDE_PX = max(240, int(os.getenv("OCR_MIN_IMAGE_SIDE_PX", "900")))
OCR_MAX_IMAGE_SIDE_PX = max(OCR_MIN_IMAGE_SIDE_PX, int(os.getenv("OCR_MAX_IMAGE_SIDE_PX", "2600")))
OCR_PDF_RENDER_DPI = max(72, int(os.getenv("OCR_PDF_RENDER_DPI", "220")))
OCR_MAX_PDF_PAGES = max(1, int(os.getenv("OCR_MAX_PDF_PAGES", "120")))
OCR_MIN_PDF_PAGE_TEXT_CHARS = max(0, int(os.getenv("OCR_MIN_PDF_PAGE_TEXT_CHARS", "80")))
OCR_MAX_PDF_OCR_ATTEMPTS = max(1, int(os.getenv("OCR_MAX_PDF_OCR_ATTEMPTS", "32")))
OCR_PDF_OCR_TIME_BUDGET_RATIO = min(
    0.95,
    max(0.10, float(os.getenv("OCR_PDF_OCR_TIME_BUDGET_RATIO", "0.72"))),
)
OCR_TIMEOUT_SECONDS = max(1.0, float(os.getenv("OCR_TIMEOUT_SECONDS", "25")))
OCR_TESSERACT_LANG = os.getenv("OCR_TESSERACT_LANG", "fra+eng")
OCR_TESSERACT_PSM = max(3, min(13, int(os.getenv("OCR_TESSERACT_PSM", "6"))))
OCR_TESSERACT_OEM = max(0, min(3, int(os.getenv("OCR_TESSERACT_OEM", "1"))))
OCR_TESSERACT_BIN = os.getenv("OCR_TESSERACT_BIN", "tesseract")
OCR_TABLE_RECONSTRUCTION_ENABLED = os.getenv("OCR_TABLE_RECONSTRUCTION_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OCR_TABLE_MIN_BOXES = max(4, int(os.getenv("OCR_TABLE_MIN_BOXES", "8")))
OCR_TABLE_MIN_COLUMNS = max(2, int(os.getenv("OCR_TABLE_MIN_COLUMNS", "2")))
OCR_TABLE_MIN_DENSITY = min(1.0, max(0.05, float(os.getenv("OCR_TABLE_MIN_DENSITY", "0.28"))))
OCR_DIAGRAM_SUMMARY_ENABLED = os.getenv("OCR_DIAGRAM_SUMMARY_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OCR_DIAGRAM_MIN_BOXES = max(4, int(os.getenv("OCR_DIAGRAM_MIN_BOXES", "9")))
OCR_SUPPLEMENT_LINE_SIMILARITY = min(
    1.0,
    max(0.5, float(os.getenv("OCR_SUPPLEMENT_LINE_SIMILARITY", "0.90"))),
)
OCR_SUPPLEMENT_TEXT_SIMILARITY = min(
    1.0,
    max(0.5, float(os.getenv("OCR_SUPPLEMENT_TEXT_SIMILARITY", "0.94"))),
)

CHUNK_MARKDOWN_MIN_HEADERS = max(1, int(os.getenv("CHUNK_MARKDOWN_MIN_HEADERS", "2")))
CHUNK_MARKDOWN_IGNORE_PAGE_MARKERS = os.getenv("CHUNK_MARKDOWN_IGNORE_PAGE_MARKERS", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CHUNK_SHORT_MERGE_ENABLED = os.getenv("CHUNK_SHORT_MERGE_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CHUNK_SHORT_MERGE_TARGET_TOKENS = max(0, int(os.getenv("CHUNK_SHORT_MERGE_TARGET_TOKENS", "90")))
CHUNK_SHORT_MERGE_MAX_EXPANSION = min(
    1.0,
    max(0.0, float(os.getenv("CHUNK_SHORT_MERGE_MAX_EXPANSION", "0.28"))),
)

MAX_FALLBACK_TEXT_CHARS = max(2000, int(os.getenv("MAX_FALLBACK_TEXT_CHARS", "40000")))
MAX_ERROR_MESSAGE_CHARS = max(120, int(os.getenv("MAX_ERROR_MESSAGE_CHARS", "1200")))
MAX_CHUNK_CHARS = max(200, int(os.getenv("MAX_CHUNK_CHARS", "12000")))

ANTIWORD_CPU_SECONDS = max(1, int(os.getenv("ANTIWORD_CPU_SECONDS", "60")))
ANTIWORD_MEMORY_MB = max(64, int(os.getenv("ANTIWORD_MEMORY_MB", "1024")))

PARSE_TIMEOUT_SECONDS = max(1.0, float(os.getenv("PARSE_TIMEOUT_SECONDS", "120")))

RETRYABLE_ERROR_MARKERS = (
    "timeout",
    "tempor",
    "connection",
    "network",
    "rate limit",
    "429",
    "503",
    "resource busy",
)


def _coerce_cat_value(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def _load_id_cat_dict_from_env() -> Dict[str, List[int]]:
    raw = os.getenv("ID_CAT_DICT_JSON", "").strip()
    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed, dict):
        return {}

    normalized: Dict[str, List[int]] = {}
    for prefix, categories in parsed.items():
        if not isinstance(categories, list):
            continue
        normalized[str(prefix)] = [_coerce_cat_value(cat) for cat in categories]
    return normalized


# Mapping expected by notebook_databricks.py: {"prefix": [IDCAT, ...]}
# Default is empty and handled by a notebook-side fallback strategy.
ID_CAT_DICT = _load_id_cat_dict_from_env()
