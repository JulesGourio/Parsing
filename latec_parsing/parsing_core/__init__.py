from .chunking import split_text_to_chunks
from .constants import (
    ANTIWORD_BIN,
    ANTIWORD_CPU_SECONDS,
    ANTIWORD_MEMORY_MB,
    ANTIWORD_SHARE_DIR,
    ID_CAT_DICT,
    LOCAL_PARSE_MAX_RETRIES,
    LOCAL_PARSE_RETRY_DELAY_SECONDS,
    MAX_CHUNK_CHARS,
    MAX_CSV_ROWS,
    MAX_DOCUMENT_BYTES,
    MAX_EXCEL_ROWS_PER_SHEET,
    MAX_EXCEL_SHEETS,
    MAX_PDF_PAGES,
    MAX_PPTX_SLIDES,
    PARSE_TIMEOUT_SECONDS,
    TEXTLIKE_EXTENSIONS,
    TOKENIZER_ENCODING,
)
from .extractors import (
    extract_text_from_doc_antiword,
    extract_text_from_docx,
    extract_text_from_excel,
    extract_text_from_pdf_pdfplumber,
    extract_text_from_pptx,
    extract_text_from_textlike,
    extract_text_locally,
    extract_text_locally_with_retry,
)
from .text_utils import (
    count_tokens,
    get_tiktoken_encoder,
    normalize_text,
    rows_to_markdown_table,
    safe_decode,
    strip_html_tags,
)

__all__ = [
    "ANTIWORD_BIN",
    "ANTIWORD_CPU_SECONDS",
    "ANTIWORD_MEMORY_MB",
    "ANTIWORD_SHARE_DIR",
    "ID_CAT_DICT",
    "LOCAL_PARSE_MAX_RETRIES",
    "LOCAL_PARSE_RETRY_DELAY_SECONDS",
    "MAX_CHUNK_CHARS",
    "MAX_CSV_ROWS",
    "MAX_DOCUMENT_BYTES",
    "MAX_EXCEL_ROWS_PER_SHEET",
    "MAX_EXCEL_SHEETS",
    "MAX_PDF_PAGES",
    "MAX_PPTX_SLIDES",
    "PARSE_TIMEOUT_SECONDS",
    "TEXTLIKE_EXTENSIONS",
    "TOKENIZER_ENCODING",
    "count_tokens",
    "extract_text_from_doc_antiword",
    "extract_text_from_docx",
    "extract_text_from_excel",
    "extract_text_from_pdf_pdfplumber",
    "extract_text_from_pptx",
    "extract_text_from_textlike",
    "extract_text_locally",
    "extract_text_locally_with_retry",
    "get_tiktoken_encoder",
    "normalize_text",
    "rows_to_markdown_table",
    "safe_decode",
    "split_text_to_chunks",
    "strip_html_tags",
]

# Spark-backed features are optional for pure local parsing usage.
try:
    from .ai_payload import extract_text_from_ai_payload, extract_text_from_ai_payload_udf

    __all__.extend(["extract_text_from_ai_payload", "extract_text_from_ai_payload_udf"])
except Exception:
    extract_text_from_ai_payload = None
    extract_text_from_ai_payload_udf = None

try:
    from .schemas import CHUNK_SCHEMA, TEXT_PARSE_SCHEMA

    __all__.extend(["CHUNK_SCHEMA", "TEXT_PARSE_SCHEMA"])
except Exception:
    CHUNK_SCHEMA = None
    TEXT_PARSE_SCHEMA = None

try:
    from .udfs import build_chunks_udf, build_chunks_with_limits_udf, extract_local_text_udf, token_count_udf

    __all__.extend(["build_chunks_udf", "build_chunks_with_limits_udf", "extract_local_text_udf", "token_count_udf"])
except Exception:
    build_chunks_udf = None
    build_chunks_with_limits_udf = None
    extract_local_text_udf = None
    token_count_udf = None
