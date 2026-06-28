# GitHub Actions Quality Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Windows GitHub Actions quality gate, verify it on Pull Request #1, then merge the feature branch into `main` with a merge commit.

**Architecture:** A single workflow job reproduces the project gate on `windows-latest` with Python 3.12 and Qt offscreen mode. GitHub validates the pushed PR commit; only a green run permits the planned merge and branch cleanup.

**Tech Stack:** GitHub Actions, Windows runner, Python 3.12, PySide6, pip, ruff, mypy, pytest, GitHub CLI.

---

### Task 1: Add the Windows quality workflow

**Files:**
- Create: `.github/workflows/quality.yml`

- [ ] **Step 1: Verify the workflow is absent**

Run:

```powershell
Test-Path .github/workflows/quality.yml
```

Expected: `False`.

- [ ] **Step 2: Create the workflow**

Create `.github/workflows/quality.yml` with exactly:

```yaml
name: Quality gate

on:
  pull_request:
    branches:
      - main
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: quality-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  quality:
    runs-on: windows-latest
    timeout-minutes: 20
    env:
      QT_QPA_PLATFORM: offscreen

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: pyproject.toml

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"

      - name: Ruff
        run: ruff check src tests

      - name: Mypy
        run: mypy src tests

      - name: Pytest
        run: pytest -q

      - name: Compile
        run: python -m compileall -q src tests
```

- [ ] **Step 3: Inspect the workflow and local diff**

Run:

```powershell
Get-Content .github/workflows/quality.yml -Encoding utf8
git diff --check
git status --short
```

Expected: the YAML matches Step 2, `git diff --check` is silent and only
`.github/workflows/quality.yml` is untracked.

- [ ] **Step 4: Run the project gate locally**

Run in order:

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src tests
.\.venv\Scripts\pytest.exe -q -o addopts=""
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Expected: all commands exit 0; pytest reports the exact passing-test count.

- [ ] **Step 5: Commit the workflow**

```powershell
git add -- .github/workflows/quality.yml
git commit -m "ci: add Windows quality gate"
```

### Task 2: Run the workflow on Pull Request #1

**Files:**
- Verify: `.github/workflows/quality.yml`
- Verify: Pull Request `MeGuRu11/educase#1`

- [ ] **Step 1: Push the new commits**

```powershell
git push origin codex/project-consistency-sync
```

Expected: commits `4fd60e8`, the plan commit and the workflow commit appear in PR #1.

- [ ] **Step 2: Confirm GitHub registered the workflow run**

```powershell
gh run list --repo MeGuRu11/educase --branch codex/project-consistency-sync --limit 5
```

Expected: a `Quality gate` run for event `pull_request` appears.

- [ ] **Step 3: Wait for CI**

```powershell
gh pr checks 1 --repo MeGuRu11/educase --watch --interval 10
```

Expected: job `quality` finishes successfully. If it fails, inspect with:

```powershell
gh run view --repo MeGuRu11/educase --log-failed
```

Apply only the smallest workflow or project fix supported by the failed log, rerun the local
gate, commit, push and repeat Step 3.

- [ ] **Step 4: Mark the Pull Request ready**

```powershell
gh pr ready 1 --repo MeGuRu11/educase
gh pr view 1 --repo MeGuRu11/educase --json isDraft,mergeable,mergeStateStatus,statusCheckRollup
```

Expected: `isDraft=false`, the PR is mergeable and the `quality` check is successful.

### Task 3: Merge into main and clean up the feature branch

**Files:**
- Verify: local and remote Git refs

- [ ] **Step 1: Merge the Pull Request with history preserved**

```powershell
gh pr merge 1 --repo MeGuRu11/educase --merge --delete-branch
```

Expected: PR #1 state becomes `MERGED` and the remote feature branch is removed.

- [ ] **Step 2: Synchronize local main**

```powershell
git checkout main
git pull --ff-only origin main
```

Expected: local `main` contains the GitHub merge commit.

- [ ] **Step 3: Verify the merged result**

Run in order:

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src tests
.\.venv\Scripts\pytest.exe -q -o addopts=""
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Expected: the same green result as on the feature branch and in GitHub Actions.

- [ ] **Step 4: Remove the local feature branch**

```powershell
git branch -d codex/project-consistency-sync
git fetch --prune origin
git status -sb
git log -3 --oneline --decorate
```

Expected: only `main` is checked out, it tracks `origin/main`, the worktree is clean and the
feature branch no longer exists locally or remotely.
