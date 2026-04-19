from pyspark.sql import types as T

TEXT_PARSE_SCHEMA = T.StructType(
    [
        T.StructField("text", T.StringType(), True),
        T.StructField("parser_error", T.StringType(), True),
        T.StructField("parser_strategy", T.StringType(), True),
        T.StructField("parse_time_seconds", T.FloatType(), True),
        T.StructField("ocr_attempted", T.BooleanType(), True),
        T.StructField("ocr_used", T.BooleanType(), True),
        T.StructField("ocr_engine_trace", T.StringType(), True),
        T.StructField("ocr_pages", T.IntegerType(), True),
        T.StructField("ocr_supplement_pages", T.IntegerType(), True),
    ]
)

CHUNK_SCHEMA = T.ArrayType(
    T.StructType(
        [
            T.StructField("chunk_index", T.IntegerType(), True),
            T.StructField("chunk_stable_id", T.StringType(), True),
            T.StructField("chunk_text", T.StringType(), True),
            T.StructField("chunk_char_count", T.IntegerType(), True),
            T.StructField("chunk_token_count", T.IntegerType(), True),
            T.StructField("chunk_content_type", T.StringType(), True),
            T.StructField("metadata", T.MapType(T.StringType(), T.StringType()), True),
        ]
    )
)
