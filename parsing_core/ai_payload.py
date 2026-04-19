import json
from typing import Any, Iterable, List, Optional

import pandas as pd
from pyspark.sql import types as T
from pyspark.sql.functions import pandas_udf

from .text_utils import normalize_text


_PREFERRED_TEXT_FIELDS = (
    "text",
    "content",
    "markdown",
    "value",
    "body",
)


def _append_if_text(values: List[str], candidate: Any) -> None:
    if isinstance(candidate, str):
        normalized = normalize_text(candidate)
        if normalized:
            values.append(normalized)


def _collect_text_candidates(node: Any, values: List[str]) -> None:
    if isinstance(node, dict):
        for key in _PREFERRED_TEXT_FIELDS:
            _append_if_text(values, node.get(key))
        for value in node.values():
            _collect_text_candidates(value, values)
        return

    if isinstance(node, list):
        for item in node:
            _collect_text_candidates(item, values)


def _deduplicate_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    output: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def extract_text_from_ai_payload(payload: Optional[str]) -> str:
    if not payload:
        return ""

    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", errors="ignore")

    payload = str(payload)
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return normalize_text(payload)

    candidates: List[str] = []

    if isinstance(parsed, dict):
        error_status = parsed.get("error_status")
        if isinstance(error_status, list) and error_status:
            first_error = error_status[0]
            if isinstance(first_error, dict) and first_error.get("error_message"):
                return ""

    _collect_text_candidates(parsed, candidates)

    unique_candidates = _deduplicate_preserve_order(candidates)
    return normalize_text("\n\n".join(unique_candidates))


@pandas_udf(T.StringType())
def extract_text_from_ai_payload_udf(payload_series: pd.Series) -> pd.Series:
    return payload_series.apply(extract_text_from_ai_payload)
