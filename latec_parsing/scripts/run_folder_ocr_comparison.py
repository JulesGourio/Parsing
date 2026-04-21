#!/usr/bin/env python3
"""Run OCR ON/OFF evaluation on a folder with full-text and full-chunk outputs.

This script parses each supported file twice:
1) OCR ON
2) OCR OFF

It then chunks both full texts and writes complete integral artifacts:
- full_results.json (full text + full chunk payload per file)
- chunks_ocr_on.jsonl / chunks_ocr_off.jsonl (flat chunk-level datasets)
- documents_ocr_on/*.txt / documents_ocr_off/*.txt (full extracted text)
- full_report.md (human-readable full report)
- full_report.html (browser view with full texts/chunks)
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

from parsing_core.chunking import split_text_to_chunks

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "test_results" / "ocr_full_evaluation"

SUPPORTED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "docm",
    "xls",
    "xlsx",
    "xlsm",
    "xlsb",
    "pptx",
    "txt",
    "html",
    "htm",
    "xml",
    "md",
    "csv",
    "json",
    "tsv",
    "rtf",
    "png",
    "jpg",
    "jpeg",
    "tif",
    "tiff",
    "bmp",
    "webp",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_extension(path: Path) -> str:
    suffix = path.suffix.lower().strip()
    return suffix[1:] if suffix.startswith(".") else suffix


def _collect_input_files(input_dir: Path, extensions: set[str]) -> List[Path]:
    files: List[Path] = []
    for path in input_dir.rglob("*"):
        if not path.is_file():
            continue
        if _normalize_extension(path) in extensions:
            files.append(path)
    files.sort(key=lambda item: str(item).lower())
    return files


def _to_relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def _run_single_parse(path: Path, extension: str, ocr_enabled: bool) -> Dict[str, object]:
    code = textwrap.dedent(
        """
        import json
        import pathlib
        import sys

        from parsing_core.extractors import extract_text_locally
        from parsing_core.text_utils import count_tokens

        file_path = pathlib.Path(sys.argv[1])
        file_ext = sys.argv[2]

        result = extract_text_locally(file_path.read_bytes(), file_ext)
        result["_token_count"] = count_tokens(str(result.get("text") or ""))
        print(json.dumps(result, ensure_ascii=False))
        """
    )

    env = os.environ.copy()
    env["OCR_ENABLED"] = "1" if ocr_enabled else "0"
    env["OCR_PDF_FALLBACK_ENABLED"] = "1" if ocr_enabled else "0"

    process = subprocess.run(
        [sys.executable, "-c", code, str(path), extension],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if process.returncode != 0:
        return {
            "text": "",
            "parser_error": f"SUBPROCESS_ERROR: return_code={process.returncode}",
            "parser_strategy": "subprocess",
            "parse_time_seconds": 0.0,
            "ocr_attempted": bool(ocr_enabled),
            "ocr_used": False,
            "ocr_engine_trace": None,
            "ocr_pages": 0,
            "ocr_supplement_pages": 0,
            "_token_count": 0,
            "_stderr": process.stderr[-5000:],
            "_stdout": process.stdout[-5000:],
        }

    lines = [line for line in process.stdout.splitlines() if line.strip()]
    if not lines:
        return {
            "text": "",
            "parser_error": "SUBPROCESS_EMPTY_OUTPUT",
            "parser_strategy": "subprocess",
            "parse_time_seconds": 0.0,
            "ocr_attempted": bool(ocr_enabled),
            "ocr_used": False,
            "ocr_engine_trace": None,
            "ocr_pages": 0,
            "ocr_supplement_pages": 0,
            "_token_count": 0,
            "_stderr": process.stderr[-5000:],
            "_stdout": process.stdout[-5000:],
        }

    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {
            "text": "",
            "parser_error": "SUBPROCESS_JSON_DECODE_ERROR",
            "parser_strategy": "subprocess",
            "parse_time_seconds": 0.0,
            "ocr_attempted": bool(ocr_enabled),
            "ocr_used": False,
            "ocr_engine_trace": None,
            "ocr_pages": 0,
            "ocr_supplement_pages": 0,
            "_token_count": 0,
            "_stderr": process.stderr[-5000:],
            "_stdout": process.stdout[-5000:],
        }


def _build_chunks_payload(
    text: str,
    chunk_size_tokens: int,
    chunk_overlap_tokens: int,
    min_chunk_tokens: int,
    max_chunk_tokens: int,
) -> List[Dict[str, object]]:
    max_limit = max_chunk_tokens if max_chunk_tokens > 0 else None
    chunks = split_text_to_chunks(
        text=text,
        chunk_size_tokens=chunk_size_tokens,
        chunk_overlap_tokens=chunk_overlap_tokens,
        min_chunk_tokens=min_chunk_tokens,
        max_chunk_tokens=max_limit,
    )
    formatted: List[Dict[str, object]] = []
    for chunk in chunks:
        formatted.append(
            {
                "chunk_index": int(chunk.get("chunk_index") or 0),
                "chunk_stable_id": chunk.get("chunk_stable_id"),
                "chunk_content_type": chunk.get("chunk_content_type"),
                "chunk_char_count": int(chunk.get("chunk_char_count") or 0),
                "chunk_token_count": int(chunk.get("chunk_token_count") or 0),
                "metadata": chunk.get("metadata") or {},
                "chunk_text": str(chunk.get("chunk_text") or ""),
            }
        )
    return formatted


def _base_mode_payload(result: Dict[str, object], chunks: List[Dict[str, object]]) -> Dict[str, object]:
    text_value = str(result.get("text") or "")
    return {
        "parser_strategy": result.get("parser_strategy"),
        "parser_error": result.get("parser_error"),
        "parse_time_seconds": result.get("parse_time_seconds"),
        "ocr_attempted": result.get("ocr_attempted"),
        "ocr_used": result.get("ocr_used"),
        "ocr_engine_trace": result.get("ocr_engine_trace"),
        "ocr_pages": result.get("ocr_pages"),
        "ocr_supplement_pages": result.get("ocr_supplement_pages"),
        "text": text_value,
        "text_char_count": len(text_value),
        "text_token_count": int(result.get("_token_count") or 0),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def _write_full_text_file(base_dir: Path, relative_path: str, text: str) -> Path:
    target = base_dir / Path(relative_path)
    target = target.with_suffix(target.suffix + ".txt") if target.suffix else Path(str(target) + ".txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def _flatten_chunks_for_jsonl(file_entry: Dict[str, object], mode: str) -> Iterable[Dict[str, object]]:
    mode_payload = file_entry[mode]
    for chunk in mode_payload["chunks"]:
        yield {
            "file": file_entry["relative_path"],
            "extension": file_entry["extension"],
            "size_bytes": file_entry["size_bytes"],
            "mode": "ocr_on" if mode == "ocr_on" else "ocr_off",
            "chunk_index": chunk["chunk_index"],
            "chunk_stable_id": chunk["chunk_stable_id"],
            "chunk_content_type": chunk["chunk_content_type"],
            "chunk_char_count": chunk["chunk_char_count"],
            "chunk_token_count": chunk["chunk_token_count"],
            "metadata": chunk["metadata"],
            "chunk_text": chunk["chunk_text"],
        }


def _html_escape(value: object) -> str:
    return html.escape(str(value if value is not None else ""))


def _build_html_chunks(chunks: List[Dict[str, object]]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(
            "<details class='chunk'><summary>"
            f"Chunk #{_html_escape(chunk['chunk_index'])} | "
            f"tokens={_html_escape(chunk['chunk_token_count'])} | "
            f"chars={_html_escape(chunk['chunk_char_count'])} | "
            f"type={_html_escape(chunk['chunk_content_type'])}"
            "</summary>"
            f"<pre>{_html_escape(chunk['chunk_text'])}</pre>"
            "</details>"
        )
    return "".join(blocks) if blocks else "<p>No chunks generated.</p>"


def _build_html_report(payload: Dict[str, object]) -> str:
    run = payload["run"]
    stats = payload["stats"]
    files = payload["files"]

    summary_rows = []
    for item in files:
        summary_rows.append(
            "<tr>"
            f"<td>{_html_escape(item['relative_path'])}</td>"
            f"<td>{_html_escape(item['extension'])}</td>"
            f"<td>{_html_escape(item['ocr_on']['text_char_count'])}</td>"
            f"<td>{_html_escape(item['ocr_off']['text_char_count'])}</td>"
            f"<td>{_html_escape(item['ocr_on']['chunk_count'])}</td>"
            f"<td>{_html_escape(item['ocr_off']['chunk_count'])}</td>"
            f"<td>{'yes' if item['ocr_on']['ocr_used'] else 'no'}</td>"
            "</tr>"
        )

    detail_blocks = []
    for item in files:
        detail_blocks.append(
            "<section class='file'>"
            f"<h3>{_html_escape(item['relative_path'])}</h3>"
            "<div class='meta'>"
            f"<p><strong>Extension:</strong> {_html_escape(item['extension'])}</p>"
            f"<p><strong>Size bytes:</strong> {_html_escape(item['size_bytes'])}</p>"
            "</div>"
            "<div class='split'>"
            "<div class='panel'>"
            "<h4>OCR ON - full document text</h4>"
            f"<pre>{_html_escape(item['ocr_on']['text'])}</pre>"
            "<h4>OCR ON - full chunk list</h4>"
            f"{_build_html_chunks(item['ocr_on']['chunks'])}"
            "</div>"
            "<div class='panel'>"
            "<h4>OCR OFF - full document text</h4>"
            f"<pre>{_html_escape(item['ocr_off']['text'])}</pre>"
            "<h4>OCR OFF - full chunk list</h4>"
            f"{_build_html_chunks(item['ocr_off']['chunks'])}"
            "</div>"
            "</div>"
            "</section>"
        )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>OCR Full Evaluation</title>
  <style>
    :root {{
      --bg: #f5f6f3;
      --ink: #1b2320;
      --line: #d7ddd9;
      --panel: #ffffff;
      --accent: #0b5d8f;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    }}
    .wrap {{ max-width: 1440px; margin: 0 auto; padding: 20px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px; margin-bottom: 16px; }}
    h1, h2, h3, h4 {{ margin: 0 0 10px 0; }}
    .meta p {{ margin: 4px 0; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid var(--line); padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #ecf3f8; }}
    .split {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .panel {{ border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: #fff; }}
    pre {{ white-space: pre-wrap; background: #f8f8f8; border: 1px solid var(--line); border-radius: 6px; padding: 10px; overflow-wrap: anywhere; }}
    details.chunk {{ margin-bottom: 8px; border: 1px solid var(--line); border-radius: 6px; padding: 8px; background: #fcfcfc; }}
    summary {{ cursor: pointer; color: var(--accent); font-weight: 600; }}
    @media (max-width: 980px) {{
      .split {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"card\">
      <h1>OCR Full Evaluation Report</h1>
      <p><strong>Generated at:</strong> {_html_escape(run['generated_at'])}</p>
      <p><strong>Input directory:</strong> {_html_escape(run['input_dir'])}</p>
      <p><strong>Extensions:</strong> {_html_escape(', '.join(run['extensions']))}</p>
      <p><strong>Chunk config:</strong> size={_html_escape(run['chunk_size_tokens'])}, overlap={_html_escape(run['chunk_overlap_tokens'])}, min={_html_escape(run['min_chunk_tokens'])}, max={_html_escape(run['max_chunk_tokens'])}</p>
    </section>

    <section class=\"card\">
      <h2>Global stats</h2>
      <ul>
        <li>Total files: {_html_escape(stats['total_files'])}</li>
        <li>OCR used files (ON mode): {_html_escape(stats['ocr_used_files'])}</li>
        <li>Total chunks OCR ON: {_html_escape(stats['total_chunks_ocr_on'])}</li>
        <li>Total chunks OCR OFF: {_html_escape(stats['total_chunks_ocr_off'])}</li>
      </ul>
    </section>

    <section class=\"card\">
      <h2>File summary</h2>
      <table>
        <thead>
          <tr>
            <th>File</th>
            <th>Ext</th>
            <th>Chars ON</th>
            <th>Chars OFF</th>
            <th>Chunks ON</th>
            <th>Chunks OFF</th>
            <th>OCR used</th>
          </tr>
        </thead>
        <tbody>
          {''.join(summary_rows)}
        </tbody>
      </table>
    </section>

    <section class=\"card\">
      <h2>Per-file full output</h2>
      {''.join(detail_blocks)}
    </section>
  </div>
</body>
</html>
"""


def _build_markdown_report(payload: Dict[str, object]) -> str:
    run = payload["run"]
    stats = payload["stats"]
    files = payload["files"]

    lines: List[str] = []
    lines.append("# OCR Full Evaluation Report")
    lines.append("")
    lines.append(f"- Generated at: {run['generated_at']}")
    lines.append(f"- Input directory: {run['input_dir']}")
    lines.append(f"- Extensions: {', '.join(run['extensions'])}")
    lines.append(
        "- Chunk config: size={size}, overlap={overlap}, min={min_tokens}, max={max_tokens}".format(
            size=run["chunk_size_tokens"],
            overlap=run["chunk_overlap_tokens"],
            min_tokens=run["min_chunk_tokens"],
            max_tokens=run["max_chunk_tokens"],
        )
    )
    lines.append("")
    lines.append("## Stats")
    lines.append("")
    lines.append(f"- Total files: {stats['total_files']}")
    lines.append(f"- OCR used files (ON mode): {stats['ocr_used_files']}")
    lines.append(f"- Total chunks OCR ON: {stats['total_chunks_ocr_on']}")
    lines.append(f"- Total chunks OCR OFF: {stats['total_chunks_ocr_off']}")
    lines.append("")

    for file_entry in files:
        lines.append(f"## {file_entry['relative_path']}")
        lines.append("")
        lines.append(f"- Extension: {file_entry['extension']}")
        lines.append(f"- Size bytes: {file_entry['size_bytes']}")
        lines.append(f"- OCR ON chars: {file_entry['ocr_on']['text_char_count']}")
        lines.append(f"- OCR OFF chars: {file_entry['ocr_off']['text_char_count']}")
        lines.append(f"- OCR ON chunks: {file_entry['ocr_on']['chunk_count']}")
        lines.append(f"- OCR OFF chunks: {file_entry['ocr_off']['chunk_count']}")
        lines.append("")

        lines.append("### OCR ON - full document text")
        lines.append("")
        lines.append("```text")
        lines.append(file_entry["ocr_on"]["text"])
        lines.append("```")
        lines.append("")

        lines.append("### OCR ON - full chunks")
        lines.append("")
        for chunk in file_entry["ocr_on"]["chunks"]:
            lines.append(
                "- chunk_index={index} token_count={tokens} char_count={chars} content_type={content_type}".format(
                    index=chunk["chunk_index"],
                    tokens=chunk["chunk_token_count"],
                    chars=chunk["chunk_char_count"],
                    content_type=chunk["chunk_content_type"],
                )
            )
            lines.append("```text")
            lines.append(chunk["chunk_text"])
            lines.append("```")
        lines.append("")

        lines.append("### OCR OFF - full document text")
        lines.append("")
        lines.append("```text")
        lines.append(file_entry["ocr_off"]["text"])
        lines.append("```")
        lines.append("")

        lines.append("### OCR OFF - full chunks")
        lines.append("")
        for chunk in file_entry["ocr_off"]["chunks"]:
            lines.append(
                "- chunk_index={index} token_count={tokens} char_count={chars} content_type={content_type}".format(
                    index=chunk["chunk_index"],
                    tokens=chunk["chunk_token_count"],
                    chars=chunk["chunk_char_count"],
                    content_type=chunk["chunk_content_type"],
                )
            )
            lines.append("```text")
            lines.append(chunk["chunk_text"])
            lines.append("```")
        lines.append("")

    return "\n".join(lines)


def _build_index_markdown() -> str:
    return "\n".join(
        [
            "# OCR Full Evaluation Outputs",
            "",
            "Generated artifacts:",
            "",
            "- full_report.html: browser view with full text/chunks for OCR ON and OCR OFF",
            "- full_report.md: markdown integral dump",
            "- full_results.json: complete structured payload (per-file full text + full chunks)",
            "- chunks_ocr_on.jsonl: flat chunk dataset for OCR ON",
            "- chunks_ocr_off.jsonl: flat chunk dataset for OCR OFF",
            "- documents_ocr_on/: one full text file per source document",
            "- documents_ocr_off/: one full text file per source document",
            "",
            "Suggested default for downstream processing: full_results.json + chunks_ocr_on.jsonl/chunks_ocr_off.jsonl.",
        ]
    )


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full OCR ON/OFF evaluation on a folder")
    parser.add_argument("input_dir", help="Folder to parse recursively")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--extensions",
        default=",".join(sorted(SUPPORTED_EXTENSIONS)),
        help="Comma-separated extensions to include",
    )
    parser.add_argument("--clean-output", action="store_true", help="Delete output directory before writing")
    parser.add_argument("--chunk-size-tokens", type=int, default=600)
    parser.add_argument("--chunk-overlap-tokens", type=int, default=120)
    parser.add_argument("--min-chunk-tokens", type=int, default=80)
    parser.add_argument("--max-chunk-tokens", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = _parse_arguments()

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory not found or not a directory: {input_dir}")

    extensions = {ext.strip().lower().lstrip(".") for ext in str(args.extensions).split(",") if ext.strip()}
    if not extensions:
        raise SystemExit("No extension provided")

    output_dir = Path(args.output_dir).resolve()
    if args.clean_output and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = _collect_input_files(input_dir, extensions)
    if not files:
        raise SystemExit(f"No supported files found in: {input_dir}")

    docs_on_dir = output_dir / "documents_ocr_on"
    docs_off_dir = output_dir / "documents_ocr_off"
    docs_on_dir.mkdir(parents=True, exist_ok=True)
    docs_off_dir.mkdir(parents=True, exist_ok=True)

    entries: List[Dict[str, object]] = []

    for idx, file_path in enumerate(files, start=1):
        ext = _normalize_extension(file_path)
        print(f"[{idx}/{len(files)}] Parsing {file_path.name} ({ext})")

        on_result = _run_single_parse(file_path, ext, ocr_enabled=True)
        off_result = _run_single_parse(file_path, ext, ocr_enabled=False)

        on_text = str(on_result.get("text") or "")
        off_text = str(off_result.get("text") or "")

        on_chunks = _build_chunks_payload(
            text=on_text,
            chunk_size_tokens=args.chunk_size_tokens,
            chunk_overlap_tokens=args.chunk_overlap_tokens,
            min_chunk_tokens=args.min_chunk_tokens,
            max_chunk_tokens=args.max_chunk_tokens,
        )
        off_chunks = _build_chunks_payload(
            text=off_text,
            chunk_size_tokens=args.chunk_size_tokens,
            chunk_overlap_tokens=args.chunk_overlap_tokens,
            min_chunk_tokens=args.min_chunk_tokens,
            max_chunk_tokens=args.max_chunk_tokens,
        )

        rel_path = _to_relative(file_path)
        on_text_path = _write_full_text_file(docs_on_dir, rel_path, on_text)
        off_text_path = _write_full_text_file(docs_off_dir, rel_path, off_text)

        entry = {
            "relative_path": rel_path,
            "extension": ext,
            "size_bytes": file_path.stat().st_size,
            "ocr_on_text_file": _to_relative(on_text_path),
            "ocr_off_text_file": _to_relative(off_text_path),
            "ocr_on": _base_mode_payload(on_result, on_chunks),
            "ocr_off": _base_mode_payload(off_result, off_chunks),
        }
        entries.append(entry)

    stats = {
        "total_files": len(entries),
        "ocr_used_files": sum(1 for item in entries if bool(item["ocr_on"].get("ocr_used"))),
        "total_chunks_ocr_on": sum(int(item["ocr_on"].get("chunk_count") or 0) for item in entries),
        "total_chunks_ocr_off": sum(int(item["ocr_off"].get("chunk_count") or 0) for item in entries),
    }

    payload: Dict[str, object] = {
        "run": {
            "generated_at": _utc_now_iso(),
            "input_dir": _to_relative(input_dir),
            "extensions": sorted(extensions),
            "chunk_size_tokens": int(args.chunk_size_tokens),
            "chunk_overlap_tokens": int(args.chunk_overlap_tokens),
            "min_chunk_tokens": int(args.min_chunk_tokens),
            "max_chunk_tokens": int(args.max_chunk_tokens),
        },
        "stats": stats,
        "files": entries,
    }

    json_path = output_dir / "full_results.json"
    md_path = output_dir / "full_report.md"
    html_path = output_dir / "full_report.html"
    chunks_on_path = output_dir / "chunks_ocr_on.jsonl"
    chunks_off_path = output_dir / "chunks_ocr_off.jsonl"
    index_path = output_dir / "README.md"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_build_markdown_report(payload), encoding="utf-8")
    html_path.write_text(_build_html_report(payload), encoding="utf-8")
    index_path.write_text(_build_index_markdown(), encoding="utf-8")

    with chunks_on_path.open("w", encoding="utf-8") as handle_on, chunks_off_path.open("w", encoding="utf-8") as handle_off:
        for item in entries:
            for row in _flatten_chunks_for_jsonl(item, "ocr_on"):
                handle_on.write(json.dumps(row, ensure_ascii=False) + "\n")
            for row in _flatten_chunks_for_jsonl(item, "ocr_off"):
                handle_off.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("\nGenerated outputs:")
    print(f"- {_to_relative(index_path)}")
    print(f"- {_to_relative(html_path)}")
    print(f"- {_to_relative(md_path)}")
    print(f"- {_to_relative(json_path)}")
    print(f"- {_to_relative(chunks_on_path)}")
    print(f"- {_to_relative(chunks_off_path)}")
    print(f"- {_to_relative(docs_on_dir)}")
    print(f"- {_to_relative(docs_off_dir)}")


if __name__ == "__main__":
    main()
