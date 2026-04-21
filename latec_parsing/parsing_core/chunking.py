import hashlib
import re
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from .constants import (
    CHUNK_MARKDOWN_IGNORE_PAGE_MARKERS,
    CHUNK_MARKDOWN_MIN_HEADERS,
    CHUNK_SHORT_MERGE_ENABLED,
    CHUNK_SHORT_MERGE_MAX_EXPANSION,
    CHUNK_SHORT_MERGE_TARGET_TOKENS,
    MAX_CHUNK_CHARS,
    TOKENIZER_ENCODING,
)
from .text_utils import count_tokens, normalize_text

TABLE_BLOCK_PATTERN = re.compile(r"\[TABLE_START\].*?\[TABLE_END\]", re.DOTALL)
MARKDOWN_HEADER_LINE_PATTERN = re.compile(r"^#{1,6}\s+\S+", re.MULTILINE)
PROVENANCE_HEADER_PATTERN = re.compile(r"^##\s*(Page\s+\d+|Sheet:|Slide\s+\d+)\b", re.IGNORECASE)
PAGE_PATTERN = re.compile(r"##\s*Page\s+(\d+)", re.IGNORECASE)
SHEET_PATTERN = re.compile(r"##\s*Sheet:\s*(.+)", re.IGNORECASE)
SLIDE_PATTERN = re.compile(r"##\s*Slide\s+(\d+)", re.IGNORECASE)


def _coerce_chunk_limits(
    chunk_size_tokens: int,
    chunk_overlap_tokens: int,
    min_chunk_tokens: int,
    max_chunk_tokens: Optional[int],
):
    chunk_size = max(50, int(chunk_size_tokens or 600))
    chunk_overlap = max(0, min(int(chunk_overlap_tokens or 0), chunk_size - 1))
    min_tokens = max(0, int(min_chunk_tokens or 0))
    max_tokens = int(max_chunk_tokens) if max_chunk_tokens and int(max_chunk_tokens) > 0 else None
    return chunk_size, chunk_overlap, min_tokens, max_tokens


def _is_probably_markdown(text: str) -> bool:
    headers = []
    for line in text.splitlines():
        if not MARKDOWN_HEADER_LINE_PATTERN.match(line):
            continue

        normalized_line = normalize_text(line)
        if CHUNK_MARKDOWN_IGNORE_PAGE_MARKERS and PROVENANCE_HEADER_PATTERN.match(normalized_line):
            continue
        headers.append(normalized_line)

    if len(headers) < CHUNK_MARKDOWN_MIN_HEADERS:
        return False

    line_count = max(1, len(text.splitlines()))
    header_density = len(headers) / float(line_count)
    return header_density <= 0.45


def _extract_provenance_metadata(segment_text: str) -> Dict[str, str]:
    provenance: Dict[str, str] = {}

    page_match = PAGE_PATTERN.search(segment_text)
    if page_match:
        provenance["source_page"] = page_match.group(1)

    sheet_match = SHEET_PATTERN.search(segment_text)
    if sheet_match:
        provenance["source_sheet"] = normalize_text(sheet_match.group(1))

    slide_match = SLIDE_PATTERN.search(segment_text)
    if slide_match:
        provenance["source_slide"] = slide_match.group(1)

    return provenance


def _classify_chunk_content(text: str) -> str:
    if "[TABLE_START]" in text:
        return "table"
    if "[DIAGRAM_START]" in text:
        return "diagram"
    if re.search(r"^#{1,6}\s+", text, re.MULTILINE):
        semantic_headers = []
        for line in text.splitlines():
            if not MARKDOWN_HEADER_LINE_PATTERN.match(line):
                continue
            normalized_line = normalize_text(line)
            if CHUNK_MARKDOWN_IGNORE_PAGE_MARKERS and PROVENANCE_HEADER_PATTERN.match(normalized_line):
                continue
            semantic_headers.append(normalized_line)
        if semantic_headers:
            return "heading"
    if re.search(r"^[-*]\s+", text, re.MULTILINE):
        return "list"
    return "text"


def _is_table_block(text: str) -> bool:
    return "[TABLE_START]" in text and "[TABLE_END]" in text


def _can_merge_adjacent_chunks(
    left_chunk: Dict[str, Any],
    right_chunk: Dict[str, Any],
    max_merge_tokens: int,
) -> bool:
    if not left_chunk or not right_chunk:
        return False

    if left_chunk.get("metadata") != right_chunk.get("metadata"):
        return False

    left_text = str(left_chunk.get("text") or "")
    right_text = str(right_chunk.get("text") or "")
    if not left_text or not right_text:
        return False

    if _is_table_block(left_text) or _is_table_block(right_text):
        return False

    merged_text = normalize_text(f"{left_text}\n\n{right_text}")
    return count_tokens(merged_text) <= max_merge_tokens


def _merge_short_adjacent_chunks(
    candidate_chunks: List[Dict[str, Any]],
    min_tokens: int,
    chunk_size: int,
    max_tokens: Optional[int],
) -> List[Dict[str, Any]]:
    if not candidate_chunks:
        return []

    if not CHUNK_SHORT_MERGE_ENABLED or min_tokens <= 0:
        return candidate_chunks

    max_merge_tokens = max(min_tokens, int(round(chunk_size * (1.0 + CHUNK_SHORT_MERGE_MAX_EXPANSION))))
    if max_tokens and max_tokens > 0:
        max_merge_tokens = min(max_merge_tokens, int(max_tokens))

    target_tokens = max(min_tokens, CHUNK_SHORT_MERGE_TARGET_TOKENS)
    merged_chunks: List[Dict[str, Any]] = []
    index = 0

    while index < len(candidate_chunks):
        current = {
            "text": str(candidate_chunks[index].get("text") or ""),
            "metadata": dict(candidate_chunks[index].get("metadata") or {}),
        }
        next_index = index + 1

        current_tokens = count_tokens(current["text"])
        if _is_table_block(current["text"]):
            merged_chunks.append(current)
            index = next_index
            continue

        while current_tokens < target_tokens and next_index < len(candidate_chunks):
            candidate_next = {
                "text": str(candidate_chunks[next_index].get("text") or ""),
                "metadata": dict(candidate_chunks[next_index].get("metadata") or {}),
            }

            if not _can_merge_adjacent_chunks(current, candidate_next, max_merge_tokens):
                break

            current["text"] = normalize_text(f"{current['text']}\n\n{candidate_next['text']}")
            current_tokens = count_tokens(current["text"])
            next_index += 1

        if current_tokens < min_tokens and merged_chunks:
            previous = merged_chunks[-1]
            previous_view = {
                "text": str(previous.get("text") or ""),
                "metadata": dict(previous.get("metadata") or {}),
            }
            if _can_merge_adjacent_chunks(previous_view, current, max_merge_tokens):
                previous["text"] = normalize_text(f"{previous['text']}\n\n{current['text']}")
            else:
                merged_chunks.append(current)
        else:
            merged_chunks.append(current)

        index = next_index

    return merged_chunks


def _split_oversized_chunk(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    parts: List[str] = []
    overlap = min(120, max(20, max_chars // 8))
    start = 0

    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            newline_boundary = text.rfind("\n", start + (max_chars // 2), end)
            if newline_boundary > start:
                end = newline_boundary

        piece = text[start:end].strip()
        if piece:
            parts.append(piece)

        if end >= len(text):
            break
        start = max(0, end - overlap)

    return parts or [text[:max_chars]]


def _build_stable_chunk_id(chunk_text: str, metadata: Dict[str, str]) -> str:
    metadata_repr = "|".join([f"{key}={metadata[key]}" for key in sorted(metadata.keys())])
    payload = f"{metadata_repr}||{chunk_text}"
    return hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()


def split_text_to_chunks(
    text: str,
    chunk_size_tokens: int,
    chunk_overlap_tokens: int,
    min_chunk_tokens: int = 0,
    max_chunk_tokens: Optional[int] = None,
) -> List[Dict[str, Any]]:
    normalized_text = normalize_text(text)
    if not normalized_text:
        return []

    chunk_size, chunk_overlap, min_tokens, max_tokens = _coerce_chunk_limits(
        chunk_size_tokens,
        chunk_overlap_tokens,
        min_chunk_tokens,
        max_chunk_tokens,
    )

    if _is_probably_markdown(normalized_text):
        headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        try:
            semantic_splits = markdown_splitter.split_text(normalized_text)
        except Exception:
            semantic_splits = [SimpleNamespace(page_content=normalized_text, metadata={})]
    else:
        semantic_splits = [SimpleNamespace(page_content=normalized_text, metadata={})]

    custom_separators = [
        "\n[TABLE_START]\n",
        "\n[TABLE_END]\n",
        "\n\n",
        "\n",
        ". ",
        "! ",
        "? ",
        "; ",
        "\u3002",
        "\u3001",
        "\uff0c",
        "\uff0e",
        "\u200b",
        " ",
        "",
    ]
    token_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=TOKENIZER_ENCODING,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=custom_separators,
    )

    candidate_chunks: List[Dict[str, Any]] = []
    final_chunks = []
    seen_chunk_ids = set()
    chunk_index = 0

    def add_candidate_chunk(enriched_text: str, metadata: Dict[str, str]) -> None:
        for piece in _split_oversized_chunk(enriched_text, MAX_CHUNK_CHARS):
            cleaned_piece = normalize_text(piece)
            if not cleaned_piece:
                continue
            candidate_chunks.append({"text": cleaned_piece, "metadata": dict(metadata)})

    def add_final_chunk(piece: str, metadata: Dict[str, str]) -> None:
        nonlocal chunk_index

        token_count = count_tokens(piece)
        if token_count < min_tokens:
            return

        effective_metadata = dict(metadata)
        if max_tokens and token_count > max_tokens:
            if _is_table_block(piece):
                effective_metadata["chunk_token_overflow"] = "table_preserved"
            else:
                return

        stable_id = _build_stable_chunk_id(piece, effective_metadata)
        if stable_id in seen_chunk_ids:
            return
        seen_chunk_ids.add(stable_id)

        final_chunks.append(
            {
                "chunk_index": chunk_index,
                "chunk_stable_id": stable_id,
                "chunk_text": piece,
                "chunk_char_count": len(piece),
                "chunk_token_count": token_count,
                "chunk_content_type": _classify_chunk_content(piece),
                "metadata": effective_metadata,
            }
        )
        chunk_index += 1

    def split_preserving_table_blocks(segment_text: str) -> List[str]:
        if "[TABLE_START]" not in segment_text or "[TABLE_END]" not in segment_text:
            return token_splitter.split_text(segment_text)

        chunks: List[str] = []
        cursor = 0
        for match in TABLE_BLOCK_PATTERN.finditer(segment_text):
            prefix = segment_text[cursor : match.start()]
            if prefix.strip():
                chunks.extend(token_splitter.split_text(prefix))
            table_block = match.group(0).strip()
            if table_block:
                chunks.append(table_block)
            cursor = match.end()

        suffix = segment_text[cursor:]
        if suffix.strip():
            chunks.extend(token_splitter.split_text(suffix))
        return chunks

    for semantic_doc in semantic_splits:
        segment_text = str(semantic_doc.page_content)
        sub_chunks = split_preserving_table_blocks(segment_text)

        metadata = {
            str(key): str(value)
            for key, value in dict(getattr(semantic_doc, "metadata", {}) or {}).items()
            if value is not None
        }
        metadata.update({key: value for key, value in _extract_provenance_metadata(segment_text).items() if value})
        metadata["metadata_schema_version"] = "1"

        header_values = [metadata.get("Header 1"), metadata.get("Header 2"), metadata.get("Header 3")]
        header_context = " > ".join([value for value in header_values if value])

        for sub_chunk in sub_chunks:
            enriched_text = f"[{header_context}]\n{sub_chunk}" if header_context else sub_chunk
            add_candidate_chunk(enriched_text, metadata)

    merged_candidates = _merge_short_adjacent_chunks(
        candidate_chunks,
        min_tokens=min_tokens,
        chunk_size=chunk_size,
        max_tokens=max_tokens,
    )
    for candidate in merged_candidates:
        add_final_chunk(str(candidate.get("text") or ""), dict(candidate.get("metadata") or {}))

    return final_chunks
