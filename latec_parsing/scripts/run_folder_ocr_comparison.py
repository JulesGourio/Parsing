#!/usr/bin/env python3
"""Run OCR ON/OFF parsing on a directory and generate readable reports.

This script parses every supported file twice:
1) OCR enabled
2) OCR disabled

It then computes quality diagnostics (with extra focus on table reconstruction)
and writes consolidated outputs:
- JSON payload for automation
- Markdown report for quick review
- HTML report for business-friendly browsing
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "test_results" / "ocr_comparison"

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

TABLE_NATIVE_EXTENSIONS = {"xls", "xlsx", "xlsm", "xlsb", "csv", "tsv"}
SEMI_TABLE_EXTENSIONS = {"pdf", "docx", "docm", "pptx", "json", "xml", "html", "htm", "md"}

TABLE_MARKER_RE = re.compile(r"\[TABLE_START\]", re.IGNORECASE)
DIAGRAM_MARKER_RE = re.compile(r"\[DIAGRAM_START\]", re.IGNORECASE)
TABLE_HINT_RE = re.compile(
    r"\b(table|tableau|qte|qty|item|prix|price|total|montant|amount|colonne|column)\b",
    re.IGNORECASE,
)

DEPENDENCY_ERROR_MARKERS = (
    "err_antiword_bin",
    "antiword",
    "utf-8.txt",
    "mapping file",
    "module not found",
    "modulenotfounderror",
    "no module named",
    "command not found",
    "cannot find",
    "is not installed",
    "dependency",
)


def _classify_parser_error(error_text: str) -> str:
    lowered = (error_text or "").strip().lower()
    if not lowered:
        return "none"
    if "timeout" in lowered:
        return "timeout"
    if any(marker in lowered for marker in DEPENDENCY_ERROR_MARKERS):
        return "dependency"
    if lowered.startswith("subprocess_error"):
        return "runtime"
    return "parser"


def _table_check_status(
    extension: str,
    parser_error_kind: str,
    table_markers: int,
    table_hints: int,
) -> Dict[str, str]:
    if extension in TABLE_NATIVE_EXTENSIONS:
        if parser_error_kind not in {"none", "dependency"}:
            return {
                "status": "blocked",
                "expectation": "required",
                "reason": "Tabular format but parser failed before table validation.",
            }
        if table_markers > 0:
            return {
                "status": "pass",
                "expectation": "required",
                "reason": "Expected [TABLE_START] marker found for tabular input.",
            }
        return {
            "status": "fail",
            "expectation": "required",
            "reason": "Tabular format without [TABLE_START] marker.",
        }

    if extension in SEMI_TABLE_EXTENSIONS and table_hints >= 4:
        if parser_error_kind not in {"none", "dependency"}:
            return {
                "status": "blocked",
                "expectation": "hint_based",
                "reason": "Strong table hints present but parser failed before validation.",
            }
        if table_markers > 0:
            return {
                "status": "pass",
                "expectation": "hint_based",
                "reason": "Table hints and table marker detected.",
            }
        return {
            "status": "warn",
            "expectation": "hint_based",
            "reason": "Table hints detected but no [TABLE_START] marker.",
        }

    return {
        "status": "n/a",
        "expectation": "none",
        "reason": "No strong table expectation for this file type.",
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
        ext = _normalize_extension(path)
        if ext in extensions:
            files.append(path)
    files.sort(key=lambda p: str(p).lower())
    return files


def _to_relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def _safe_preview(text: str, max_chars: int = 360) -> str:
    cleaned = (text or "").replace("\r", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[:max_chars]}\n... [truncated]"


def _table_excerpt(text: str, max_lines: int = 22) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return "[empty]"

    hits: List[int] = []
    for index, line in enumerate(lines):
        if TABLE_MARKER_RE.search(line) or TABLE_HINT_RE.search(line):
            hits.append(index)

    if not hits:
        return "\n".join(lines[:max_lines])

    selected = set()
    for hit in hits:
        for idx in range(max(0, hit - 2), min(len(lines), hit + 3)):
            selected.add(idx)

    merged = [lines[idx] for idx in sorted(selected)]
    return "\n".join(merged[:max_lines])


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
            "_stderr": process.stderr[-3000:],
            "_stdout": process.stdout[-3000:],
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
            "_stderr": process.stderr[-3000:],
            "_stdout": process.stdout[-3000:],
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
            "_stderr": process.stderr[-3000:],
            "_stdout": process.stdout[-3000:],
        }


def _compute_text_metrics(result: Dict[str, object]) -> Dict[str, object]:
    text = str(result.get("text") or "")
    table_markers = len(TABLE_MARKER_RE.findall(text))
    diagram_markers = len(DIAGRAM_MARKER_RE.findall(text))
    table_hints = len(TABLE_HINT_RE.findall(text))

    return {
        "chars": len(text),
        "tokens": int(result.get("_token_count") or 0),
        "table_markers": table_markers,
        "diagram_markers": diagram_markers,
        "table_hints": table_hints,
        "empty": len(text.strip()) == 0,
    }


def _evaluate_quality(
    extension: str,
    ocr_on: Dict[str, object],
    ocr_off: Dict[str, object],
    on_metrics: Dict[str, object],
    off_metrics: Dict[str, object],
) -> Dict[str, object]:
    issues: List[str] = []
    warnings: List[str] = []

    on_error = str(ocr_on.get("parser_error") or "").strip()
    off_error = str(ocr_off.get("parser_error") or "").strip()
    on_error_kind = _classify_parser_error(on_error)
    off_error_kind = _classify_parser_error(off_error)

    on_strategy = str(ocr_on.get("parser_strategy") or "")
    on_timeout_partial = "timeout_partial" in on_strategy
    on_ocr_budget_limited = "ocr_attempt_budget:" in on_strategy or "ocr_time_budget_ratio:" in on_strategy

    if on_error:
        if on_error_kind == "dependency":
            warnings.append(f"OCR ON dependency/toolchain issue: {on_error}")
        else:
            issues.append(f"OCR ON parser error: {on_error}")
    if off_error:
        if off_error_kind == "dependency":
            warnings.append(f"OCR OFF dependency/toolchain issue: {off_error}")
        else:
            warnings.append(f"OCR OFF parser error: {off_error}")

    if bool(on_metrics.get("empty")) and not on_error:
        issues.append("OCR ON output is empty")

    on_tables = int(on_metrics.get("table_markers") or 0)
    on_hints = int(on_metrics.get("table_hints") or 0)
    table_check = _table_check_status(extension, on_error_kind, on_tables, on_hints)

    if table_check["status"] == "fail" and on_error_kind in {"none", "dependency"}:
        issues.append(table_check["reason"])
    elif table_check["status"] == "warn":
        warnings.append(table_check["reason"])

    on_chars = int(on_metrics.get("chars") or 0)
    off_chars = int(off_metrics.get("chars") or 0)
    if (
        off_chars > 0
        and on_chars < int(round(off_chars * 0.85))
        and not on_error
        and not on_timeout_partial
    ):
        if on_ocr_budget_limited:
            warnings.append("OCR ON text length lower than OCR OFF (OCR budget limited for performance)")
        else:
            warnings.append("OCR ON text length significantly lower than OCR OFF")

    off_tables = int(off_metrics.get("table_markers") or 0)
    if on_tables < off_tables and not on_timeout_partial:
        if on_ocr_budget_limited:
            warnings.append("OCR ON has fewer table markers than OCR OFF (OCR budget limited for performance)")
        else:
            warnings.append("OCR ON has fewer table markers than OCR OFF")

    severity = "ok"
    if issues:
        severity = "error"
    elif warnings:
        severity = "warning"

    return {
        "severity": severity,
        "issues": issues,
        "warnings": warnings,
        "chars_gain": on_chars - off_chars,
        "table_gain": on_tables - off_tables,
        "on_error_kind": on_error_kind,
        "off_error_kind": off_error_kind,
        "table_check": table_check,
    }


def _format_short_mode_payload(result: Dict[str, object], metrics: Dict[str, object], preview: str) -> Dict[str, object]:
    return {
        "parser_strategy": result.get("parser_strategy"),
        "parser_error": result.get("parser_error"),
        "parse_time_seconds": result.get("parse_time_seconds"),
        "ocr_attempted": result.get("ocr_attempted"),
        "ocr_used": result.get("ocr_used"),
        "ocr_engine_trace": result.get("ocr_engine_trace"),
        "ocr_pages": result.get("ocr_pages"),
        "ocr_supplement_pages": result.get("ocr_supplement_pages"),
        "chars": metrics.get("chars"),
        "tokens": metrics.get("tokens"),
        "table_markers": metrics.get("table_markers"),
        "diagram_markers": metrics.get("diagram_markers"),
        "table_hints": metrics.get("table_hints"),
        "preview": preview,
    }


def _build_markdown_report(payload: Dict[str, object]) -> str:
    run = payload["run"]
    stats = payload["stats"]
    files = payload["files"]
    table_status_counts = {"pass": 0, "warn": 0, "fail": 0, "blocked": 0, "n/a": 0}

    for entry in files:
        status = str(entry["quality"].get("table_check", {}).get("status", "n/a"))
        table_status_counts[status] = table_status_counts.get(status, 0) + 1

    lines: List[str] = []
    lines.append("# OCR ON/OFF Folder Parsing Report")
    lines.append("")
    lines.append(f"- Generated at: {run['generated_at']}")
    lines.append(f"- Input directory: {run['input_dir']}")
    lines.append(f"- Supported extensions: {', '.join(run['extensions'])}")
    lines.append(f"- Total files: {stats['total_files']}")
    lines.append(f"- Files with errors: {stats['error_files']}")
    lines.append(f"- Files with warnings: {stats['warning_files']}")
    lines.append(f"- Files with dependency/toolchain issues: {stats['dependency_issue_files']}")
    lines.append(f"- OCR ON parsed with ocr_used=True: {stats['ocr_used_files']}")
    lines.append(f"- Files with table marker improvement (ON > OFF): {stats['table_gain_files']}")
    lines.append("")

    lines.append("## Priority Findings")
    lines.append("")
    findings_count = 0
    for entry in files:
        quality = entry["quality"]
        issues = quality["issues"]
        warnings = quality["warnings"]
        if not issues and not warnings:
            continue

        findings_count += 1
        severity = quality["severity"].upper()
        lines.append(f"### [{severity}] {entry['relative_path']}")
        lines.append("")
        if issues:
            lines.append("Issues:")
            for issue in issues:
                lines.append(f"- {issue}")
        if warnings:
            lines.append("Warnings:")
            for warning in warnings:
                lines.append(f"- {warning}")
        lines.append("")
        if findings_count >= 30:
            lines.append("- Additional findings exist in JSON/HTML reports.")
            lines.append("")
            break

    if findings_count == 0:
        lines.append("No critical findings detected. Residual risk remains for files without explicit table markers but with weak tabular hints.")
        lines.append("")

    lines.append("## Table Quality Overview")
    lines.append("")
    lines.append(f"- Table check pass: {table_status_counts.get('pass', 0)}")
    lines.append(f"- Table check warn: {table_status_counts.get('warn', 0)}")
    lines.append(f"- Table check fail: {table_status_counts.get('fail', 0)}")
    lines.append(f"- Table check blocked: {table_status_counts.get('blocked', 0)}")
    lines.append(f"- Table check n/a: {table_status_counts.get('n/a', 0)}")
    lines.append("")

    lines.append("## File Summary")
    lines.append("")
    lines.append("| File | Ext | Severity | Table Check | OCR Used | Chars ON | Chars OFF | Table Gain |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|")
    for entry in files:
        lines.append(
            "| {path} | {ext} | {sev} | {table_check} | {ocr_used} | {on_chars} | {off_chars} | {table_gain} |".format(
                path=entry["relative_path"],
                ext=entry["extension"],
                sev=entry["quality"]["severity"],
                table_check=entry["quality"].get("table_check", {}).get("status", "n/a"),
                ocr_used="yes" if entry["ocr_on"]["ocr_used"] else "no",
                on_chars=entry["ocr_on"]["chars"],
                off_chars=entry["ocr_off"]["chars"],
                table_gain=entry["quality"]["table_gain"],
            )
        )
    lines.append("")

    lines.append("## Per-file Details")
    lines.append("")
    for entry in files:
        lines.append(f"### {entry['relative_path']}")
        lines.append("")
        lines.append(f"- Extension: {entry['extension']}")
        lines.append(f"- Size bytes: {entry['size_bytes']}")
        lines.append(f"- Quality severity: {entry['quality']['severity']}")
        lines.append(f"- Chars gain (ON - OFF): {entry['quality']['chars_gain']}")
        lines.append(f"- Table gain (ON - OFF): {entry['quality']['table_gain']}")
        lines.append(f"- OCR ON error kind: {entry['quality']['on_error_kind']}")
        lines.append(f"- OCR OFF error kind: {entry['quality']['off_error_kind']}")
        lines.append(f"- Table check status: {entry['quality']['table_check']['status']}")
        lines.append(f"- Table check reason: {entry['quality']['table_check']['reason']}")
        lines.append("")
        lines.append("OCR ON preview:")
        lines.append("")
        lines.append("```text")
        lines.append(entry["ocr_on"]["preview"])
        lines.append("```")
        lines.append("")
        lines.append("OCR OFF preview:")
        lines.append("")
        lines.append("```text")
        lines.append(entry["ocr_off"]["preview"])
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def _html_escape(value: object) -> str:
    return html.escape(str(value if value is not None else ""))


def _build_html_report(payload: Dict[str, object]) -> str:
    run = payload["run"]
    stats = payload["stats"]
    files = payload["files"]
    table_status_counts = {"pass": 0, "warn": 0, "fail": 0, "blocked": 0, "n/a": 0}

    for entry in files:
        status = str(entry["quality"].get("table_check", {}).get("status", "n/a"))
        table_status_counts[status] = table_status_counts.get(status, 0) + 1

    top_findings = [entry for entry in files if entry["quality"]["severity"] != "ok"][:8]
    top_finding_items = []
    for entry in top_findings:
        notes = list(entry["quality"].get("issues") or []) + list(entry["quality"].get("warnings") or [])
        note = notes[0] if notes else "Review details"
        top_finding_items.append(
            "<li><strong>{path}</strong> ({sev}) - {note}</li>".format(
                path=_html_escape(entry["relative_path"]),
                sev=_html_escape(entry["quality"]["severity"]),
                note=_html_escape(note),
            )
        )

    top_finding_html = "".join(top_finding_items) if top_finding_items else "<li>No critical finding in this run.</li>"

    rows = []
    for entry in files:
        severity = entry["quality"]["severity"]
        table_check = entry["quality"].get("table_check", {}).get("status", "n/a")
        cls = f"sev-{severity}"
        rows.append(
            "<tr class='{cls}'>"
            "<td>{path}</td>"
            "<td>{ext}</td>"
            "<td>{severity}</td>"
            "<td>{table_check}</td>"
            "<td>{ocr_used}</td>"
            "<td>{on_chars}</td>"
            "<td>{off_chars}</td>"
            "<td>{chars_gain}</td>"
            "<td>{table_gain}</td>"
            "<td>{issues}</td>"
            "<td>{warnings}</td>"
            "</tr>".format(
                cls=_html_escape(cls),
                path=_html_escape(entry["relative_path"]),
                ext=_html_escape(entry["extension"]),
                severity=_html_escape(severity),
                table_check=_html_escape(table_check),
                ocr_used="yes" if entry["ocr_on"]["ocr_used"] else "no",
                on_chars=_html_escape(entry["ocr_on"]["chars"]),
                off_chars=_html_escape(entry["ocr_off"]["chars"]),
                chars_gain=_html_escape(entry["quality"]["chars_gain"]),
                table_gain=_html_escape(entry["quality"]["table_gain"]),
                issues=_html_escape(" | ".join(entry["quality"]["issues"]) or "-"),
                warnings=_html_escape(" | ".join(entry["quality"]["warnings"]) or "-"),
            )
        )

    details_blocks = []
    for entry in files:
        details_blocks.append(
            "<details><summary>{path} ({sev})</summary>"
            "<p><strong>Table check:</strong> {table_check} - {table_reason}</p>"
            "<div class='detail-grid'>"
            "<div><h4>OCR ON</h4><pre>{on_preview}</pre></div>"
            "<div><h4>OCR OFF</h4><pre>{off_preview}</pre></div>"
            "</div>"
            "</details>".format(
                path=_html_escape(entry["relative_path"]),
                sev=_html_escape(entry["quality"]["severity"]),
                table_check=_html_escape(entry["quality"].get("table_check", {}).get("status", "n/a")),
                table_reason=_html_escape(entry["quality"].get("table_check", {}).get("reason", "")),
                on_preview=_html_escape(entry["ocr_on"]["preview"]),
                off_preview=_html_escape(entry["ocr_off"]["preview"]),
            )
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OCR ON/OFF Folder Parsing Report</title>
  <style>
    :root {{
      --bg: #f6f7f4;
      --panel: #ffffff;
      --ink: #1a1f1d;
      --muted: #5a6763;
      --ok: #1f7a4c;
      --warn: #9a6b00;
      --err: #b42318;
      --line: #d9dfdc;
      --accent: #0b5d8f;
    }}
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background: linear-gradient(165deg, #f7f9f5 0%, #eef2ec 100%);
      color: var(--ink);
    }}
    .wrap {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 4px 14px rgba(17, 24, 39, 0.06);
      margin-bottom: 16px;
    }}
    h1, h2 {{ margin: 0 0 10px 0; }}
    .meta {{ color: var(--muted); font-size: 0.95rem; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }}
    .stat {{ background: #f8fbfd; border: 1px solid var(--line); border-radius: 10px; padding: 12px; }}
    .stat .k {{ color: var(--muted); font-size: 0.85rem; }}
    .stat .v {{ font-size: 1.4rem; font-weight: 700; }}
    ul.top {{ margin: 6px 0 0 18px; }}
    ul.top li {{ margin: 4px 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ border: 1px solid var(--line); padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf3f8; }}
    .sev-ok td:nth-child(3) {{ color: var(--ok); font-weight: 700; }}
    .sev-warning td:nth-child(3) {{ color: var(--warn); font-weight: 700; }}
    .sev-error td:nth-child(3) {{ color: var(--err); font-weight: 700; }}
    details {{ border: 1px solid var(--line); border-radius: 10px; padding: 10px; margin-bottom: 10px; background: #fff; }}
    summary {{ cursor: pointer; font-weight: 700; color: var(--accent); }}
    .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }}
    pre {{ white-space: pre-wrap; background: #f8f8f8; border: 1px solid var(--line); border-radius: 8px; padding: 8px; max-height: 280px; overflow: auto; }}
    @media (max-width: 900px) {{
      .detail-grid {{ grid-template-columns: 1fr; }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="card">
      <h1>OCR ON/OFF Folder Parsing Report</h1>
      <p class="meta">Generated at: {_html_escape(run['generated_at'])}</p>
      <p class="meta">Input: {_html_escape(run['input_dir'])}</p>
      <p class="meta">Extensions: {_html_escape(', '.join(run['extensions']))}</p>
    </section>

    <section class="card">
      <h2>Summary</h2>
      <div class="stats">
        <div class="stat"><div class="k">Total files</div><div class="v">{_html_escape(stats['total_files'])}</div></div>
        <div class="stat"><div class="k">Error files</div><div class="v">{_html_escape(stats['error_files'])}</div></div>
        <div class="stat"><div class="k">Warning files</div><div class="v">{_html_escape(stats['warning_files'])}</div></div>
                <div class="stat"><div class="k">Dependency issues</div><div class="v">{_html_escape(stats['dependency_issue_files'])}</div></div>
        <div class="stat"><div class="k">OCR used files</div><div class="v">{_html_escape(stats['ocr_used_files'])}</div></div>
        <div class="stat"><div class="k">Table gain files</div><div class="v">{_html_escape(stats['table_gain_files'])}</div></div>
      </div>
    </section>

        <section class="card">
            <h2>Executive Focus</h2>
            <p class="meta">Top findings to investigate first:</p>
            <ul class="top">{top_finding_html}</ul>
            <p class="meta">Table checks - pass: {_html_escape(table_status_counts.get('pass', 0))}, warn: {_html_escape(table_status_counts.get('warn', 0))}, fail: {_html_escape(table_status_counts.get('fail', 0))}, blocked: {_html_escape(table_status_counts.get('blocked', 0))}.</p>
        </section>

    <section class="card">
      <h2>File Matrix</h2>
      <table>
        <thead>
          <tr>
            <th>File</th>
            <th>Ext</th>
            <th>Severity</th>
            <th>Table check</th>
            <th>OCR used</th>
            <th>Chars ON</th>
            <th>Chars OFF</th>
            <th>Chars gain</th>
            <th>Table gain</th>
            <th>Issues</th>
            <th>Warnings</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </section>

    <section class="card">
      <h2>Per-file previews</h2>
      {''.join(details_blocks)}
    </section>
  </div>
</body>
</html>
"""


def _build_index_markdown(output_dir: Path) -> str:
    return "\n".join(
        [
            "# OCR Comparison Outputs",
            "",
            "Primary files generated by run_folder_ocr_comparison.py:",
            "",
            "- [comparison_report.html](comparison_report.html)",
            "- [comparison_report.md](comparison_report.md)",
            "- [comparison_results.json](comparison_results.json)",
            "",
            "Recommended entry point: open comparison_report.html in a browser.",
        ]
    )


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OCR ON/OFF parsing on a folder and generate reports.")
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
    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="Delete output directory before writing new files",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_arguments()

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory not found or not a directory: {input_dir}")

    extensions = {
        ext.strip().lower().lstrip(".")
        for ext in str(args.extensions).split(",")
        if ext.strip()
    }
    if not extensions:
        raise SystemExit("No extension provided")

    output_dir = Path(args.output_dir).resolve()
    if args.clean_output and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = _collect_input_files(input_dir, extensions)
    if not files:
        raise SystemExit(f"No supported files found in: {input_dir}")

    entries: List[Dict[str, object]] = []

    for index, file_path in enumerate(files, start=1):
        extension = _normalize_extension(file_path)
        print(f"[{index}/{len(files)}] Parsing {file_path.name} ({extension})")

        on_result = _run_single_parse(file_path, extension, ocr_enabled=True)
        off_result = _run_single_parse(file_path, extension, ocr_enabled=False)

        on_metrics = _compute_text_metrics(on_result)
        off_metrics = _compute_text_metrics(off_result)

        quality = _evaluate_quality(extension, on_result, off_result, on_metrics, off_metrics)

        on_text = str(on_result.get("text") or "")
        off_text = str(off_result.get("text") or "")

        entry = {
            "relative_path": _to_relative(file_path),
            "extension": extension,
            "size_bytes": file_path.stat().st_size,
            "ocr_on": _format_short_mode_payload(on_result, on_metrics, _table_excerpt(on_text)),
            "ocr_off": _format_short_mode_payload(off_result, off_metrics, _table_excerpt(off_text)),
            "quality": quality,
        }
        entries.append(entry)

    total_files = len(entries)
    error_files = sum(1 for item in entries if item["quality"]["severity"] == "error")
    warning_files = sum(1 for item in entries if item["quality"]["severity"] == "warning")
    ocr_used_files = sum(1 for item in entries if bool(item["ocr_on"].get("ocr_used")))
    table_gain_files = sum(1 for item in entries if int(item["quality"].get("table_gain") or 0) > 0)
    dependency_issue_files = sum(
        1
        for item in entries
        if item["quality"].get("on_error_kind") == "dependency"
        or item["quality"].get("off_error_kind") == "dependency"
    )

    payload: Dict[str, object] = {
        "run": {
            "generated_at": _utc_now_iso(),
            "input_dir": _to_relative(input_dir),
            "extensions": sorted(extensions),
        },
        "stats": {
            "total_files": total_files,
            "error_files": error_files,
            "warning_files": warning_files,
            "ocr_used_files": ocr_used_files,
            "table_gain_files": table_gain_files,
            "dependency_issue_files": dependency_issue_files,
        },
        "files": entries,
    }

    json_path = output_dir / "comparison_results.json"
    md_path = output_dir / "comparison_report.md"
    html_path = output_dir / "comparison_report.html"
    index_path = output_dir / "README.md"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_build_markdown_report(payload), encoding="utf-8")
    html_path.write_text(_build_html_report(payload), encoding="utf-8")
    index_path.write_text(_build_index_markdown(output_dir), encoding="utf-8")

    print("\nGenerated outputs:")
    print(f"- {_to_relative(index_path)}")
    print(f"- {_to_relative(html_path)}")
    print(f"- {_to_relative(md_path)}")
    print(f"- {_to_relative(json_path)}")


if __name__ == "__main__":
    main()