import os
import time
import difflib
import fitz  # PyMuPDF
from pathlib import Path

# Docling imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    AcceleratorOptions,
    AcceleratorDevice
)

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PDF = "/home/n7student/Téléchargements/2410.09871v1.pdf"
OUTPUT_MD = str(SCRIPT_DIR / "benchmark_comparison.md")
OFFLINE_MODELS_DIR = "/home/n7student/Bureau/IA/Parsing/docling/docling_models"
METHOD3_FORCE_FULL_PAGE_OCR = True


def resolve_easyocr_models_dir(models_path: str | None) -> str | None:
    if not models_path:
        return None

    easyocr_path = Path(models_path) / "EasyOcr"
    if easyocr_path.is_dir():
        return str(easyocr_path)

    return None


def compare_markdown_outputs(native_md: str, ocr_md: str) -> dict:
    native_lines = native_md.splitlines()
    ocr_lines = ocr_md.splitlines()
    matcher = difflib.SequenceMatcher(None, native_lines, ocr_lines)

    added_lines = 0
    removed_lines = 0
    changed_blocks = 0
    ocr_added_lines = []
    native_removed_lines = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        changed_blocks += 1
        if tag in ("insert", "replace"):
            added_lines += j2 - j1
            ocr_added_lines.extend(ocr_lines[j1:j2])
        if tag in ("delete", "replace"):
            removed_lines += i2 - i1
            native_removed_lines.extend(native_lines[i1:i2])

    native_line_set = {line.strip() for line in native_lines if line.strip()}
    ocr_only_samples = []
    for line in ocr_lines:
        normalized = line.strip()
        if normalized and normalized not in native_line_set:
            ocr_only_samples.append(normalized)
        if len(ocr_only_samples) >= 5:
            break

    return {
        "is_identical": native_md == ocr_md,
        "similarity_ratio": difflib.SequenceMatcher(None, native_md, ocr_md).ratio(),
        "changed_blocks": changed_blocks,
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "ocr_only_samples": ocr_only_samples,
        "ocr_added_lines": ocr_added_lines,
        "native_removed_lines": native_removed_lines,
    }


def format_diff_lines_for_markdown(lines: list[str], empty_label: str) -> str:
    if not lines:
        return "Aucune ligne."

    formatted = []
    for idx, line in enumerate(lines, start=1):
        value = line if line else empty_label
        formatted.append(f"{idx:04d} | {value}")

    return "\n".join(formatted)

# ==============================================================================
# PARSING METHODS
# ==============================================================================

def parse_with_pymupdf(pdf_path: str) -> tuple[str, float]:
    print("[INFO] Running Method 1: PyMuPDF (Classical)...")
    start_time = time.time()
    
    try:
        doc = fitz.open(pdf_path)
        text_content = [page.get_text("text") for page in doc]
        doc.close()
        md_result = "\n\n".join(text_content)
    except Exception as e:
        md_result = f"Erreur lors de l'extraction PyMuPDF : {e}"
        
    elapsed_time = time.time() - start_time
    return md_result, elapsed_time


def parse_with_docling_native(pdf_path: str, models_path: str = None) -> tuple[str, float]:
    print("[INFO] Running Method 2: Docling Native (Layout only, No OCR)...")
    start_time = time.time()
    
    try:
        pipeline_options = PdfPipelineOptions()
        if models_path and os.path.exists(models_path):
            pipeline_options.artifacts_path = models_path
            
        pipeline_options.do_ocr = False  
        pipeline_options.do_table_structure = True 
        
        doc_converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
        
        conv_result = doc_converter.convert(pdf_path)
        md_result = conv_result.document.export_to_markdown()
    except Exception as e:
        md_result = f"Erreur lors de l'extraction Docling Natif : {e}"
        
    elapsed_time = time.time() - start_time
    return md_result, elapsed_time


def parse_with_docling_easyocr(
    pdf_path: str,
    models_path: str = None,
    force_full_page_ocr: bool = METHOD3_FORCE_FULL_PAGE_OCR,
) -> tuple[str, float]:
    print("[INFO] Running Method 3: Docling + EasyOCR...")
    start_time = time.time()
    
    try:
        pipeline_options = PdfPipelineOptions()
        if models_path and os.path.exists(models_path):
            pipeline_options.artifacts_path = models_path
            
        pipeline_options.do_ocr = True 
        pipeline_options.do_table_structure = True 
        
        # Configuration CPU sécurisée
        pipeline_options.accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice.CPU
        )

        easyocr_models_dir = resolve_easyocr_models_dir(models_path)
        ocr_options_kwargs = {
            "lang": ["fr", "en"],
            "force_full_page_ocr": force_full_page_ocr,
            "bitmap_area_threshold": 0.0 if force_full_page_ocr else 0.05,
            "confidence_threshold": 0.3,
        }
        if easyocr_models_dir:
            ocr_options_kwargs["model_storage_directory"] = easyocr_models_dir
            ocr_options_kwargs["download_enabled"] = False

        pipeline_options.ocr_options = EasyOcrOptions(**ocr_options_kwargs)
        print(
            "[INFO] EasyOCR config: "
            f"full_page={ocr_options_kwargs['force_full_page_ocr']}, "
            f"bitmap_area_threshold={ocr_options_kwargs['bitmap_area_threshold']}, "
            f"model_dir={easyocr_models_dir or 'default_cache'}"
        )
        
        doc_converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
        
        conv_result = doc_converter.convert(pdf_path)
        md_result = conv_result.document.export_to_markdown()
    except Exception as e:
        md_result = f"Erreur lors de l'extraction Docling EasyOCR : {e}"
        
    elapsed_time = time.time() - start_time
    return md_result, elapsed_time

# ==============================================================================
# MAIN EXECUTION & REPORT GENERATION
# ==============================================================================
if __name__ == "__main__":
    if not os.path.isfile(INPUT_PDF):
        print(f"[ERROR] PDF not found: {INPUT_PDF}")
        exit(1)

    print(f"🚀 Starting Benchmark for: {INPUT_PDF}\n")

    # 1. Exécution des trois méthodes
    md_pymupdf, time_pymupdf = parse_with_pymupdf(INPUT_PDF)
    md_docling_native, time_docling_native = parse_with_docling_native(INPUT_PDF, OFFLINE_MODELS_DIR)
    md_docling_ocr, time_docling_ocr = parse_with_docling_easyocr(INPUT_PDF, OFFLINE_MODELS_DIR)
    comparison_2_vs_3 = compare_markdown_outputs(md_docling_native, md_docling_ocr)

    print(
        "[INFO] Méthode 2 vs 3 | "
        f"identique={comparison_2_vs_3['is_identical']} | "
        f"similarité={comparison_2_vs_3['similarity_ratio']:.4f} | "
        f"blocs_modifiés={comparison_2_vs_3['changed_blocks']}"
    )

    ocr_samples = comparison_2_vs_3["ocr_only_samples"]
    if ocr_samples:
        ocr_samples_md = "\n".join([f"  - {sample}" for sample in ocr_samples])
    else:
        ocr_samples_md = "  - (Aucune ligne spécifique OCR détectée)"

    ocr_added_lines_md = format_diff_lines_for_markdown(
        comparison_2_vs_3["ocr_added_lines"],
        empty_label="[LIGNE_VIDE]",
    )
    native_removed_lines_md = format_diff_lines_for_markdown(
        comparison_2_vs_3["native_removed_lines"],
        empty_label="[LIGNE_VIDE]",
    )

    # 2. Construction propre et sécurisée du Markdown (sans f-strings multilingnes problématiques)
    report_lines = [
        "# 📊 Rapport de Benchmark de Parsing PDF pour RAG\n",
        f"**Fichier source :** `{INPUT_PDF}`\n",
        "| Méthode | Temps d'exécution | Idéal pour... |",
        "|---------|-------------------|---------------|",
        f"| **1. PyMuPDF (Classique)** | {time_pymupdf:.2f} secondes | Extraction massive de texte simple. |",
        f"| **2. Docling (Natif)** | {time_docling_native:.2f} secondes | PDF avec tableaux complexes. |",
        f"| **3. Docling + EasyOCR** | {time_docling_ocr:.2f} secondes | Scans, schémas, factures. |\n",
        "## 🧪 Contrôle OCR (Méthode 2 vs Méthode 3)",
        f"- Sortie strictement identique : **{comparison_2_vs_3['is_identical']}**",
        f"- Similarité globale : **{comparison_2_vs_3['similarity_ratio']:.4f}**",
        f"- Blocs modifiés : **{comparison_2_vs_3['changed_blocks']}**",
        f"- Lignes ajoutées (OCR) : **{comparison_2_vs_3['added_lines']}**",
        f"- Lignes retirées : **{comparison_2_vs_3['removed_lines']}**",
        "- Exemples de lignes présentes uniquement avec OCR :",
        ocr_samples_md + "\n",
        "### ➕ Diff complet : lignes ajoutées par OCR (Méthode 3 - Méthode 2)",
        "```text\n" + ocr_added_lines_md + "\n```\n",
        "### ➖ Diff complet : lignes retirées vs OCR (Méthode 2 - Méthode 3)",
        "```text\n" + native_removed_lines_md + "\n```\n",
        "---\n",
        "## 🔍 Partie 1 : Résultat PyMuPDF (Extraction Classique)",
        "*Notez comment les tableaux sont généralement détruits en une liste de mots empilés.*\n",
        "```text\n" + md_pymupdf + "\n```\n",
        "---\n",
        "## 📐 Partie 2 : Résultat Docling Natif (Sans OCR)",
        "*Notez la conservation des titres et le formatage parfait des tableaux en Markdown.*\n",
        md_docling_native + "\n",
        "---\n",
        "## 🤖 Partie 3 : Résultat Docling + EasyOCR",
        "*Identique à la partie 2, mais inclut le texte extrait des images et des zones scannées.*\n",
        md_docling_ocr + "\n"
    ]

    # 3. Écriture dans le fichier de sortie
    try:
        with open(OUTPUT_MD, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        print(f"\n✅ Benchmark terminé avec succès ! Rapport écrit dans : {OUTPUT_MD}")
    except Exception as e:
        print(f"\n❌ Erreur lors de l'écriture du fichier Markdown : {e}")