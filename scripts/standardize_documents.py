#!/usr/bin/env python3
"""Standardize legal draft documents into one JSON schema per file."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from execution_manifests import (
    ManifestValidationError,
    build_execution_overlay,
    load_active_manifests,
)

ROOT = Path(__file__).resolve().parents[1]
STANDARD_VERSION = "1.1"
VALID_EXECUTION_STATUSES = {"draft", "awaiting_signatures", "signed", "registered"}


def resolve_generated_on() -> str:
    source_date_epoch = os.getenv("SOURCE_DATE_EPOCH")
    if source_date_epoch:
        try:
            timestamp = int(source_date_epoch)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
        except ValueError:
            pass

    # Deterministic fallback for reproducible generated artifacts.
    return "1970-01-01"


GENERATED_ON = resolve_generated_on()


@dataclass(frozen=True)
class MarkdownDocumentConfig:
    id: str
    source: str
    output: str
    stage_date: str
    stage_name: str
    document_type: str
    execution_date: str
    status: str = "draft"


@dataclass(frozen=True)
class LegacyPdfConfig:
    id: str
    source: str
    output: str
    stage_date: str
    stage_name: str
    document_type: str
    execution_date: str
    status: str = "legacy-model"


MARKDOWN_DOCUMENTS: list[MarkdownDocumentConfig] = [
    MarkdownDocumentConfig(
        id="2021-12-16-foundation-and-initial-capitalization-instrument",
        source="src/documents_drafts/2021.12.16 Foundation/Foundation and Initial Capitalization Instrument.md",
        output="src/documents_json/2021-12-16-foundation/foundation-and-initial-capitalization-instrument.json",
        stage_date="2021-12-16",
        stage_name="Foundation",
        document_type="foundation_and_initial_capitalization_instrument",
        execution_date="2021-12-16",
    ),
    MarkdownDocumentConfig(
        id="2022-08-21-equity-purchase-agreement-eliel-rogerio",
        source="src/documents_drafts/2022.08.21 Foundation Realignment/Equity Purchase Agreement - Eliel + Rogério.md",
        output="src/documents_json/2022-08-21-foundation-realignment/equity-purchase-agreement-eliel-rogerio.json",
        stage_date="2022-08-21",
        stage_name="Foundation Realignment",
        document_type="equity_purchase_agreement",
        execution_date="2022-08-21",
    ),
    MarkdownDocumentConfig(
        id="2024-01-09-founders-agreement",
        source="src/documents_drafts/2024.01.09 Founders Agreement/Founders Agreement.md",
        output="src/documents_json/2024-01-09-founders-agreement/founders-agreement.json",
        stage_date="2024-01-09",
        stage_name="Founders Agreement",
        document_type="founders_agreement",
        execution_date="2024-01-09",
        status="legacy-model",
    ),
    MarkdownDocumentConfig(
        id="2025-01-01-founders-agreement-and-ceo-appointment",
        source="src/documents_drafts/2025.01.01 Founders Agreement/Founders Agreement.md",
        output="src/documents_json/2025-01-01-founders-agreement/founders-agreement-and-ceo-appointment.json",
        stage_date="2025-01-01",
        stage_name="Founders Agreement",
        document_type="founders_agreement",
        execution_date="2025-01-01",
    ),
    MarkdownDocumentConfig(
        id="2026-02-01-pool-formation-instrument",
        source="src/documents_drafts/2026.02.01 Pool Formation/Pool Formation.md",
        output="src/documents_json/2026-02-01-pool-formation/pool-formation-instrument.json",
        stage_date="2026-02-01",
        stage_name="Pool Formation",
        document_type="equity_pool_formation_instrument",
        execution_date="2026-02-01",
    ),
    MarkdownDocumentConfig(
        id="2026-02-10-equity-purchase-agreement-eliel-vinicyus",
        source="src/documents_drafts/2026.02.10 Equity Purchase Agreement/Equity Purchase Agreement - Eliel + Vinicyus.md",
        output="src/documents_json/2026-02-10-foundation-realignment/equity-purchase-agreement-eliel-vinicyus.json",
        stage_date="2026-02-10",
        stage_name="Foundation Realignment",
        document_type="equity_purchase_agreement",
        execution_date="2026-02-10",
    ),
    MarkdownDocumentConfig(
        id="2026-02-10-equity-purchase-agreement-rogerio-vinicyus",
        source="src/documents_drafts/2026.02.10 Equity Purchase Agreement/Equity Purchase Agreement - Rogério + Vinicyus.md",
        output="src/documents_json/2026-02-10-foundation-realignment/equity-purchase-agreement-rogerio-vinicyus.json",
        stage_date="2026-02-10",
        stage_name="Foundation Realignment",
        document_type="equity_purchase_agreement",
        execution_date="2026-02-10",
    ),
    MarkdownDocumentConfig(
        id="2026-02-10-performance-equity-agreement-vinicyus",
        source="src/documents_drafts/2026.02.10 Performance Equity Agreement/Performance Equity Agreement.md",
        output="src/documents_json/2026-02-10-foundation-realignment/performance-equity-agreement-vinicyus.json",
        stage_date="2026-02-10",
        stage_name="Foundation Realignment",
        document_type="performance_equity_agreement",
        execution_date="2026-02-10",
    ),
]

LEGACY_PDFS: list[LegacyPdfConfig] = []

ALIGNMENT_ROW_RE = re.compile(r"^[:\-\s]+$")
EMAIL_RE = re.compile(r"\[([^\]]+)\]\(mailto:[^)]+\)", re.IGNORECASE)
TAX_ID_RE = re.compile(r"(?:\d{3}\.\d{3}\.\d{3}-\d{2})|(?:\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}")
CLAUSE_RE = re.compile(r"^(\d+\.\d+)\s+")
EMBEDDED_CLAUSE_RE = re.compile(r"\n\s*(\d+\.\d+)\s+")


def clean_markdown_text(value: str, strip_emphasis: bool = True) -> str:
    text = value or ""
    text = text.replace("\\.", ".").replace("\\+", "+")
    text = text.replace("\\(", "(").replace("\\)", ")")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\[(.*?)\]\([^)]+\)", r"\1", text)
    if strip_emphasis:
        text = text.replace("**", "")
        text = text.replace("*", "")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_rows_from_markdown_table(lines: list[str]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    pending_single_cell: str | None = None

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped.startswith("|"):
            continue

        cell_values = [cell.strip() for cell in stripped.strip("|").split("|")]
        cell_values = [cell for cell in cell_values if cell]

        if not cell_values:
            continue

        if all(ALIGNMENT_ROW_RE.fullmatch(cell) for cell in cell_values):
            continue

        if len(cell_values) >= 2:
            rows.append((cell_values[0], cell_values[1]))
            pending_single_cell = None
            continue

        # Handles broken markdown rows where PT and EN cells are on separate lines.
        if pending_single_cell is None:
            pending_single_cell = cell_values[0]
        else:
            rows.append((pending_single_cell, cell_values[0]))
            pending_single_cell = None

    if pending_single_cell:
        rows.append((pending_single_cell, ""))

    return rows


def extract_heading_info(raw_cell: str) -> dict[str, str | None] | None:
    candidate = raw_cell.strip()
    match = re.match(r"^\*\*(.+?)\*\*(?:\s*<br\s*/?>\s*(.*))?$", candidate, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    heading_raw = clean_markdown_text(match.group(1))
    body_raw = clean_markdown_text(match.group(2) or "")

    ref_match = re.match(r"^(\d+)\.\s*(.+)$", heading_raw)
    if ref_match:
        return {
            "ref": ref_match.group(1),
            "title": ref_match.group(2).strip(),
            "inline_body": body_raw,
        }

    return {
        "ref": None,
        "title": heading_raw,
        "inline_body": body_raw,
    }


def strip_clause_prefix(text: str, reference: str | None) -> str:
    if not reference:
        return text
    return re.sub(rf"^{re.escape(reference)}\s+", "", text).strip()


def split_text_with_embedded_clause_refs(text: str, initial_ref: str) -> list[tuple[str, str]]:
    matches = list(EMBEDDED_CLAUSE_RE.finditer(text))
    if not matches:
        return [(initial_ref, text.strip())]

    chunks: list[tuple[str, str]] = []
    current_ref = initial_ref
    cursor = 0

    for match in matches:
        chunk = text[cursor:match.start()].strip()
        if chunk:
            chunks.append((current_ref, chunk))
        current_ref = match.group(1)
        cursor = match.end()

    tail = text[cursor:].strip()
    if tail:
        chunks.append((current_ref, tail))

    return chunks if chunks else [(initial_ref, text.strip())]


def split_compound_clause(reference: str | None, pt_text: str, en_text: str) -> list[dict[str, Any]]:
    if not reference:
        return [{"ref": None, "pt": pt_text, "en": en_text}]

    pt_chunks = split_text_with_embedded_clause_refs(pt_text, reference)
    en_chunks = split_text_with_embedded_clause_refs(en_text, reference)
    pt_refs = [item[0] for item in pt_chunks]
    en_refs = [item[0] for item in en_chunks]

    if pt_refs != en_refs:
        return [{"ref": reference, "pt": pt_text, "en": en_text}]

    return [
        {
            "ref": clause_ref,
            "pt": pt_clause_text,
            "en": en_clause_text,
        }
        for (clause_ref, pt_clause_text), (_, en_clause_text) in zip(pt_chunks, en_chunks)
    ]


def build_execution_block(status_hint: str) -> dict[str, Any]:
    execution_status = status_hint if status_hint in VALID_EXECUTION_STATUSES else "draft"
    return {
        "status": execution_status,
        "signature_standard": "icp_brasil_qualified",
        "signed_at": None,
        "provider": None,
        "evidence": {
            "sha256": None,
            "validation_report": None,
            "registry_protocol": None,
        },
    }


def parse_parties(header_lines: list[str]) -> list[dict[str, Any]]:
    blocks: list[list[str]] = []
    current_block: list[str] = []

    for line in header_lines:
        trimmed = line.strip()
        if not trimmed:
            if current_block:
                blocks.append(current_block)
                current_block = []
            continue
        if trimmed.startswith("#"):
            continue
        current_block.append(trimmed)

    if current_block:
        blocks.append(current_block)

    parties: list[dict[str, Any]] = []

    for block in blocks:
        name_match = re.match(r"^\*\*(.+?)\*\*$", block[0])
        if not name_match:
            continue

        party: dict[str, Any] = {
            "name": clean_markdown_text(name_match.group(1)),
            "labels": [],
            "notes": [],
        }

        for raw_line in block[1:]:
            line = clean_markdown_text(raw_line)
            if not line:
                continue

            email_match = EMAIL_RE.search(raw_line)
            if email_match:
                party["email"] = email_match.group(1)
                continue

            if TAX_ID_RE.search(line):
                party["tax_id"] = TAX_ID_RE.search(line).group(0)
                continue

            if PHONE_RE.search(line):
                party["phone"] = PHONE_RE.search(line).group(0)
                continue

            if "|" in line:
                left, right = [part.strip() for part in line.split("|", 1)]
                party["labels"].append({"pt": left, "en": right})
                continue

            party["notes"].append(line)

        if not party["labels"]:
            del party["labels"]
        if not party["notes"]:
            del party["notes"]

        parties.append(party)

    return parties


def parse_markdown_document(
    config: MarkdownDocumentConfig,
    execution_overrides: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_path = ROOT / config.source
    content = source_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    title_lines = [clean_markdown_text(line[1:].strip()) for line in lines if line.startswith("# ")]
    title_pt = title_lines[0] if title_lines else ""
    title_en = title_lines[1] if len(title_lines) > 1 else ""

    table_start = None
    for index, line in enumerate(lines):
        if line.lstrip().startswith("|"):
            table_start = index
            break

    if table_start is None:
        raise ValueError(f"No markdown table found in {config.source}")

    parties = parse_parties(lines[:table_start])
    table_rows = split_rows_from_markdown_table(lines[table_start:])

    intro: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    language_rule: dict[str, str] | None = None
    current_section: dict[str, Any] | None = None

    for pt_raw, en_raw in table_rows:
        pt_heading = extract_heading_info(pt_raw)
        en_heading = extract_heading_info(en_raw)

        if pt_heading and en_heading:
            should_open_section = bool(pt_heading["ref"] or en_heading["ref"]) or current_section is None
            if not should_open_section:
                # Some clauses are bolded for emphasis but are not section headers.
                pt_text = clean_markdown_text(pt_raw)
                en_text = clean_markdown_text(en_raw)
                clause = {
                    "ref": None,
                    "pt": pt_text,
                    "en": en_text,
                }
                current_section["clauses"].append(clause)
                continue

            section_ref = pt_heading["ref"] or en_heading["ref"]
            section_entry: dict[str, Any] = {
                "ref": section_ref,
                "title": {
                    "pt": pt_heading["title"],
                    "en": en_heading["title"],
                },
                "clauses": [],
            }
            sections.append(section_entry)
            current_section = section_entry

            inline_pt = pt_heading.get("inline_body") or ""
            inline_en = en_heading.get("inline_body") or ""
            if inline_pt or inline_en:
                section_entry["clauses"].append(
                    {
                        "ref": None,
                        "pt": inline_pt,
                        "en": inline_en,
                    }
                )
            continue

        pt_text = clean_markdown_text(pt_raw)
        en_text = clean_markdown_text(en_raw)

        if not pt_text and not en_text:
            continue

        clause_ref = None
        for candidate in (pt_text, en_text):
            clause_match = CLAUSE_RE.match(candidate)
            if clause_match:
                clause_ref = clause_match.group(1)
                break

        clause = {
            "ref": clause_ref,
            "pt": strip_clause_prefix(pt_text, clause_ref),
            "en": strip_clause_prefix(en_text, clause_ref),
        }

        if not language_rule:
            pt_lower = clause["pt"].lower()
            if "prevalecer" in pt_lower and "portugu" in pt_lower:
                language_rule = {
                    "prevailing_language": "pt-BR",
                    "pt": clause["pt"],
                    "en": clause["en"],
                }

        split_clauses = split_compound_clause(clause["ref"], clause["pt"], clause["en"])

        if current_section is None:
            intro.extend(split_clauses)
        else:
            current_section["clauses"].extend(split_clauses)

    payload = {
        "id": config.id,
        "standard_version": STANDARD_VERSION,
        "meta": {
            "status": config.status,
            "generated_on": GENERATED_ON,
            "source": {
                "path": config.source,
                "format": "markdown",
            },
        },
        "timeline": {
            "stage_date": config.stage_date,
            "stage_name": config.stage_name,
            "execution_date": config.execution_date,
        },
        "document": {
            "type": config.document_type,
            "title": {
                "pt": title_pt,
                "en": title_en,
            },
            "language": {
                "primary": "pt-BR",
                "secondary": "en-US",
                "prevailing": "pt-BR",
            },
        },
        "parties": parties,
        "intro": intro,
        "sections": sections,
        "language_rule": language_rule,
        "execution": build_execution_block(config.status),
    }

    if config.status != "legacy-model" and config.id in execution_overrides:
        payload["execution"] = execution_overrides[config.id]
        payload["meta"]["status"] = execution_overrides[config.id]["status"]

    return payload


def build_legacy_pdf_placeholder(config: LegacyPdfConfig) -> dict[str, Any]:
    filename_title = Path(config.source).stem

    return {
        "id": config.id,
        "standard_version": STANDARD_VERSION,
        "meta": {
            "status": config.status,
            "generated_on": GENERATED_ON,
            "source": {
                "path": config.source,
                "format": "pdf",
            },
            "extraction": {
                "parsed": False,
                "reason": "No PDF text extractor is available in this environment.",
            },
        },
        "timeline": {
            "stage_date": config.stage_date,
            "stage_name": config.stage_name,
            "execution_date": config.execution_date,
        },
        "document": {
            "type": config.document_type,
            "title": {
                "pt": filename_title,
                "en": filename_title,
            },
            "language": {
                "primary": "pt-BR",
                "secondary": "en-US",
                "prevailing": "pt-BR",
            },
        },
        "parties": [],
        "intro": [],
        "sections": [],
        "language_rule": None,
        "execution": build_execution_block(config.status),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    try:
        active_manifests = load_active_manifests(ROOT)
    except ManifestValidationError as exc:
        raise ValueError(f"Execution manifest validation failed:\n{exc}") from exc

    known_active_document_ids = {
        config.id for config in MARKDOWN_DOCUMENTS if config.status != "legacy-model"
    }
    unknown_manifest_documents = sorted(set(active_manifests) - known_active_document_ids)
    if unknown_manifest_documents:
        raise ValueError(
            "active-manifests.json references unknown document ids: "
            + ", ".join(unknown_manifest_documents)
        )

    execution_overrides = {
        document_id: build_execution_overlay(manifest)
        for document_id, manifest in active_manifests.items()
    }

    generated_index: list[dict[str, Any]] = []

    for config in MARKDOWN_DOCUMENTS:
        payload = parse_markdown_document(config, execution_overrides)
        output_path = ROOT / config.output
        write_json(output_path, payload)

        entry_status = config.status
        if config.status != "legacy-model":
            entry_status = payload["execution"]["status"]

        generated_index.append(
            {
                "id": config.id,
                "path": config.output,
                "stage_date": config.stage_date,
                "stage_name": config.stage_name,
                "type": config.document_type,
                "status": entry_status,
                "source": config.source,
            }
        )

    for config in LEGACY_PDFS:
        payload = build_legacy_pdf_placeholder(config)
        output_path = ROOT / config.output
        write_json(output_path, payload)

        generated_index.append(
            {
                "id": config.id,
                "path": config.output,
                "stage_date": config.stage_date,
                "stage_name": config.stage_name,
                "type": config.document_type,
                "status": config.status,
                "source": config.source,
            }
        )

    generated_index.sort(key=lambda item: (item["stage_date"], item["id"]))
    index_path = ROOT / "src/documents_json/index.json"
    index_payload = {
        "standard_version": STANDARD_VERSION,
        "generated_on": GENERATED_ON,
        "documents": generated_index,
    }
    write_json(index_path, index_payload)


if __name__ == "__main__":
    main()
