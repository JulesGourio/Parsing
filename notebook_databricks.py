# Databricks notebook source
# MAGIC %pip install -q lxml langchain-text-splitters tiktoken pdfplumber beautifulsoup4 python-docx python-pptx pandas openpyxl xlrd pyxlsb

# COMMAND ----------
import uuid
from itertools import chain

from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

from utils import *

# Optimize small file reading
spark.conf.set("spark.sql.files.maxPartitionBytes", "134217728")
spark.conf.set("spark.sql.files.openCostInBytes", "134217728")
spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")

VOLUME_ROOT_PATH = "/Volumes/dev_landingzone/intraqual/intraqual_documents"
TARGET_PROCESSED_FILES_TABLE = "dev_lab.lab_jules.processed_files"
TARGET_CHUNK_TABLE = "dev_lab.lab_jules.chunks"

TRASH_FILES_BLACKLIST = [
    "headers.html",
    "thumbs.db",
    ".ds_store",
    "desktop.ini",
    "copyright.txt",
]

AUDIT_DB = "dev_lab.lab_jules"
TABLE_UNIFIED_AUDIT = f"{AUDIT_DB}.audit_files_unified"

# =============================================================================
# RUN MODE: "AUDIT_ONLY" = generate audit table only (no parsing)
#           "FULL"       = audit + parsing + chunking
# =============================================================================
RUN_MODE = "FULL"

FORMAT_PRIORITIES = {
    "docx": 1,
    "pdf": 2,
    "docm": 3,
    "doc": 4,
    "html": 5,
    "pptx": 6,
    "ppt": 7,
    "txt": 8,
    "xml": 9,
    "xlsx": 10,
    "xls": 11,
    "xlsm": 12,
    "xlsb": 13,
}

LIMIT_TEST_FILES = 500000
ENABLE_AI_FALLBACK = False
AI_FALLBACK_MAX_RETRIES = 2
AI_RETRYABLE_ERROR_REGEX = "(?i)(timeout|tempor|rate\\s*limit|429|503|service unavailable|connection|internal)"

CHUNK_SIZE_TOKENS = 600
CHUNK_OVERLAP_TOKENS = 120
MIN_CHUNK_TOKENS = 80
TABLE_CHUNK_MAX_TOKENS = 1500

if TABLE_CHUNK_MAX_TOKENS and MIN_CHUNK_TOKENS > TABLE_CHUNK_MAX_TOKENS:
    raise ValueError("MIN_CHUNK_TOKENS cannot be greater than TABLE_CHUNK_MAX_TOKENS")

INGESTION_RUN_ID = str(uuid.uuid4())

# COMMAND ----------
# ============================================================
# CELL 2: DATABASE-DRIVEN SELECTION & UNIFIED DIAGNOSTIC AUDIT
# ============================================================

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from itertools import chain

# ------------------------------------------------------------
# STEP 1: LOAD BUSINESS TRUTH (DATABASE METADATA)
# ------------------------------------------------------------
mapping_data = [(cat, prefix) for prefix, cats in ID_CAT_DICT.items() for cat in cats]
df_doc_cat = spark.read.table("dev_landingzone.intraqual.gd_doc_cat")

if mapping_data:
    df_prefix_mapping = spark.createDataFrame(mapping_data, ["IDCAT", "gd_prefix"])
    df_doc_prefixes = (
        df_doc_cat.join(F.broadcast(df_prefix_mapping), on="IDCAT", how="inner")
        .groupBy("IDDOC")
        .agg(F.concat_ws(",", F.collect_set("gd_prefix")).alias("document_prefixes"))
    )
else:
    print(
        "WARNING: ID_CAT_DICT is empty. Falling back to IDCAT-based prefixes for document_prefixes."
    )
    df_doc_prefixes = (
        df_doc_cat.groupBy("IDDOC")
        .agg(F.concat_ws(",", F.collect_set(F.col("IDCAT").cast("string"))).alias("document_prefixes"))
    )

df_kb = spark.read.table("dev_landingzone.intraqual.gd_knowledge_base")

# FIX: gd_knowledge_base has ~260K rows for ~18K IDDOCs (pure row duplication).
# Dedup to 1 row per IDDOC to prevent artificial join multiplication.
kb_stats = df_kb.agg(
    F.count("*").alias("row_count"),
    F.countDistinct("IDDOC").alias("distinct_iddoc_count"),
).collect()[0]
df_kb_dedup = df_kb.dropDuplicates(["IDDOC"])
print(
    "gd_knowledge_base: "
    f"{kb_stats['row_count']} rows -> {kb_stats['distinct_iddoc_count']} after dedup by IDDOC"
)

df_doc_raw = (
    spark.read.table("dev_landingzone.intraqual.gd_doc")
    .filter(F.col("courant") == 1)
    .select("IDDOC")
)

df_business_meta = (
    df_kb_dedup.join(df_doc_raw, on="IDDOC", how="inner")
    .join(F.broadcast(df_doc_prefixes), on="IDDOC", how="left")
)
df_business_meta.cache()
business_iddocs = F.broadcast(df_business_meta.select("IDDOC").distinct())

# Lookup tables for orphaned file enrichment (all courant values)
df_doc_lookup = (
    spark.read.table("dev_landingzone.intraqual.gd_doc")
    .groupBy("IDDOC")
    .agg(
        F.max("courant").alias("_max_courant"),
        F.concat_ws(
            ",",
            F.sort_array(F.collect_set(F.col("courant").cast("string"))),
        ).alias("_courant_values"),
        F.first("REF").alias("_doc_ref"),
        F.first("TITRE").alias("_doc_titre"),
    )
)

df_kb_lookup = df_kb_dedup.select(
    F.col("IDDOC"),
    F.col("ref").alias("_kb_ref"),
    F.col("titre").alias("_kb_titre"),
)

# ------------------------------------------------------------
# STEP 2: LOAD PHYSICAL FILES (METADATA ONLY FOR AUDIT)
# ------------------------------------------------------------
df_files_raw = (
    spark.read.format("binaryFile")
    .option("recursiveFileLookup", "true")
    .load(VOLUME_ROOT_PATH)
)

df_meta_raw = (
    df_files_raw.select(
        F.col("path").alias("source_path"),
        F.col("length").cast("long").alias("source_file_size_bytes"),
        F.col("modificationTime").alias("source_modification_time"),
    )
    .withColumn("source_file_name", F.element_at(F.split(F.col("source_path"), "/"), -1))
    .withColumn(
        "source_file_extension",
        F.lower(F.regexp_extract(F.col("source_file_name"), r"\.([^.]+)$", 1)),
    )
    .withColumn("source_folder_path", F.regexp_replace(F.col("source_path"), r"/[^/]+$", ""))
    .withColumn("ingestion_run_id", F.lit(INGESTION_RUN_ID))
    .withColumn("ingestion_timestamp", F.current_timestamp())
)

df_meta_raw = df_meta_raw.filter(
    ~F.lower(F.col("source_file_name")).isin(TRASH_FILES_BLACKLIST)
    & ~F.col("source_file_name").startswith("~")
)

# Smart IDDOC extraction with diagnostic tracking
df_meta_raw = (
    df_meta_raw.withColumn(
        "extracted_folder_id",
        F.regexp_extract(F.col("source_path"), r"/[dD]m?_(\d+)/", 1),
    )
    .withColumn(
        "extracted_file_id",
        F.regexp_extract(F.col("source_file_name"), r"^[dD]m?_(\d+)", 1),
    )
    .withColumn(
        "extracted_raw_number",
        F.regexp_extract(F.col("source_file_name"), r"^(\d+)", 1),
    )
    .withColumn(
        "iddoc_extraction_method",
        F.when(F.col("extracted_folder_id") != "", F.lit("FOLDER_D_PREFIX"))
        .when(F.col("extracted_file_id") != "", F.lit("FILENAME_D_PREFIX"))
        .when(F.col("extracted_raw_number") != "", F.lit("FILENAME_RAW_NUMBER"))
        .otherwise(F.lit("NO_EXTRACTION_POSSIBLE")),
    )
    .withColumn(
        "file_naming_pattern",
        F.when(F.col("source_file_name").rlike(r"^[dD]m_"), F.lit("Dm_IDDOC (modified doc)"))
        .when(F.col("source_file_name").rlike(r"^[dD]_"), F.lit("D_IDDOC (standard)"))
        .when(F.col("source_file_name").rlike(r"^\d+"), F.lit("RAW_NUMBER (bare number)"))
        .otherwise(F.lit("NON_STANDARD (no recognized pattern)")),
    )
    .withColumn(
        "IDDOC",
        F.coalesce(
            F.nullif(F.col("extracted_folder_id"), F.lit("")),
            F.nullif(F.col("extracted_file_id"), F.lit("")),
            F.nullif(F.col("extracted_raw_number"), F.lit("")),
        ).cast("bigint"),
    )
)
df_meta_raw.cache()
file_iddocs = F.broadcast(df_meta_raw.select("IDDOC").distinct())

# ------------------------------------------------------------
# STEP 3: RANKING & DEDUPLICATION (shared between AUDIT and FULL)
# Priority order: D_ > Dm_ > format priority > newest modification
# ------------------------------------------------------------
df_matched_files = df_meta_raw.join(df_business_meta, on="IDDOC", how="inner")

mapping_expr = F.create_map([F.lit(x) for x in chain(*FORMAT_PRIORITIES.items())])

df_matched_ranked = (
    df_matched_files.withColumn(
        "ext_priority",
        F.coalesce(mapping_expr[F.col("source_file_extension")], F.lit(99)),
    ).withColumn(
        "is_dm_file",
        F.when(F.col("source_file_name").rlike(r"^[dD]m_"), 1).otherwise(0),
    )
)

window_priority = Window.partitionBy("IDDOC").orderBy(
    F.col("is_dm_file").asc(),
    F.col("ext_priority").asc(),
    F.col("source_modification_time").desc(),
)

df_matched_ranked = (
    df_matched_ranked.withColumn("priority_rank", F.row_number().over(window_priority))
    .withColumn(
        "files_count_for_iddoc",
        F.count("*").over(Window.partitionBy("IDDOC")),
    )
)

df_selected_info = df_matched_ranked.filter(F.col("priority_rank") == 1).select(
    F.col("IDDOC"),
    F.col("source_file_name").alias("selected_file_for_iddoc"),
    F.col("source_file_extension").alias("_sel_ext"),
    F.col("ext_priority").alias("_sel_ext_priority"),
    F.col("is_dm_file").alias("_sel_is_dm"),
)

df_matched_full = df_matched_ranked.join(F.broadcast(df_selected_info), on="IDDOC", how="left")

df_matched_full = (
    df_matched_full.withColumn(
        "depriority_reason",
        F.when(F.col("priority_rank") == 1, F.lit(None).cast("string"))
        .when(
            F.col("ext_priority") == 99,
            F.concat(
                F.lit("UNSUPPORTED_FORMAT: '"),
                F.col("source_file_extension"),
                F.lit("' not in supported formats. Selected: '"),
                F.col("selected_file_for_iddoc"),
                F.lit("'"),
            ),
        )
        .when(
            (F.col("is_dm_file") == 1) & (F.col("_sel_is_dm") == 0),
            F.concat(
                F.lit("PREFIX_LOWER_PRIORITY: Dm_ always deprioritized vs D_. Selected: '"),
                F.col("selected_file_for_iddoc"),
                F.lit("'"),
            ),
        )
        .when(
            F.col("ext_priority") > F.col("_sel_ext_priority"),
            F.concat(
                F.lit("FORMAT_LOWER_PRIORITY: "),
                F.col("source_file_extension"),
                F.lit(" (rank "),
                F.col("ext_priority"),
                F.lit(")"),
                F.lit(" vs "),
                F.col("_sel_ext"),
                F.lit(" (rank "),
                F.col("_sel_ext_priority"),
                F.lit(")."),
                F.lit(" Selected: '"),
                F.col("selected_file_for_iddoc"),
                F.lit("'"),
            ),
        )
        .otherwise(
            F.concat(
                F.lit("OLDER_FILE: Same prefix & format but older modification date. Selected: '"),
                F.col("selected_file_for_iddoc"),
                F.lit("'"),
            ),
        ),
    ).drop("_sel_ext", "_sel_ext_priority", "_sel_is_dm")
)

# ------------------------------------------------------------
# STEP 4: BUILD UNIFIED DIAGNOSTIC AUDIT TABLE
# ------------------------------------------------------------

# --- AUDIT A: Business documents WITHOUT a matching physical file ---
df_missing_files = (
    df_business_meta.join(file_iddocs, on="IDDOC", how="left_anti")
    .withColumn("audit_type", F.lit("MISSING_FILE"))
    .withColumn("source_path", F.lit(None).cast("string"))
    .withColumn("source_file_name", F.lit(None).cast("string"))
    .withColumn("source_file_extension", F.lit(None).cast("string"))
    .withColumn("source_folder_path", F.lit(None).cast("string"))
    .withColumn("source_file_size_bytes", F.lit(None).cast("long"))
    .withColumn("source_modification_time", F.lit(None).cast("timestamp"))
    .withColumn("iddoc_extraction_method", F.lit("N/A"))
    .withColumn("file_naming_pattern", F.lit("N/A"))
    .withColumn("iddoc_in_business_db", F.lit(True))
    .withColumn("file_exists_on_disk", F.lit(False))
    .withColumn("priority_rank", F.lit(None).cast("int"))
    .withColumn("files_count_for_iddoc", F.lit(None).cast("int"))
    .withColumn("selected_file_for_iddoc", F.lit(None).cast("string"))
    .withColumn("depriority_reason", F.lit(None).cast("string"))
    .withColumn("courant_values", F.lit(None).cast("string"))
    .withColumn(
        "diagnostic_message",
        F.concat(
            F.lit("Document IDDOC="),
            F.col("IDDOC"),
            F.lit(" (ref: "),
            F.coalesce(F.col("ref"), F.lit("?")),
            F.lit(")"),
            F.lit(" exists in gd_knowledge_base but NO physical file was found in the volume."),
        ),
    )
    .withColumn("root_cause", F.lit("FILE_ABSENT_FROM_STORAGE"))
    .withColumn(
        "recommended_action",
        F.lit("Check if the file was archived, deleted, or never uploaded to the volume."),
    )
)

# --- AUDIT B: Physical files WITHOUT a matching business record ---
# Enriched with gd_doc (all courant values) and gd_knowledge_base
df_orphaned_enriched = (
    df_meta_raw.join(business_iddocs, on="IDDOC", how="left_anti")
    .join(F.broadcast(df_doc_lookup), on="IDDOC", how="left")
    .join(F.broadcast(df_kb_lookup), on="IDDOC", how="left")
)

df_orphaned_files = (
    df_orphaned_enriched.withColumn("audit_type", F.lit("ORPHANED_FILE"))
    .withColumn("ref", F.coalesce(F.col("_kb_ref"), F.col("_doc_ref")))
    .withColumn("titre", F.coalesce(F.col("_kb_titre"), F.col("_doc_titre")))
    .withColumn("type_document", F.lit(None).cast("string"))
    .withColumn("categorie", F.lit(None).cast("string"))
    .withColumn("langue", F.lit(None).cast("string"))
    .withColumn("auteur", F.lit(None).cast("string"))
    .withColumn("document_prefixes", F.lit(None).cast("string"))
    .withColumn("iddoc_in_business_db", F.lit(False))
    .withColumn("file_exists_on_disk", F.lit(True))
    .withColumn("priority_rank", F.lit(None).cast("int"))
    .withColumn("files_count_for_iddoc", F.lit(None).cast("int"))
    .withColumn("selected_file_for_iddoc", F.lit(None).cast("string"))
    .withColumn("depriority_reason", F.lit(None).cast("string"))
    .withColumn("courant_values", F.col("_courant_values"))
    .withColumn(
        "root_cause",
        F.when(F.col("IDDOC").isNull(), F.lit("NON_CONFORMING_NAME_NO_IDDOC"))
        .when(F.col("_max_courant").isNull(), F.lit("IDDOC_NOT_IN_GD_DOC"))
        .when(F.col("_max_courant") < 1, F.lit("ARCHIVED_DOCUMENT_COURANT_0"))
        .when(
            (F.col("_max_courant") >= 1) & F.col("_kb_ref").isNull(),
            F.lit("IN_GD_DOC_BUT_NOT_IN_KNOWLEDGE_BASE"),
        )
        .when(F.col("_max_courant") == 2, F.lit("DOCUMENT_IN_PROGRESS_COURANT_2"))
        .when(
            F.col("iddoc_extraction_method") == "FILENAME_RAW_NUMBER",
            F.lit("AMBIGUOUS_NAME_BARE_NUMBER"),
        )
        .otherwise(F.lit("IDDOC_NOT_IN_BUSINESS_DB")),
    )
    .withColumn(
        "diagnostic_message",
        F.concat(
            F.lit("File '"),
            F.col("source_file_name"),
            F.lit("' "),
            F.when(
                F.col("IDDOC").isNull(),
                F.lit("has no extractable IDDOC (non-conforming naming)."),
            )
            .when(
                F.col("_max_courant").isNull(),
                F.concat(
                    F.lit("has extracted IDDOC="),
                    F.col("IDDOC"),
                    F.lit(" but this IDDOC does NOT exist anywhere in gd_doc."),
                ),
            )
            .when(
                F.col("_max_courant") < 1,
                F.concat(
                    F.lit("has IDDOC="),
                    F.col("IDDOC"),
                    F.lit(" which is ARCHIVED in gd_doc (courant="),
                    F.col("_courant_values"),
                    F.lit(")."),
                    F.lit(" Ref: "),
                    F.coalesce(F.col("ref"), F.lit("?")),
                ),
            )
            .when(
                F.col("_kb_ref").isNull(),
                F.concat(
                    F.lit("has IDDOC="),
                    F.col("IDDOC"),
                    F.lit(" found in gd_doc (courant="),
                    F.col("_courant_values"),
                    F.lit(")"),
                    F.lit(" but NOT present in gd_knowledge_base."),
                ),
            )
            .otherwise(
                F.concat(
                    F.lit("has IDDOC="),
                    F.col("IDDOC"),
                    F.lit(" (method: "),
                    F.col("iddoc_extraction_method"),
                    F.lit(")."),
                    F.lit(" gd_doc courant="),
                    F.col("_courant_values"),
                    F.lit("."),
                )
            ),
        ),
    )
    .withColumn(
        "recommended_action",
        F.when(
            F.col("IDDOC").isNull(),
            F.lit("Rename the file to D_IDDOC or Dm_IDDOC format, or delete if obsolete."),
        )
        .when(
            F.col("_max_courant").isNull(),
            F.lit("IDDOC not found in gd_doc. Verify the file naming or remove if obsolete."),
        )
        .when(
            F.col("_max_courant") < 1,
            F.lit("Document archived (courant=0). File can likely be removed or archived."),
        )
        .when(
            F.col("_kb_ref").isNull(),
            F.lit("Document exists in gd_doc but missing from gd_knowledge_base. Check KB ingestion."),
        )
        .when(
            F.col("iddoc_extraction_method") == "FILENAME_RAW_NUMBER",
            F.lit("Verify if the bare number maps to a real IDDOC. Rename to D_IDDOC if so."),
        )
        .otherwise(
            F.lit("Check if the document was archived (courant=0) or removed from the business DB."),
        ),
    )
    .drop("_max_courant", "_courant_values", "_doc_ref", "_doc_titre", "_kb_ref", "_kb_titre")
)

# --- AUDIT C: Rank 1 + NON-STANDARD naming ---
df_edge_cases = (
    df_matched_full.filter(
        (F.col("priority_rank") == 1) & ~F.col("source_file_name").rlike(r"^[dD]m?_")
    )
    .withColumn("audit_type", F.lit("EDGE_CASE"))
    .withColumn("iddoc_in_business_db", F.lit(True))
    .withColumn("file_exists_on_disk", F.lit(True))
    .withColumn("courant_values", F.lit("1"))
    .withColumn(
        "diagnostic_message",
        F.concat(
            F.lit("File '"),
            F.col("source_file_name"),
            F.lit("' "),
            F.lit("SELECTED (rank 1 of "),
            F.col("files_count_for_iddoc"),
            F.lit(") for IDDOC="),
            F.col("IDDOC"),
            F.lit(" via "),
            F.col("iddoc_extraction_method"),
            F.lit(" but name does NOT follow standard D_/Dm_ format. "),
            F.lit("Pattern: "),
            F.col("file_naming_pattern"),
        ),
    )
    .withColumn(
        "root_cause",
        F.when(
            F.col("iddoc_extraction_method") == "FOLDER_D_PREFIX",
            F.lit("FILE_IN_D_FOLDER_BUT_NON_STANDARD_NAME"),
        )
        .when(
            F.col("iddoc_extraction_method") == "FILENAME_RAW_NUMBER",
            F.lit("BARE_NUMBER_NAME_NO_D_PREFIX"),
        )
        .otherwise(F.lit("NON_STANDARD_NAME_OTHER")),
    )
    .withColumn(
        "recommended_action",
        F.lit("Rename the file to D_IDDOC.ext or Dm_IDDOC.ext for compliance."),
    )
)

# --- AUDIT D: Rank 1 + STANDARD naming = fully valid ---
df_valid_files = (
    df_matched_full.filter(
        (F.col("priority_rank") == 1) & F.col("source_file_name").rlike(r"^[dD]m?_")
    )
    .withColumn("audit_type", F.lit("VALID_FILE"))
    .withColumn("iddoc_in_business_db", F.lit(True))
    .withColumn("file_exists_on_disk", F.lit(True))
    .withColumn("courant_values", F.lit("1"))
    .withColumn(
        "diagnostic_message",
        F.concat(
            F.lit("File '"),
            F.col("source_file_name"),
            F.lit("' "),
            F.lit("SELECTED (rank 1 of "),
            F.col("files_count_for_iddoc"),
            F.lit(") for IDDOC="),
            F.col("IDDOC"),
            F.lit(" (ref: "),
            F.coalesce(F.col("ref"), F.lit("?")),
            F.lit("). "),
            F.lit("Standard naming, format: "),
            F.col("source_file_extension"),
            F.lit(" (priority "),
            F.col("ext_priority"),
            F.lit("). No action required."),
        ),
    )
    .withColumn("root_cause", F.lit("NONE"))
    .withColumn("recommended_action", F.lit("No action required."))
)

# --- AUDIT E: Rank > 1 = DEPRIORITIZED ---
df_deprioritized = (
    df_matched_full.filter(F.col("priority_rank") > 1)
    .withColumn("audit_type", F.lit("DEPRIORITIZED_FILE"))
    .withColumn("iddoc_in_business_db", F.lit(True))
    .withColumn("file_exists_on_disk", F.lit(True))
    .withColumn("courant_values", F.lit("1"))
    .withColumn(
        "diagnostic_message",
        F.concat(
            F.lit("File '"),
            F.col("source_file_name"),
            F.lit("' "),
            F.lit("is rank "),
            F.col("priority_rank"),
            F.lit(" of "),
            F.col("files_count_for_iddoc"),
            F.lit(" for IDDOC="),
            F.col("IDDOC"),
            F.lit(". "),
            F.lit("Not selected for parsing. "),
            F.col("depriority_reason"),
        ),
    )
    .withColumn(
        "root_cause",
        F.when(F.col("ext_priority") == 99, F.lit("UNSUPPORTED_FORMAT"))
        .when(
            (F.col("is_dm_file") == 1)
            & (F.col("selected_file_for_iddoc").rlike(r"^[dD]_")),
            F.lit("DM_PREFIX_LOWER_THAN_D"),
        )
        .when(F.col("ext_priority") > F.lit(1), F.lit("FORMAT_LOWER_PRIORITY"))
        .otherwise(F.lit("OLDER_MODIFICATION_DATE")),
    )
    .withColumn(
        "recommended_action",
        F.when(
            F.col("ext_priority") == 99,
            F.lit("This format is not supported for parsing. Convert to a supported format if needed."),
        ).otherwise(
            F.lit("No action required. A higher-priority file was selected for this IDDOC."),
        ),
    )
)

# ------------------------------------------------------------
# STEP 5: UNION ALL AUDITS INTO A SINGLE TABLE
# ------------------------------------------------------------
common_columns = [
    "IDDOC",
    "audit_type",
    "root_cause",
    "diagnostic_message",
    "recommended_action",
    "iddoc_in_business_db",
    "file_exists_on_disk",
    "iddoc_extraction_method",
    "file_naming_pattern",
    "priority_rank",
    "files_count_for_iddoc",
    "selected_file_for_iddoc",
    "depriority_reason",
    "courant_values",
    "source_path",
    "source_file_name",
    "source_file_extension",
    "source_folder_path",
    "source_file_size_bytes",
    "source_modification_time",
    "ref",
    "titre",
    "type_document",
    "categorie",
    "langue",
    "auteur",
    "document_prefixes",
]

df_unified_audit = (
    df_missing_files.select(common_columns)
    .unionByName(df_orphaned_files.select(common_columns))
    .unionByName(df_edge_cases.select(common_columns))
    .unionByName(df_valid_files.select(common_columns))
    .unionByName(df_deprioritized.select(common_columns))
    .withColumn("audit_timestamp", F.current_timestamp())
    .withColumn("ingestion_run_id", F.lit(INGESTION_RUN_ID))
)

df_unified_audit.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(TABLE_UNIFIED_AUDIT)

# --- Summary ---
print("=" * 80)
print(f"UNIFIED AUDIT SUMMARY - Table: {TABLE_UNIFIED_AUDIT}")
print("=" * 80)

df_audit_written = spark.read.table(TABLE_UNIFIED_AUDIT)
df_audit_summary = (
    df_audit_written.groupBy("audit_type", "root_cause")
    .agg(F.count("*").alias("count"))
    .orderBy(
        F.when(F.col("audit_type") == "VALID_FILE", 0)
        .when(F.col("audit_type") == "DEPRIORITIZED_FILE", 1)
        .when(F.col("audit_type") == "EDGE_CASE", 2)
        .when(F.col("audit_type") == "ORPHANED_FILE", 3)
        .otherwise(4),
        F.desc("count"),
    )
)
display(df_audit_summary)

audit_metrics = df_audit_written.agg(
    F.count("*").alias("total"),
    F.sum(F.when(F.col("audit_type") == "VALID_FILE", 1).otherwise(0)).alias("valid"),
    F.sum(F.when(F.col("audit_type") == "DEPRIORITIZED_FILE", 1).otherwise(0)).alias("dedup"),
).collect()[0]

total = int(audit_metrics["total"] or 0)
valid = int(audit_metrics["valid"] or 0)
dedup = int(audit_metrics["dedup"] or 0)
issues = total - valid - dedup
print(f"\nTotal: {total} | Valid: {valid} | Deprioritized: {dedup} | Issues: {issues}")

# ------------------------------------------------------------
# STEP 6: CONDITIONAL STOP FOR AUDIT_ONLY MODE
# ------------------------------------------------------------
if RUN_MODE == "AUDIT_ONLY":
    print("\n" + "=" * 80)
    print("MODE AUDIT_ONLY - Stopping after audit table generation.")
    print(f"   Inspect the table: {TABLE_UNIFIED_AUDIT}")
    print("   Set RUN_MODE = 'FULL' to run the full parsing pipeline.")
    print("=" * 80)
    display(df_audit_written.limit(50))
    df_business_meta.unpersist()
    df_meta_raw.unpersist()
    dbutils.notebook.exit("AUDIT_ONLY completed successfully")

# ------------------------------------------------------------
# STEP 7: FULL MODE - Continue with parsing
# ------------------------------------------------------------
print("\nFULL MODE - Continuing to parsing...")

df_content = df_files_raw.select(F.col("path").alias("source_path"), "content")

df_meta_dedup = (
    df_matched_full.filter((F.col("priority_rank") == 1) & (F.col("ext_priority") < 99)).drop(
        "ext_priority",
        "is_dm_file",
        "priority_rank",
        "files_count_for_iddoc",
        "selected_file_for_iddoc",
        "depriority_reason",
        "extracted_folder_id",
        "extracted_file_id",
        "extracted_raw_number",
    )
)

if LIMIT_TEST_FILES and LIMIT_TEST_FILES > 0:
    print(f"Applying LIMIT_TEST_FILES={LIMIT_TEST_FILES} after rank/format selection.")
    df_meta_final = df_meta_dedup.limit(LIMIT_TEST_FILES)
else:
    print("No file limit applied after rank/format selection.")
    df_meta_final = df_meta_dedup

df_files = df_meta_final.join(df_content, on="source_path", how="inner")
df_files = df_files.withColumn("document_sha256", F.sha2(F.col("content"), 256))

df_business_meta.unpersist()
df_meta_raw.unpersist()

# COMMAND ----------
# ============================================================
# CELL 3: Parsing Logic (Local First)
# ============================================================
optimal_partitions = sc.defaultParallelism * 2
df_files = df_files.repartition(optimal_partitions)

df_local_attempt = (
    df_files.withColumn(
        "local_parse",
        extract_local_text_udf(F.col("content"), F.col("source_file_extension")),
    )
    .withColumn("document_text", F.col("local_parse.text"))
    .withColumn("parser_error", F.col("local_parse.parser_error"))
    .withColumn("parser_strategy", F.col("local_parse.parser_strategy"))
    .withColumn("parse_time_seconds", F.col("local_parse.parse_time_seconds"))
    .drop("local_parse")
    .withColumn(
        "is_local_success",
        F.when(
            (F.col("parser_error").isNull())
            & (F.length(F.trim(F.col("document_text"))) > 0),
            True,
        ).otherwise(False),
    )
)

df_local_attempt.cache()
_ = df_local_attempt.count()

df_local_success = df_local_attempt.filter(F.col("is_local_success") == True).drop("is_local_success")
df_local_fail = df_local_attempt.filter(F.col("is_local_success") == False).drop("is_local_success")

# COMMAND ----------
# ============================================================
# CELL 4: Parsing Logic (AI Fallback)
# ============================================================

# Extensions that ai_parse_document officially supports
AI_PARSE_SUPPORTED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx", "ppt", "pptx"}

# Magic-bytes formats that ai_parse_document can actually handle
AI_PARSEABLE_BINARY_FORMATS = {"pdf", "jpeg", "png", "ole2", "ooxml"}


@F.udf(T.StringType())
def detect_binary_format(content):
    """Detect actual file format from magic bytes to avoid sending
    unsupported formats (e.g. RTF disguised as .doc) to ai_parse_document."""
    if not content or len(content) < 5:
        return "unknown"
    if content[:5] == b"%PDF-":
        return "pdf"
    if content[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if content[:4] == b"\x89PNG":
        return "png"
    if content[:4] == b"\xd0\xcf\x11\xe0":
        return "ole2"  # .doc, .xls, .ppt (OLE2 compound document)
    if content[:4] == b"PK\x03\x04":
        return "ooxml"  # .docx, .xlsx, .pptx (ZIP-based Office Open XML)
    if content.lstrip()[:5] == b"{\\rtf":
        return "rtf"
    return "unknown"


df_ai_step1 = (
    df_local_fail.withColumnRenamed("parser_error", "local_error_trace").drop(
        "document_text", "parser_strategy", "parse_time_seconds"
    )
)


def run_ai_parse_attempt(df_input, attempt_index):
    payload_col = f"ai_parse_payload_{attempt_index}"
    text_col = f"ai_text_{attempt_index}"
    error_col = f"ai_error_{attempt_index}"
    start_col = f"ai_start_{attempt_index}"
    end_col = f"ai_end_{attempt_index}"
    duration_col = f"ai_duration_seconds_{attempt_index}"

    return (
        df_input.withColumn(start_col, F.current_timestamp().cast("double"))
        .withColumn(
            payload_col,
            F.expr("cast(ai_parse_document(content, map('version','2.0')) as string)"),
        )
        .withColumn(end_col, F.current_timestamp().cast("double"))
        .withColumn(text_col, extract_text_from_ai_payload_udf(F.col(payload_col)))
        .withColumn(error_col, F.get_json_object(F.col(payload_col), "$.error_status[0].error_message"))
        .withColumn(duration_col, F.round(F.col(end_col) - F.col(start_col), 2))
    )

if ENABLE_AI_FALLBACK:
    print("WARNING: AI Parsing is ENABLED.")

    # ----- Filter 1: extension must be in supported list -----
    df_ai_ext_ok = df_ai_step1.filter(F.col("source_file_extension").isin(list(AI_PARSE_SUPPORTED_EXTENSIONS)))
    df_ai_ext_ko = df_ai_step1.filter(~F.col("source_file_extension").isin(list(AI_PARSE_SUPPORTED_EXTENSIONS)))

    # ----- Filter 2: magic bytes must match a format ai_parse_document handles -----
    df_ai_ext_ok = df_ai_ext_ok.withColumn("detected_format", detect_binary_format(F.col("content")))

    df_ai_eligible = df_ai_ext_ok.filter(F.col("detected_format").isin(list(AI_PARSEABLE_BINARY_FORMATS)))
    df_ai_format_mismatch = df_ai_ext_ok.filter(~F.col("detected_format").isin(list(AI_PARSEABLE_BINARY_FORMATS)))

    # ----- AI parse on genuinely supported files, with retry on transient AI errors -----
    df_ai_step2 = run_ai_parse_attempt(df_ai_eligible, 1)

    if AI_FALLBACK_MAX_RETRIES > 1:
        retryable_candidates = df_ai_step2.filter(
            F.col("ai_error_1").rlike(AI_RETRYABLE_ERROR_REGEX)
        ).select(*df_ai_eligible.columns)

        df_ai_retry = run_ai_parse_attempt(retryable_candidates, 2).select(
            "source_path",
            F.col("ai_parse_payload_2"),
            F.col("ai_text_2"),
            F.col("ai_error_2"),
            F.col("ai_duration_seconds_2"),
        )

        df_ai_step2 = df_ai_step2.join(F.broadcast(df_ai_retry), on="source_path", how="left")
    else:
        df_ai_step2 = (
            df_ai_step2.withColumn("ai_parse_payload_2", F.lit(None).cast("string"))
            .withColumn("ai_text_2", F.lit(None).cast("string"))
            .withColumn("ai_error_2", F.lit(None).cast("string"))
            .withColumn("ai_duration_seconds_2", F.lit(0.0))
        )

    df_ai_step2 = (
        df_ai_step2.withColumn(
            "use_retry_result",
            (F.col("ai_text_2").isNotNull()) & (F.length(F.trim(F.col("ai_text_2"))) > 0),
        )
        .withColumn(
            "document_text",
            F.when(F.col("use_retry_result"), F.col("ai_text_2")).otherwise(F.col("ai_text_1")),
        )
        .withColumn(
            "ai_error",
            F.when(F.col("use_retry_result"), F.col("ai_error_2")).otherwise(F.col("ai_error_1")),
        )
        .withColumn(
            "ai_attempt_count",
            F.when(F.col("ai_parse_payload_2").isNotNull(), F.lit(2)).otherwise(F.lit(1)),
        )
        .withColumn(
            "parser_strategy",
            F.concat(
                F.lit("ai_parse_fallback:"),
                F.col("source_file_extension"),
                F.lit(":attempts="),
                F.col("ai_attempt_count").cast("string"),
            ),
        )
        .withColumn(
            "parse_time_seconds",
            F.round(
                F.coalesce(F.col("ai_duration_seconds_1"), F.lit(0.0))
                + F.coalesce(F.col("ai_duration_seconds_2"), F.lit(0.0)),
                2,
            ),
        )
    )

    df_part_eligible = (
        df_ai_step2.withColumn(
            "parser_error",
            F.when(
                F.col("ai_error").isNotNull() & (F.col("ai_error") != ""),
                F.concat_ws(" | ", F.lit("Local:"), F.col("local_error_trace"), F.lit("AI:"), F.col("ai_error")),
            )
            .when(
                F.length(F.trim(F.col("document_text"))) == 0,
                F.concat_ws(
                    " | ",
                    F.lit("Local:"),
                    F.col("local_error_trace"),
                    F.lit("AI: EMPTY_TEXT (no text extracted from AI payload)"),
                ),
            )
            .otherwise(F.lit(None).cast("string")),
        ).drop(
            "ai_parse_payload_1",
            "ai_text_1",
            "ai_error_1",
            "ai_duration_seconds_1",
            "ai_parse_payload_2",
            "ai_text_2",
            "ai_error_2",
            "ai_duration_seconds_2",
            "ai_error",
            "use_retry_result",
            "ai_attempt_count",
            "local_error_trace",
            "detected_format",
            "ai_start_1",
            "ai_end_1",
            "ai_start_2",
            "ai_end_2",
        )
    )

    # ----- Format mismatch: .doc that is actually RTF / unknown -----
    df_part_format_mismatch = (
        df_ai_format_mismatch.withColumn("document_text", F.lit(""))
        .withColumn(
            "parser_strategy",
            F.concat(
                F.lit("ai_skipped_format_mismatch:"),
                F.col("source_file_extension"),
                F.lit(":"),
                F.col("detected_format"),
            ),
        )
        .withColumn("parse_time_seconds", F.lit(0.0))
        .withColumn(
            "parser_error",
            F.concat_ws(
                " | ",
                F.lit("Local:"),
                F.col("local_error_trace"),
                F.lit("AI: SKIPPED (magic bytes='"),
                F.col("detected_format"),
                F.lit("' not compatible with ai_parse_document)"),
            ),
        )
        .drop("local_error_trace", "detected_format")
    )

    # ----- Extension not supported at all (xls, xlsx, etc.) -----
    df_part_ext_ko = (
        df_ai_ext_ko.withColumn("document_text", F.lit(""))
        .withColumn(
            "parser_strategy",
            F.concat(F.lit("ai_skipped_unsupported_ext:"), F.col("source_file_extension")),
        )
        .withColumn("parse_time_seconds", F.lit(0.0))
        .withColumn(
            "parser_error",
            F.concat_ws(
                " | ",
                F.lit("Local:"),
                F.col("local_error_trace"),
                F.lit("AI: SKIPPED (extension not supported by ai_parse_document)"),
            ),
        )
        .drop("local_error_trace")
    )

    df_ai_attempt = df_part_eligible.unionByName(
        df_part_format_mismatch, allowMissingColumns=True
    ).unionByName(df_part_ext_ko, allowMissingColumns=True)

else:
    print("AI Parsing is DISABLED. Failed files will be logged for auditing.")
    df_ai_attempt = (
        df_ai_step1.withColumn("document_text", F.lit(""))
        .withColumn(
            "parser_strategy",
            F.concat(F.lit("ai_skipped_for_cost:"), F.col("source_file_extension")),
        )
        .withColumn("parse_time_seconds", F.lit(0.0))
        .withColumn(
            "parser_error",
            F.concat_ws(
                " | ",
                F.lit("Local:"),
                F.col("local_error_trace"),
                F.lit("AI: SKIPPED (ENABLE_AI_FALLBACK=False)"),
            ),
        )
        .drop("local_error_trace")
    )

# COMMAND ----------
# ============================================================
# CELL 5: Union & Final Processing
# ============================================================
df_parsed_all = df_local_success.unionByName(df_ai_attempt, allowMissingColumns=True)

if "url_preview" not in df_parsed_all.columns:
    df_parsed_all = df_parsed_all.withColumn("url_preview", F.lit(None).cast("string"))
if "url" not in df_parsed_all.columns:
    df_parsed_all = df_parsed_all.withColumn("url", F.lit(None).cast("string"))

df_parsed_all = df_parsed_all.withColumn(
    "parse_status",
    F.when(F.col("parser_error").isNotNull(), F.lit("ERROR"))
    .when(F.length(F.trim(F.col("document_text"))) == 0, F.lit("EMPTY_TEXT"))
    .otherwise(F.lit("SUCCESS")),
)

df_parsed_all.cache()
_ = df_parsed_all.count()

# COMMAND ----------
# ============================================================
# CELL 6: Build Final Tables (Processed files & Chunks)
# ============================================================

df_processed_files = (
    df_parsed_all.withColumn("document_char_count", F.length(F.col("document_text")))
    .withColumn(
        "document_token_count",
        F.when(F.col("parse_status") == "SUCCESS", token_count_udf(F.col("document_text"))).otherwise(F.lit(0)),
    )
    .withColumnRenamed("parser_error", "error_trace")
    .select(
        "IDDOC",
        "document_sha256",
        "source_path",
        "source_file_name",
        "source_file_extension",
        "source_folder_path",
        "source_file_size_bytes",
        "source_modification_time",
        # Business metadata from gd_knowledge_base
        "ref",
        "titre",
        "type_document",
        "categorie",
        "langue",
        "auteur",
        "url",
        "url_preview",
        "document_prefixes",
        "ingestion_run_id",
        "ingestion_timestamp",
        "parser_strategy",
        "parse_status",
        "error_trace",
        "parse_time_seconds",
        "document_char_count",
        "document_token_count",
    )
)

df_chunks = (
    df_parsed_all.filter(F.col("parse_status") == "SUCCESS")
    .withColumn(
        "chunks",
        build_chunks_with_limits_udf(
            F.col("document_text"),
            F.lit(CHUNK_SIZE_TOKENS),
            F.lit(CHUNK_OVERLAP_TOKENS),
            F.lit(MIN_CHUNK_TOKENS),
            F.lit(TABLE_CHUNK_MAX_TOKENS),
        ),
    )
    .withColumn("chunk_struct", F.explode(F.col("chunks")))
    # RAG optimization: inject context directly into chunk text
    .withColumn(
        "enriched_chunk_text",
        F.concat(
            F.lit("[Source: "),
            F.coalesce(F.col("ref"), F.lit("N/A")),
            F.lit(" | Title: "),
            F.coalesce(F.col("titre"), F.lit("N/A")),
            F.lit(" | URL: "),
            F.coalesce(F.col("url_preview"), F.col("url"), F.lit("N/A")),
            F.lit("]\n\n"),
            F.col("chunk_struct.chunk_text"),
        ),
    )
    .select(
        F.col("IDDOC"),
        # chunk_id = IDDOC-000001 (readable, unique per chunk)
        F.concat_ws(
            "-",
            F.col("IDDOC").cast("string"),
            F.lpad((F.col("chunk_struct.chunk_index") + F.lit(1)).cast("string"), 6, "0"),
        ).alias("chunk_id"),
        F.col("chunk_struct.chunk_stable_id").alias("chunk_stable_id"),
        F.col("chunk_struct.chunk_index").alias("chunk_index"),
        # Contextually enriched text for the vector database
        F.col("enriched_chunk_text").alias("chunk_text"),
        # REMOVED char_start and char_end here because Header splitter alters text
        F.col("chunk_struct.chunk_char_count").alias("chunk_char_count"),
        F.col("chunk_struct.chunk_token_count").alias("chunk_token_count"),
        F.col("chunk_struct.chunk_content_type").alias("chunk_content_type"),
        # OPTIONAL: Keep semantic headers extracted by Langchain
        F.to_json(F.col("chunk_struct.metadata")).alias("semantic_headers"),
        F.col("url_preview").alias("source_url_preview"),
        # Hash of original unmodified text for data integrity tracking
        F.sha2(F.col("chunk_struct.chunk_text"), 256).alias("chunk_sha256"),
        F.lit("table_aware_recursive_tiktoken").alias("chunking_strategy"),
        F.current_date().alias("partition_date"),
    )
)

# Single pass: count both in one action instead of two separate .count() calls
stats = (
    df_parsed_all.agg(
        F.sum(F.when(F.col("parse_status") == "SUCCESS", 1).otherwise(0)).alias("success_count"),
        F.count("*").alias("total_count"),
    ).collect()[0]
)
print(f"Successfully processed documents: {stats['success_count']} / {stats['total_count']}")
print("Chunks will be generated at write time (lazy evaluation).")

# COMMAND ----------
# ============================================================
# CELL 7: Write Tables with Delta optimizations
# ============================================================

# Enable auto-optimization for smaller, faster writes
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")

(
    df_processed_files.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TARGET_PROCESSED_FILES_TABLE)
)

(
    df_chunks.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .partitionBy("partition_date")
    .saveAsTable(TARGET_CHUNK_TABLE)
)

print(f"Written: {TARGET_PROCESSED_FILES_TABLE}")
print(f"Written: {TARGET_CHUNK_TABLE}")
