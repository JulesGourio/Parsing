import re
from functools import lru_cache
from typing import Any, Iterable, List

import pandas as pd
from bs4 import BeautifulSoup

from .constants import DEFAULT_DECODE_ENCODINGS, TOKENIZER_ENCODING


def safe_decode(raw_bytes: bytes, encodings: Iterable[str] = None) -> str:
    if not raw_bytes:
        return ""

    decode_chain = tuple(encodings) if encodings else DEFAULT_DECODE_ENCODINGS
    for enc in decode_chain:
        try:
            return raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def strip_html_tags(text: str) -> str:
    if not text:
        return ""
    try:
        soup = BeautifulSoup(text, "lxml")
    except Exception:
        soup = BeautifulSoup(text, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    return soup.get_text(separator=" ", strip=True)


def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    return re.sub(r"\n{3,}", "\n\n", normalized).strip()


def rows_to_markdown_table(rows: List[List[Any]]) -> str:
    if not rows:
        return ""

    normalized_rows = [
        [normalize_text(str(cell) if pd.notna(cell) and cell is not None else "") for cell in row]
        for row in rows
    ]
    col_count = max((len(row) for row in normalized_rows), default=0)
    if col_count == 0:
        return ""

    normalized_rows = [row + [""] * (col_count - len(row)) for row in normalized_rows]
    header = normalized_rows[0]
    body = normalized_rows[1:] if len(normalized_rows) > 1 else []

    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * col_count) + " |"]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def get_tiktoken_encoder():
    import tiktoken

    return tiktoken.get_encoding(TOKENIZER_ENCODING)


def count_tokens(text: str) -> int:
    if not text:
        return 0
    try:
        encoder = get_tiktoken_encoder()
        return len(encoder.encode(text))
    except Exception:
        # Conservative fallback when tokenizer is unavailable.
        return max(1, len(text) // 4)
