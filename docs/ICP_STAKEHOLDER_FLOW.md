# ICP Stakeholder Signature Flow

This playbook defines the operational procedure to execute legal documents with ICP-Brasil signatures and keep repository metadata consistent.

## 1) Prepare Final Instrument

1. Freeze legal text and export final file as PDF/A when possible.
2. Save the final file under:
   - `legal_evidence/<document-id>/<version>/signed.pdf`
3. Compute SHA-256:

```bash
sha256sum legal_evidence/<document-id>/<version>/signed.pdf
```

4. Save the hash output in:
   - `legal_evidence/<document-id>/<version>/sha256.txt`

## 2) Send to Stakeholders for ICP-Brasil Signature

1. Upload the final `signed.pdf` to your ICP-Brasil signature platform.
2. Configure all signers and sign order according to counsel instructions.
3. Collect full provider audit package after all signatures are complete.

## 3) Validate Signature Evidence

1. Validate signed file in ITI VALIDAR (or equivalent legal validation flow).
2. Save validation output in:
   - `legal_evidence/<document-id>/<version>/validation-report.pdf`

If formal registry applies:
- Save protocol evidence in:
  - `legal_evidence/<document-id>/<version>/registry-proof.pdf`
- Fill `registry_protocol` in manifest evidence.

## 4) Build Signature Manifest

1. Copy template:
   - `legal_evidence/_templates/signature-manifest.template.json`
2. Save as:
   - `legal_evidence/<document-id>/<version>/signature-manifest.json`
3. Fill fields:
   - `document_id`
   - `execution_status` (`awaiting_signatures`, `signed`, or `registered`)
   - `signature_standard` (`icp_brasil_qualified`)
   - `provider`
   - `signed_at` (ISO-8601 UTC for signed/registered)
   - `evidence.sha256`
   - `evidence.validation_report`
   - `evidence.registry_protocol` (if registered)

## 5) Activate Manifest for JSON Overlay

Update `legal_evidence/active-manifests.json` with the latest active manifest path:

```json
{
  "<document-id>": "legal_evidence/<document-id>/<version>/signature-manifest.json"
}
```

## 6) Validate and Regenerate JSON

Run:

```bash
npm run documents:validate-execution
npm run documents:build
```

Expected:
- validation passes
- corresponding `execution` block in `src/documents_json/**` is updated from manifest
- `src/documents_json/index.json` status reflects current execution state

## 7) Open Pull Request

PR must include:
- evidence files
- manifest file
- `active-manifests.json` update
- regenerated JSON outputs

Commit message format:
- `legal(exec): <document-id> -> <status>`

Manual edits directly in `src/documents_json/*.json` `execution` blocks are not allowed without manifest update.

## 8) Legal Responsibility

- This repository tracks execution metadata and evidence.
- Legal enforceability and registry obligations must be reviewed by qualified legal counsel.
