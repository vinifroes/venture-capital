# Legal Execution Guide (ICP-Brasil)

This guide defines the digital legal execution flow for societary instruments in Brazil using **qualified electronic signatures (ICP-Brasil)**.

Operational playbook:

- [`docs/ICP_STAKEHOLDER_FLOW.md`](./ICP_STAKEHOLDER_FLOW.md)

## Scope

Use this process for critical instruments (e.g., shareholders agreements, equity transfers, governance amendments).

## Standard

- Signature class: **qualified**
- Infrastructure: **ICP-Brasil**
- Legal references:
  - MP 2.200-2/2001
  - Lei 14.063/2020
  - CPC art. 784 §4 (digital title enforceability)

## Operational Flow

1. Freeze final document version (preferably PDF/A).
2. Compute SHA-256 hash of final file.
3. Collect qualified signatures (ICP-Brasil) from all required parties.
4. Export audit package from signature provider.
5. Validate signature(s) at ITI VALIDAR.
6. Store evidence package with immutable naming/versioning.
7. Register at Junta/Cartório when applicable by legal counsel.

## Required Evidence Set

For each executed document, store:

- `signed.pdf`
- `sha256.txt`
- `validation-report.pdf` (or equivalent from ITI VALIDAR)
- `signature-manifest.json`
- `registry-proof.pdf` (when there is external registration/protocol)

Recommended folder convention:

`legal_evidence/<document-id>/<version>/`

## Data-State Policy

Execution status lifecycle in JSON:

- `draft`
- `awaiting_signatures`
- `signed`
- `registered`

Rules:

- `signed` requires at least `sha256` and `validation_report`.
- `registered` requires protocol proof (`registry_protocol` and/or `registry-proof.pdf`).

## LGPD Controls

- Repository is currently public by explicit governance decision.
- Evidence publication in git is an explicit risk-accepted mode and must be approved by stakeholders/legal counsel.
- Define retention period and access review cadence.
- Avoid exposing additional personal data beyond what is required for legal execution evidence.

## Compliance Notes

- This repository operationalizes execution evidence tracking.
- Final legal interpretation, enforceability checks, and registry obligations must be validated by qualified legal counsel.
