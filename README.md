# Cap Table Legal Workspace

React + Vite application to navigate legal documents by company stage, with Markdown drafts normalized into structured JSON.

## Stack

- Frontend: React 19 + Vite
- Document pipeline: Python script (`scripts/standardize_documents.py`)
- CI/CD: GitHub Actions + GitHub Pages (`gh-pages` branch)

## Local Development

```bash
npm ci
npm run documents:build
npm run dev
```

Build commands:

```bash
npm run build:test   # /<repo>/test/
npm run build:prod   # /<repo>/
```

## Build and Quality

```bash
npm run ci:verify
```

This command mirrors the CI quality gate:

1. Build JSON from Markdown.
2. Verify generated JSON is committed.
3. Run lint.
4. Build app.

## Publishing to GitHub (Public Repository)

1. Create a **public** GitHub repository (no initial README).
2. Push code:

```bash
git add .
git commit -m "chore: initial legal docs platform baseline"
git remote add origin <github-repo-url>
git push -u origin main
```

3. GitHub settings:
   - `Settings > Pages > Source: GitHub Actions`
   - `Settings > Environments`: optional (`test`/`production`) without required reviewers
   - `Settings > Branches`: protect `main` and `develop` according to your governance policy

Detailed checklist: [`docs/GITHUB_SETUP.md`](docs/GITHUB_SETUP.md).
Operational runbook: [`docs/GITOPS_RUNBOOK.md`](docs/GITOPS_RUNBOOK.md).

## CI/CD Overview

- `ci.yml`
  - Trigger: PR to `develop` and `main`, and push to `develop` and `main`
  - Runs: `documents:build`, generated-files diff check, lint, build
- `deploy-pages.yml`
  - Trigger: push on `develop` and `main`, and manual dispatch
  - Branch strategy:
    - `develop` publishes **test** at `/<repo>/test/`
    - `main` publishes **production** at `/<repo>/`
  - Deploy target: `gh-pages`
  - URL (prod): `https://<owner>.github.io/<repo>/`
  - URL (test): `https://<owner>.github.io/<repo>/test/`

## Legal Digital Validity (ICP-Brasil)

The repository includes governance for qualified digital signatures and evidence tracking.

- Legal execution process and checklist: [`docs/LEGAL_EXECUTION.md`](docs/LEGAL_EXECUTION.md)
- Evidence templates and structure: [`legal_evidence/README.md`](legal_evidence/README.md)

## Documents JSON

Generated files are stored in `src/documents_json/`.

Schema details and generator notes: [`src/documents_json/README.md`](src/documents_json/README.md).
