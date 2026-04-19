from typing import Any, Dict

import pandas as pd
from pyspark.sql import types as T
from pyspark.sql.functions import pandas_udf

from .chunking import split_text_to_chunks
from .constants import LOCAL_PARSE_MAX_RETRIES
from .extractors import extract_text_locally_with_retry
from .schemas import CHUNK_SCHEMA, TEXT_PARSE_SCHEMA
from .text_utils import count_tokens


@pandas_udf(TEXT_PARSE_SCHEMA)
def extract_local_text_udf(content_series: pd.Series, ext_series: pd.Series) -> pd.DataFrame:
    results = []
    for content, ext in zip(content_series, ext_series):
        if content is None:
            results.append(
                {
                    "text": "",
                    "parser_error": "No Content",
                    "parser_strategy": "none",
                    "parse_time_seconds": 0.0,
                }
            )
        else:
            ext_value = str(ext) if ext is not None else ""
            parsed = extract_text_locally_with_retry(
                content,
                ext_value,
                max_retries=LOCAL_PARSE_MAX_RETRIES,
            )
            results.append(parsed)
    return pd.DataFrame(results)


@pandas_udf(CHUNK_SCHEMA)
def build_chunks_udf(text_series: pd.Series, sz_series: pd.Series, ov_series: pd.Series) -> pd.Series:
    results = []
    for text, sz, ov in zip(text_series, sz_series, ov_series):
        if not text:
            results.append([])
        else:
            chunks = split_text_to_chunks(str(text), int(sz), int(ov))
            results.append(chunks)
    return pd.Series(results)


@pandas_udf(CHUNK_SCHEMA)
def build_chunks_with_limits_udf(
    text_series: pd.Series,
    sz_series: pd.Series,
    ov_series: pd.Series,
    min_series: pd.Series,
    max_series: pd.Series,
) -> pd.Series:
    results = []
    for text, sz, ov, minimum, maximum in zip(text_series, sz_series, ov_series, min_series, max_series):
        if not text:
            results.append([])
            continue

        chunks = split_text_to_chunks(
            str(text),
            int(sz),
            int(ov),
            int(minimum) if minimum is not None else 0,
            int(maximum) if maximum is not None else None,
        )
        results.append(chunks)
    return pd.Series(results)


@pandas_udf(T.IntegerType())
def token_count_udf(text_series: pd.Series) -> pd.Series:
    return pd.Series([count_tokens(str(text)) if text else 0 for text in text_series])
