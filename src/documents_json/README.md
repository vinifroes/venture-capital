# Documents JSON Standard

This folder stores one normalized JSON file per legal document for long-term maintenance.

## Regenerate

From the project root:

```bash
npm run documents:build
```

That command reads sources under `src/documents_drafts/` and writes normalized outputs to this folder.

## Interface Integration

- The React interface reads `src/documents_json/index.json` as the source of truth.
- Each `index.json` entry points to one document JSON file under this folder.
- In the UI, documents marked with status `legacy-model` are skipped from timeline navigation.

## Current Source Coverage

- Markdown drafts (`.md`): fully parsed into structured JSON.
- Legacy PDF (`.pdf`): kept as historical source file.
- Legacy Founders Agreement (2024-01-09): maintained as Markdown converted from the legacy PDF model, tagged as `legacy-model`.
- Active timeline stages are covered from 2021-12-16 to 2026-02-10 with stage-specific documents.

## JSON Shape (v1.1)

Each document file follows this top-level structure:

- `id`: stable document id.
- `standard_version`: schema version (`"1.1"`).
- `meta`: generation metadata, source file reference, status.
- `timeline`: stage date/name and execution date.
- `document`: type, bilingual title, language policy.
- `parties`: parsed party list (name, tax id, email, phone, labels).
- `intro`: bilingual clauses before formal numbered sections.
- `sections`: ordered sections with `ref`, bilingual title, and bilingual clauses.
- `language_rule`: prevailing-language statement when detected.
- `execution`: legal digital execution metadata (status, signature standard, evidence pointers).

## Notes

- Portuguese (`pt-BR`) is set as prevailing language.
- If a Markdown table row is split across lines, the generator attempts to auto-repair it.
- The legacy Founders Agreement Markdown preserves authoritative Portuguese text and includes English placeholders pending reviewed translation.
- `generated_on` is deterministic:
  - Uses `SOURCE_DATE_EPOCH` when provided.
  - Falls back to `1970-01-01` for reproducible output.
- The generator script is `scripts/standardize_documents.py`.
