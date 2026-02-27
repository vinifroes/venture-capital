# GitOps Runbook (Test/Prod)

This runbook defines how to bootstrap, operate, troubleshoot, and recover the repository and GitHub Pages deployments.

## 1) Architecture

- Repository: `vinifroes/venture-capital` (public).
- Branch model:
  - `develop`: integration branch, deploys test.
  - `main`: production branch, deploys production.
- Pages publishing branch: `gh-pages` (managed only by workflow).
- Environments:
  - Test URL: `https://vinifroes.github.io/venture-capital/test/`
  - Prod URL: `https://vinifroes.github.io/venture-capital/`

## 2) Bootstrap From Zero (Clean History)

### 2.1 Backup and reference export

```bash
cd /path/to/project-root
mkdir -p ../backups
tar -czf ../backups/venture-capital-pre-reset-$(date +%Y%m%d-%H%M%S).tar.gz .
git remote -v
git log --oneline --max-count=5
```

Save:
- old remote URL
- relevant branches
- last stable SHA

### 2.2 Recreate GitHub repository

1. Delete old repository in GitHub.
2. Create new public repository `vinifroes/venture-capital`.
3. Keep repository empty (no README, no license, no .gitignore).

### 2.3 Reinitialize local repository

```bash
cd /path/to/project-root
rm -rf .git
git init -b main
git add .
git commit -m "chore: baseline for new gitops lifecycle"
git remote add origin git@github.com:vinifroes/venture-capital.git
git push -u origin main
git checkout -b develop
git push -u origin develop
git checkout main
```

## 3) GitHub Settings Checklist

## 3.1 Pages

- Go to `Settings > Pages`.
- Build and deployment source: `Deploy from a branch`.
- Branch: `gh-pages` / `(root)`.

## 3.2 Actions permissions

- Go to `Settings > Actions > General`.
- Ensure workflow permissions are compatible with `contents: write`.

## 3.3 Environments

- Optional: create `test` and `production`.
- Do not require reviewers for automatic deploys.
- Do not block refs `develop` and `main`.

## 3.4 Branch protection

- `main`:
  - require PR
  - restrict direct pushes
  - keep linear history
- `develop`:
  - configure according to team governance
- Status checks are observable but not mandatory in this governance model.

## 4) Daily Development Flow

## 4.1 Feature development

```bash
git checkout develop
git pull
git checkout -b feature/<short-name>
# edit code
npm ci
npm run ci:verify
git add .
git commit -m "feat: <description>"
git push -u origin feature/<short-name>
```

Open PR:
- `feature/<short-name>` -> `develop`

## 4.2 Promote to production

1. Open PR from `develop` to `main`.
2. Merge PR.
3. `main` push triggers production deploy automatically.

## 5) CI/CD Workflows

- `ci.yml`
  - Runs on PR and push to `develop` and `main`.
  - Checks: docs build consistency, lint, app build.
- `deploy-pages.yml`
  - Push `develop`: updates only `/test/` content on `gh-pages`.
  - Push `main`: updates root production content and preserves `/test/`.
  - `workflow_dispatch`: deploy from custom `ref` (branch, tag, or SHA).

## 6) Rollback Procedures

## 6.1 Rollback production

1. Identify last stable commit in `main`.
2. Re-run deploy manually with that ref:
   - Actions > `Deploy Pages` > Run workflow > ref=`<stable-sha-or-tag>`
3. Verify production URL and assets.

Alternative:
- Revert offending commit on `main` and push.

## 6.2 Rollback test

1. Identify stable commit in `develop`.
2. Run manual deploy with that ref.
3. Verify `/test/` URL.

## 7) Incident Troubleshooting

## 7.1 403 on push to `gh-pages`

Symptoms:
- deploy workflow fails during `git push origin HEAD:gh-pages`.

Checks:
```bash
git remote -v
```
- Verify repository Actions permissions include `contents: write`.
- Verify no branch protection blocks workflow pushes to `gh-pages`.

## 7.2 GitHub Pages returns 404

Checks:
- `Settings > Pages` source must be `Deploy from a branch` with `gh-pages` / `(root)`.
- Confirm latest deploy workflow succeeded.
- Inspect `gh-pages` branch content:

```bash
git fetch origin gh-pages:refs/remotes/origin/gh-pages
git ls-tree -r --name-only origin/gh-pages | head -n 50
```

Expected:
- `index.html` at root for prod.
- `test/index.html` for test.
- `.nojekyll` present.

## 7.3 Deployment rejected by environment rules

Symptoms:
- workflow fails in first seconds with rejection message.

Fix:
- remove required reviewers for automated flows.
- remove ref restrictions incompatible with `develop`/`main`.

## 7.4 Broken assets due to wrong base path

Symptoms:
- page opens but JS/CSS returns 404.

Checks:
- `develop` deploy must use `/venture-capital/test/`.
- `main` deploy must use `/venture-capital/`.
- confirm `deploy-pages.yml` still sets `VITE_BASE_PATH` correctly.

## 8) Post-Deploy Validation Commands

```bash
curl -sSI https://vinifroes.github.io/venture-capital/ | sed -n '1,20p'
curl -sSI https://vinifroes.github.io/venture-capital/test/ | sed -n '1,20p'
```

Expected:
- HTTP `200` on both URLs after propagation.

Validate generated documents consistency before merges:

```bash
npm run ci:verify
```

## 9) Operational Guardrails

- Do not push directly to `gh-pages`.
- Keep deploy logic centralized in `.github/workflows/deploy-pages.yml`.
- Keep CI deterministic with `SOURCE_DATE_EPOCH=0`.
- Keep legal execution updates manifest-driven:
  - update evidence bundle + manifest + `active-manifests.json`
  - avoid manual edits in `execution` fields without manifest change
- For ICP stakeholder flow, follow:
  - [`ICP_STAKEHOLDER_FLOW.md`](./ICP_STAKEHOLDER_FLOW.md)
- Update this runbook whenever workflow behavior changes.
