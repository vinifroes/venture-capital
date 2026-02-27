# Legal Evidence Repository Structure

Use this directory for legal execution evidence bundles, keeping one folder per document and version.

## Structure

```text
legal_evidence/
  active-manifests.json
  <document-id>/
    <version>/
      signed.pdf
      sha256.txt
      validation-report.pdf
      signature-manifest.json
      registry-proof.pdf
```

## Notes

- Evidence payload files are versioned in git by repository policy.
- `active-manifests.json` maps each active `document_id` to its current manifest path.
- For each signed document, keep evidence synchronized with JSON `execution` metadata fields.

Template manifest:

- [`legal_evidence/_templates/signature-manifest.template.json`](./_templates/signature-manifest.template.json)
