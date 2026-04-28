import argparse
import json
import logging
import os
import time
from pathlib import Path
from typing import List

# Configurations hors-ligne et desactivation de la telemetrie
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)
logging.getLogger("docling").setLevel(logging.WARNING)

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.chunking import HybridChunker

SCRIPT_DIR = Path(__file__).resolve().parent
OFFLINE_MODELS_DIR = SCRIPT_DIR / "docling_models"

def build_converter() -> DocumentConverter:
    pipeline_opts = PdfPipelineOptions()
    pipeline_opts.artifacts_path = OFFLINE_MODELS_DIR
    pipeline_opts.do_ocr = False
    pipeline_opts.do_table_structure = True
    pipeline_opts.generate_picture_images = True

    # Utilisation de l'unique methode recommandee (docling-parse backend)
    try:
        from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
        backend = DoclingParseDocumentBackend
        logger.info("Utilisation du backend optimise docling-parse")
    except ImportError:
        logger.warning("DoclingParseDocumentBackend non disponible, utilisation du backend par defaut.")
        backend = None

    if backend:
        fmt_option = PdfFormatOption(pipeline_options=pipeline_opts, backend=backend)
    else:
        fmt_option = PdfFormatOption(pipeline_options=pipeline_opts)

    return DocumentConverter(format_options={InputFormat.PDF: fmt_option})

def process_file(source_path: str, results_dir: Path):
    logger.info(f"Traitement du fichier: {source_path}")
    converter = build_converter()
    
    start = time.time()
    result = converter.convert(source_path)
    doc = result.document
    elapsed = time.time() - start
    logger.info(f"Conversion terminee en {elapsed:.2f} secondes.")
    
    # 1. Extraction Markdown
    try:
        from docling_core.types.doc.document import ImageRefMode
        md_text = doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
    except Exception:
        try:
            from docling.datamodel.document import ImageRefMode
            md_text = doc.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
        except Exception:
            md_text = doc.export_to_markdown()

    # 2. Chunking Hybride (respecte structures, tableaux, listes + tailles configurables)
    logger.info("Application du HybridChunker...")
    # Configuration : min_chunk_size et max_chunk_size en tokens
    # tokenizer par defaut = clip, environ 1 token ~= 4 caracteres
    chunker = HybridChunker(
        max_tokens=512,          # ~2048 chars, adapte au RAG
        min_tokens=100,          # Rejette les chunks trop petits (~400 chars)
        merge_peers=True         # Fusionne les chunks similaires
    )
    chunks = list(chunker.chunk(doc))
    logger.info(f"{len(chunks)} chunks structurels generes.")
    
    # Formatage des chunks pour l'export JSON
    chunks_data = []
    for i, chunk in enumerate(chunks):
        chunks_data.append({
            "chunk_id": i,
            "text": chunk.text,
            # Le chunker Docling expose de nombreuses metadonnees (heading, liens...)
            "meta": chunk.meta.export_json_dict() if hasattr(chunk.meta, "export_json_dict") else str(chunk.meta)
        })
        
    # 3. Sauvegarde (Markdown + JSON des chunks + MD des chunks)
    source_name = Path(source_path).stem
    out_dir = results_dir / source_name
    out_dir.mkdir(parents=True, exist_ok=True)
    
    md_file = out_dir / f"{source_name}_full.md"
    md_file.write_text(md_text, encoding="utf-8")
    
    chunks_file = out_dir / f"{source_name}_chunks.json"
    chunks_file.write_text(json.dumps(chunks_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Formatage des chunks en Markdown pour evaluation visuelle
    chunks_md_lines = [f"# Chunks extraits : {source_name}\n"]
    for c_data in chunks_data:
        chunks_md_lines.append(f"## Chunk {c_data['chunk_id']}")
        chunks_md_lines.append(f"**Texte :**\n{c_data['text']}\n")
        chunks_md_lines.append(f"<details><summary><b>Méta-données (cliquer pour dérouler)</b></summary>\n\n```json\n{json.dumps(c_data['meta'], indent=2, ensure_ascii=False)}\n```\n</details>\n")
        chunks_md_lines.append("---\n")
    chunks_md_file = out_dir / f"{source_name}_chunks.md"
    chunks_md_file.write_text("\n".join(chunks_md_lines), encoding="utf-8")
    
    logger.info(f"✔ Resultats sauvegardes dans {out_dir}/")
    logger.info(f"   - {md_file.name} (document complet)")
    logger.info(f"   - {chunks_file.name} (decoupage JSON)")
    logger.info(f"   - {chunks_md_file.name} (decoupage Markdown)")

def main():
    parser = argparse.ArgumentParser(description="Pipeline simplifie Docling (Parsing + Chunking)")
    parser.add_argument("--source", type=str, required=True, help="Chemin vers le fichier PDF a traiter")
    parser.add_argument("--results-dir", type=str, default=str(SCRIPT_DIR / "results"), help="Dossier de destination")
    args = parser.parse_args()
    
    if not os.path.exists(args.source):
        logger.error(f"Fichier introuvable: {args.source}")
        return

    process_file(args.source, Path(args.results_dir))

if __name__ == "__main__":
    main()
