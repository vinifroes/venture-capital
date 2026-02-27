#!/usr/bin/env python3
"""Shared helpers for execution manifest loading and validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

VALID_EXECUTION_STATUSES = {"draft", "awaiting_signatures", "signed", "registered"}
ACTIVE_MANIFESTS_FILE = "legal_evidence/active-manifests.json"
EXPECTED_SIGNATURE_STANDARD = "icp_brasil_qualified"
SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class ManifestValidationError(Exception):
    """Raised when execution manifests are malformed."""


def _resolve_relative_path(root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_non_empty_string(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return None


def _validate_manifest(
    root: Path,
    document_id: str,
    manifest_path: Path,
    payload: Any,
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []

    if not isinstance(payload, dict):
        return None, [f"{manifest_path}: manifest must be a JSON object"]

    payload_document_id = _as_non_empty_string(payload.get("document_id"))
    if payload_document_id != document_id:
        errors.append(
            f"{manifest_path}: document_id must match mapping key '{document_id}'"
        )

    execution_status = _as_non_empty_string(payload.get("execution_status"))
    if execution_status not in VALID_EXECUTION_STATUSES:
        errors.append(
            f"{manifest_path}: execution_status must be one of {sorted(VALID_EXECUTION_STATUSES)}"
        )

    signature_standard = _as_non_empty_string(payload.get("signature_standard"))
    if signature_standard != EXPECTED_SIGNATURE_STANDARD:
        errors.append(
            f"{manifest_path}: signature_standard must be '{EXPECTED_SIGNATURE_STANDARD}'"
        )

    provider = _as_non_empty_string(payload.get("provider"))
    signed_at = _as_non_empty_string(payload.get("signed_at"))
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict):
        errors.append(f"{manifest_path}: evidence must be a JSON object")
        evidence = {}

    sha256 = _as_non_empty_string(evidence.get("sha256"))
    if sha256 and not SHA256_HEX_RE.fullmatch(sha256):
        errors.append(f"{manifest_path}: evidence.sha256 must be a 64-char hex string")

    validation_report = _as_non_empty_string(evidence.get("validation_report"))
    if validation_report:
        validation_report_path = _resolve_relative_path(root, validation_report)
        if not validation_report_path.exists():
            errors.append(
                f"{manifest_path}: evidence.validation_report file not found: {validation_report}"
            )

    registry_protocol = _as_non_empty_string(evidence.get("registry_protocol"))
    registry_proof_file = manifest_path.parent / "registry-proof.pdf"
    if execution_status in {"signed", "registered"}:
        if not sha256:
            errors.append(f"{manifest_path}: signed/registered manifest requires evidence.sha256")
        if not validation_report:
            errors.append(
                f"{manifest_path}: signed/registered manifest requires evidence.validation_report"
            )
        if not provider:
            errors.append(f"{manifest_path}: signed/registered manifest requires provider")
        if not signed_at:
            errors.append(f"{manifest_path}: signed/registered manifest requires signed_at")

    if execution_status == "awaiting_signatures" and not provider:
        errors.append(f"{manifest_path}: awaiting_signatures manifest requires provider")

    if execution_status == "registered":
        if not registry_protocol and not registry_proof_file.exists():
            errors.append(
                f"{manifest_path}: registered manifest requires evidence.registry_protocol or registry-proof.pdf"
            )

    if errors:
        return None, errors

    normalized_manifest: dict[str, Any] = {
        "document_id": document_id,
        "execution_status": execution_status,
        "signature_standard": EXPECTED_SIGNATURE_STANDARD,
        "provider": provider,
        "signed_at": signed_at,
        "evidence": {
            "sha256": sha256,
            "validation_report": validation_report,
            "registry_protocol": registry_protocol,
        },
    }
    return normalized_manifest, []


def load_active_manifests(root: Path) -> dict[str, dict[str, Any]]:
    active_manifests_path = root / ACTIVE_MANIFESTS_FILE
    if not active_manifests_path.exists():
        return {}

    raw_index = _load_json(active_manifests_path)
    if not isinstance(raw_index, dict):
        raise ManifestValidationError(
            f"{active_manifests_path}: active-manifests.json must be a JSON object mapping document_id to manifest path"
        )

    errors: list[str] = []
    manifests: dict[str, dict[str, Any]] = {}

    for raw_document_id, raw_manifest_rel_path in raw_index.items():
        document_id = _as_non_empty_string(raw_document_id)
        if not document_id:
            errors.append(
                f"{active_manifests_path}: document_id keys must be non-empty strings"
            )
            continue

        manifest_rel_path = _as_non_empty_string(raw_manifest_rel_path)
        if not manifest_rel_path:
            errors.append(
                f"{active_manifests_path}: document '{document_id}' must map to a non-empty manifest path"
            )
            continue

        manifest_path = _resolve_relative_path(root, manifest_rel_path)
        if not manifest_path.exists():
            errors.append(
                f"{active_manifests_path}: manifest path not found for '{document_id}': {manifest_rel_path}"
            )
            continue

        try:
            manifest_payload = _load_json(manifest_path)
        except json.JSONDecodeError as exc:
            errors.append(f"{manifest_path}: invalid JSON ({exc.msg})")
            continue

        normalized_manifest, manifest_errors = _validate_manifest(
            root=root,
            document_id=document_id,
            manifest_path=manifest_path,
            payload=manifest_payload,
        )
        if manifest_errors:
            errors.extend(manifest_errors)
            continue

        manifests[document_id] = normalized_manifest

    if errors:
        raise ManifestValidationError("\n".join(errors))

    return manifests


def build_execution_overlay(manifest: dict[str, Any]) -> dict[str, Any]:
    evidence = manifest["evidence"]
    return {
        "status": manifest["execution_status"],
        "signature_standard": manifest["signature_standard"],
        "signed_at": manifest.get("signed_at"),
        "provider": manifest.get("provider"),
        "evidence": {
            "sha256": evidence.get("sha256"),
            "validation_report": evidence.get("validation_report"),
            "registry_protocol": evidence.get("registry_protocol"),
        },
    }
