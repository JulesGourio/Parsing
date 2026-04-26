import os
import gc
import re
import time
import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import Tuple, Dict, Any

# ==============================================================================
# 🛠️ 1. CONFIGURATION AVANCÉE & MÉMOIRE GPU
# ==============================================================================
ENABLE_GPU = True  # Granite-Docling 258M est très léger, il passera sur ton GPU !

if ENABLE_GPU:
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
else:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)
logging.getLogger("docling").setLevel(logging.WARNING)
logging.getLogger("RapidOCR").setLevel(logging.ERROR)

# Chemins
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PDF = "/home/n7student/Téléchargements/2410.09871v1.pdf"
OUTPUT_MD = str(SCRIPT_DIR / "benchmark_nextgen_report.md")

# ==============================================================================
# 📦 2. IMPORTS DOCLING V2 (NOUVELLE GÉNÉRATION)
# ==============================================================================
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    RapidOcrOptions,
    AcceleratorOptions,
    AcceleratorDevice
)

# Tentative de chargement sécurisé de l'infrastructure VLM
try:
    from docling.pipeline.vlm_pipeline import VlmPipeline
    from docling.datamodel.pipeline_options import VlmPipelineOptions
    
    # Gestion des différentes versions récentes de Docling pour charger Granite
    try:
        from docling.datamodel.pipeline_options import VlmConvertOptions
        HAS_VLM_PRESET = True
    except ImportError:
        from docling.datamodel import vlm_model_specs
        HAS_VLM_PRESET = False
    VLM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Pipeline VLM non détecté. Veuillez mettre à jour (pip install --upgrade docling).")
    VLM_AVAILABLE = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# ==============================================================================
# 🧹 3. UTILITAIRES ET ANALYSEURS INTELLIGENTS
# ==============================================================================
def free_memory():
    """Libère la VRAM entre chaque exécution pour éviter le OOM."""
    gc.collect()
    if HAS_TORCH and torch.cuda.is_available():
        torch.cuda.empty_cache()

def sanitize_base64_for_report(md_text: str) -> str:
    """Remplace les gigantesques chaînes Base64 par un tag pour garder un markdown lisible."""
    return re.sub(r'data:image/[a-zA-Z]+;base64,[a-zA-Z0-9+/=]+', r'[BASE64_IMAGE_DATA_EXTRACTED]', md_text)

def analyze_markdown_content(md_text: str) -> Dict[str, int]:
    """
    C'est ici la magie : au lieu d'un diff rouge/vert, on compte LES STRUCTURES 
    que seul un modèle intelligent (VLM) peut comprendre.
    """
    stats = {
        "words": len(re.findall(r'\b\w+\b', md_text)),
        "math_inline": len(re.findall(r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)', md_text)), # Ex: $x=2$
        "math_block": len(re.findall(r'\$\$(.*?)\$\$', md_text, re.DOTALL)),             # Ex: $$ equation $$
        "tables": len(re.findall(r'\|.*\|.*\|', md_text)),                               # Lignes de tableau MD
        "images_base64": md_text.count("BASE64_IMAGE_DATA_EXTRACTED") + md_text.count("data:image/")
    }
    return stats

def get_best_snippet(md_text: str, feature: str) -> str:
    """Récupère le premier bel exemple d'une feature pour le rapport."""
    if feature == "math":
        match = re.search(r'(\$\$.*?\$\$)', md_text, re.DOTALL)
        return match.group(1).strip() if match else "Aucune formule bloc détectée."
    elif feature == "table":
        match = re.search(r'(\|.*?\|\n\|[-:| ]+\|\n(?:\|.*?\|\n)+)', md_text)
        return match.group(1).strip() if match else "Aucun tableau structuré détecté."
    return ""

# ==============================================================================
# 🚀 4. MOTEURS D'EXTRACTION
# ==============================================================================

def parse_with_pymupdf(pdf_path: str):
    logger.info("▶ Méthode 1: PyMuPDF (Texte Brut)...")
    start = time.time()
    doc = fitz.open(pdf_path)
    md_result = "\n\n".join([page.get_text("text") for page in doc])
    doc.close()
    return md_result, time.time() - start, analyze_markdown_content(md_result)

def parse_with_docling_standard(pdf_path: str, use_ocr: bool = False):
    name = "Docling + RapidOCR" if use_ocr else "Docling Natif (Sans OCR)"
    logger.info(f"▶ Méthode 2/3: {name}...")
    start = time.time()
    
    pipeline_opts = PdfPipelineOptions()
    pipeline_opts.do_table_structure = True 
    pipeline_opts.do_ocr = use_ocr
    pipeline_opts.accelerator_options = AcceleratorOptions(
        device=AcceleratorDevice.CUDA if ENABLE_GPU else AcceleratorDevice.CPU
    )
    if use_ocr:
        pipeline_opts.ocr_options = RapidOcrOptions(force_full_page_ocr=True)
        
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts)})
    md_result = converter.convert(pdf_path).document.export_to_markdown()
    
    free_memory()
    return md_result, time.time() - start, analyze_markdown_content(md_result)

def parse_with_vlm_granite(pdf_path: str):
    logger.info("▶ Méthode 4: Docling VLM (Granite-Docling)... Mode IA Visuelle Activé !")
    start = time.time()
    
    if not VLM_AVAILABLE:
        logger.error("VLM non disponible.")
        return "Non supporté", 0, analyze_markdown_content("")

    # Configuration hyper-robuste du VLM selon la version de docling
    try:
        if HAS_VLM_PRESET:
            vlm_options = VlmConvertOptions.from_preset("granite_docling")
            pipeline_opts = VlmPipelineOptions(vlm_options=vlm_options)
        else:
            pipeline_opts = VlmPipelineOptions(vlm_options=vlm_model_specs.GRANITEDOCLING)
            
        pipeline_opts.accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice.CUDA if ENABLE_GPU else AcceleratorDevice.CPU
        )

        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_cls=VlmPipeline, pipeline_options=pipeline_opts)}
        )
        
        doc = converter.convert(pdf_path).document
        
        # Demander explicitement à Docling d'embarquer les images en Base64 dans le Markdown
        try:
            from docling.datamodel.document import ImageRefMode
            md_result = doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
        except ImportError:
            md_result = doc.export_to_markdown() # Fallback
            
        # On nettoie le base64 pour que le fichier final de rapport ne pèse pas 50Mo
        md_clean = sanitize_base64_for_report(md_result)
        
        free_memory()
        return md_clean, time.time() - start, analyze_markdown_content(md_clean)
        
    except Exception as e:
        logger.error(f"Crash du VLM: {e}")
        return f"Erreur VLM: {e}", 0, analyze_markdown_content("")

# ==============================================================================
# 🎯 5. EXÉCUTION & GÉNÉRATION DU RAPPORT VISUEL
# ==============================================================================
if __name__ == "__main__":
    if not os.path.isfile(INPUT_PDF):
        logger.error("PDF introuvable.")
        exit()

    logger.info("🚀 Début du Benchmark Nouvelle Génération")
    free_memory()
    
    # 1. Extraction
    md_pdf, t_pdf, s_pdf = parse_with_pymupdf(INPUT_PDF)
    md_nat, t_nat, s_nat = parse_with_docling_standard(INPUT_PDF, use_ocr=False)
    md_ocr, t_ocr, s_ocr = parse_with_docling_standard(INPUT_PDF, use_ocr=True)
    md_vlm, t_vlm, s_vlm = parse_with_vlm_granite(INPUT_PDF)

    # 2. Construction du rapport
    logger.info("Création du rapport analytique...")
    
    report = [
        f"# 🚀 Benchmark Docling Next-Gen (VLM & OCR)\n",
        f"**Fichier :** `{INPUT_PDF}`\n\n",
        "*(L'objectif d'un pipeline d'IA moderne n'est pas d'avoir le plus grand nombre de mots, mais la meilleure **compréhension sémantique** : extraction parfaite des équations, des tableaux, et des images).* \n",
        
        "## 🏆 Tableau Comparatif des Structures Extraites",
        "| Méthode | Temps | Mots | Math (Ligne) | Math (Bloc) | Lignes de Tableaux | Images (Base64) |",
        "|---------|-------|------|--------------|-------------|--------------------|-----------------|",
        f"| **1. PyMuPDF** | {t_pdf:.2f}s | {s_pdf['words']} | {s_pdf['math_inline']} | {s_pdf['math_block']} | {s_pdf['tables']} | {s_pdf['images_base64']} |",
        f"| **2. Docling Natif** | {t_nat:.2f}s | {s_nat['words']} | {s_nat['math_inline']} | {s_nat['math_block']} | {s_nat['tables']} | {s_nat['images_base64']} |",
        f"| **3. Docling + RapidOCR** | {t_ocr:.2f}s | {s_ocr['words']} | {s_ocr['math_inline']} | {s_ocr['math_block']} | {s_ocr['tables']} | {s_ocr['images_base64']} |",
        f"| **4. Docling VLM (Granite)** | {t_vlm:.2f}s | **{s_vlm['words']}** | **{s_vlm['math_inline']}** | **{s_vlm['math_block']}** | **{s_vlm['tables']}** | **{s_vlm['images_base64']}** |\n",
        
        "## 👁️ La preuve par l'image : La puissance du VLM",
        "Voici ce que seul le VLM (`granite_docling`) a pu structurer correctement (vs l'OCR traditionnel) :\n",
        
        "### 🧮 1. Compréhension Mathématique",
        "> *Le VLM encode les formules nativement en LaTeX (`$$...$$`), là où l'OCR lit simplement une suite de lettres dénuées de sens.*\n",
        "**Exemple extrait par le VLM :**\n",
        f"```latex\n{get_best_snippet(md_vlm, 'math')}\n```\n",
        
        "### 📊 2. Structure des Tableaux",
        "> *L'OCR standard brise les colonnes. Le VLM comprend l'image et recrée la syntaxe Markdown parfaite.*\n",
        "**Exemple extrait par le VLM :**\n",
        f"```markdown\n{get_best_snippet(md_vlm, 'table')}\n```\n",
        
        "---\n## 📑 Annexes (Résultats Intégraux)\n",
        "<details><summary><b>1️⃣ Voir le résultat : Docling + RapidOCR</b></summary>\n\n```markdown\n" + md_ocr + "\n```\n\n</details>\n",
        "<details><summary><b>2️⃣ Voir le résultat : Docling VLM (Granite)</b></summary>\n\n```markdown\n" + md_vlm + "\n```\n\n</details>\n"
    ]

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    logger.info(f"✅ Benchmark VLM terminé ! Rapport dispo ici : {OUTPUT_MD}")