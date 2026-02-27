# GitHub Setup Checklist

## 1) Repository

- Create repository as **Public**.
- Default branch: `main`.
- Create `develop` branch after initial push.

## 2) Branch Protection

Recommended baseline rules:

- `main`:
  - Require pull request before merging.
  - Restrict direct pushes.
  - Keep linear history enabled.
- `develop`:
  - Restrict direct pushes when needed by team policy.
  - Optionally require PR for all merges.
- Status checks are optional in this project governance model.

## 3) Pages and Environments

- `Settings > Pages > Build and deployment > Source`: **Deploy from a branch**.
- `Settings > Pages > Branch`: `gh-pages` / `(root)`.
- Environments `test` and `production` are optional.
- If environments exist:
  - Do not require manual reviewers for automatic deploy.
  - Do not block refs used by the workflows (`develop` and `main`).

## 4) Actions Permissions

- In `Settings > Actions > General`, keep default token permissions compatible with workflows.
- If needed, set workflow permissions to allow `contents: write` for deploy jobs.

## 5) Release Policy

- `develop` deploys test to `https://<owner>.github.io/<repo>/test/`.
- `main` deploys production to `https://<owner>.github.io/<repo>/`.
- Manual re-deploy is available via `workflow_dispatch` in `deploy-pages.yml` using a branch/tag/SHA ref.

## 6) Recreate Repository (Clean History)

Use this flow when you need to rebuild the repository lifecycle from zero:

1. Backup local project folder and note current remote URL + stable SHA.
2. Delete old GitHub repository.
3. Create new `vinifroes/venture-capital` repository as public (empty).
4. Reinitialize local git and publish fresh baseline:

```bash
rm -rf .git
git init -b main
git add .
git commit -m "chore: baseline for new gitops lifecycle"
git remote add origin git@github.com:vinifroes/venture-capital.git
git push -u origin main
git checkout -b develop
git push -u origin develop
```
