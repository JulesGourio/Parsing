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
MAX_PDF_PAGES = max(1, int(os.getenv("MAX_PDF_PAGES", "300")))
PDF_EXCLUDE_TABLE_TEXT = os.getenv("PDF_EXCLUDE_TABLE_TEXT", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
MAX_PPTX_SLIDES = max(1, int(os.getenv("MAX_PPTX_SLIDES", "400")))
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
