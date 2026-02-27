# Legal Evidence Repository Structure

Use this directory for legal execution evidence bundles, keeping one folder per document and version.

## Structure

```text
legal_evidence/
  <document-id>/
    <version>/
      signed.pdf
      sha256.txt
      validation-report.pdf
      signature-manifest.json
      registry-proof.pdf
```

## Notes

- Real evidence payload files are ignored by `.gitignore`.
- Only templates and this README are tracked in git by default.
- For each signed document, keep evidence synchronized with JSON `execution` metadata fields.

Template manifest:

- [`legal_evidence/_templates/signature-manifest.template.json`](./_templates/signature-manifest.template.json)
