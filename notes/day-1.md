# Day 1 — Foundation: Packaging & Project Skeleton (uv + pyproject.toml)

> Detailed working reference for Day 1 of the Java -> Python framework migration.
> Target project: **ita_pw** (the Python port of `inforTestAutomation-pw`).
> Local project path: `C:\code\branch_0.0.10\automation-cqa-libraries\pw-webTestAutomation-py`
> GitHub remote: `https://github.com/ssampathkumar104/py-webUI-pw.git`
> Spec tasks completed: **1.1** (package skeleton) and **1.2** (install-contract tests).

---

## 1. Objective

Produce a clean, installable `ita_pw` package managed by **uv**, with:

- a `pyproject.toml` (the Python equivalent of `pom.xml`),
- a committed `uv.lock` (reproducible, exact-pinned dependencies),
- the full subpackage skeleton,
- a pytest plugin that auto-discovers on install,
- passing install-contract tests.

No framework logic yet — Day 1 is the shell and its build file.

---

## 2. Key concepts learned

- **The package is the deliverable.** Downstream test projects depend on `ita_pw` the way
  they depended on the Maven JAR.
- **`pyproject.toml` = `pom.xml`.** `[project].dependencies` = `<dependencies>`;
  `[build-system]` = the Maven build plugin role; `version`/`name` = `<version>`/`<artifactId>`.
- **Lockfile (`uv.lock`) = stronger `<properties>` pinning.** It pins exact versions of direct
  AND transitive deps with hashes, so every machine installs byte-identical dependencies.
- **uv** unifies environment + dependency + build in one fast tool (ADR-5; poetry/pip-tools
  rejected).
- **pytest-plugin entry point (`pytest11`)** is the Python replacement for Java
  `@Listeners` + `extends BaseClass` auto-wiring: once `ita_pw` is installed, pytest loads the
  plugin automatically, no imports/config in the consuming project.
- **`src/` layout** chosen (uv default): prevents accidentally importing the package from the
  working directory instead of the installed one.
- **A folder is an importable package only if it contains `__init__.py`.**

---

## 3. Decisions made

| Decision | Choice | Why |
|---|---|---|
| Python version | 3.12 (`>=3.12,<3.13`) | 3.14.6 was too new; Playwright/pydantic/boto3 may lack 3.14 wheels. uv manages 3.12 per-project; global 3.14 untouched. |
| Dependency manager | uv | Fast, reproducible lockfile incl. transitive deps, unified tooling (ADR-5). |
| Layout | `src/` layout | Modern best practice; import-safety. |
| Day 1 deps | pytest, pytest-xdist, pytest-rerunfailures (exact-pinned) | Test runner trio only; heavier deps added on the days their layers are built. |
| Package activation | `pytest11` entry point -> `ita_pw.plugin` | Auto-discovery, replaces Java @Listeners wiring. |
| Desktop subpackage | NOT created | SikuliX is out of scope (resolved decision). |

---

## 4. Step-by-step (what was actually done)

### Step 1 — Install uv
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv --version   # uv 0.13.5
```

### Step 2 — Create & initialize the project
```powershell
mkdir <project-folder>
cd <project-folder>
uv python pin 3.12
uv init --package --name ita_pw --python 3.12
```
Result: `.venv`, `src/ita_pw/__init__.py`, `pyproject.toml`, `.python-version`, `README.md`,
`uv.lock`, `.gitignore`. Note: distribution name is `ita-pw` (hyphen), import name `ita_pw`
(underscore) — normal Python convention.

### Step 3 — Scaffold subpackages + test dirs
```powershell
$pkgs = "core","pages","plugin","events","reporting","data","results_api","sharepoint","genai_summary","integrations"
foreach ($p in $pkgs) {
  New-Item -ItemType Directory -Force -Path "src\ita_pw\$p" | Out-Null
  New-Item -ItemType File -Force -Path "src\ita_pw\$p\__init__.py" | Out-Null
}
New-Item -ItemType Directory -Force -Path "tests\unit" | Out-Null
New-Item -ItemType Directory -Force -Path "tests\equivalence" | Out-Null
New-Item -ItemType File -Force -Path "tests\unit\.gitkeep" | Out-Null
New-Item -ItemType File -Force -Path "tests\equivalence\.gitkeep" | Out-Null
```
Result: 11 `__init__.py` (top-level + 10 subpackages); two test dirs. No `desktop/`.

### Step 4 — Edit pyproject.toml
Final content:
```toml
[project]
name = "ita-pw"
version = "0.1.0"
description = "Infor Test Automation - Playwright + Python + Pytest framework (migrated from inforTestAutomation-pw Java)."
readme = "README.md"
authors = [ { name = "Sampath Sankati", email = "Sampath.Sankati@infor.com" } ]
requires-python = ">=3.12,<3.13"
dependencies = [
    "pytest==8.3.4",
    "pytest-xdist==3.6.1",
    "pytest-rerunfailures==15.0",
]

[project.entry-points.pytest11]
ita_pw = "ita_pw.plugin"

[build-system]
requires = ["uv_build>=0.13.5,<0.14.0"]
build-backend = "uv_build"
```
Changes vs uv template: real description; tightened `requires-python` ceiling; added 3 pinned
deps; REMOVED `[project.scripts]` (no CLI); ADDED `[project.entry-points.pytest11]`.

### Step 5 — Lock & sync
```powershell
uv lock    # resolves direct + transitive deps -> uv.lock (exact versions + hashes)
uv sync    # installs lockfile into .venv (deterministic env)
```

### Step 6 — Verify (the proof of Day 1)
```powershell
# plugin auto-discovery:
uv run pytest --trace-config 2>&1 | Select-String "ita_pw"
#  -> "PLUGIN registered: <module 'ita_pw.plugin' ...>"   (SUCCESS)

# installed versions:
uv pip list 2>&1 | Select-String "pytest|xdist|rerunfailures|ita"
```

### Step 7 — Install-contract tests (task 1.2)
File: `tests/unit/test_packaging.py` with 3 tests:
- `test_ita_pw_is_importable` — package installs & imports.
- `test_all_subpackages_import` — all 10 subpackages importable.
- `test_pytest_plugin_entrypoint_is_registered` — plugin auto-discovered (uses `pytestconfig`).
```powershell
uv run pytest -v   # -> 3 passed
```

### Step 8 — Docs
`docs/ADR-notes.md` — ADR-5 (why uv), Day 1 dependency set, and the manual-check note (below).

### Step 9 — Git + GitHub
```powershell
# repo already init'd by uv (branch master, no commits)
git checkout -b feat/foundation-packaging
git add .gitignore .python-version README.md pyproject.toml uv.lock src tests docs
git status                       # verified .venv / __pycache__ NOT staged
git commit -m "chore: scaffold ita_pw package with uv (Day 1 foundation)"
git remote add origin https://github.com/ssampathkumar104/py-webUI-pw.git
git remote -v
git push -u origin feat/foundation-packaging
```
`.gitignore` correctly ignores `.venv` and `__pycache__/`; `uv.lock` is committed (NOT ignored).

---

## 5. Issues encountered & solutions (the valuable part)

### Issue 1 — `uv` not recognized after install ("CommandNotFoundException")
**Symptom:** `uv --version` -> "The term 'uv' is not recognized ..." even after closing and
reopening the terminal.
**Root cause:** uv installs to `%USERPROFILE%\.local\bin`, which was not on PATH. IDE-integrated
terminals inherit the environment from the already-running IDE process, so reopening only the
terminal panel does NOT pick up PATH changes — the whole IDE must restart, and even then the
permanent entry had not been set yet.
**Diagnosis:** `Test-Path "$env:USERPROFILE\.local\bin\uv.exe"` returned `True` -> installed,
pure PATH problem.
**Solution (session, immediate):**
```powershell
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
uv --version
```
**Solution (permanent):**
```powershell
setx PATH "$env:USERPROFILE\.local\bin;$env:PATH"
```
Then open a NEW terminal (setx does not affect the current one).
**Caveat:** `setx` rewrites the whole user PATH and truncates at ~1024 chars. For a very long
PATH use instead:
```powershell
[Environment]::SetEnvironmentVariable("Path", "$env:USERPROFILE\.local\bin;" + [Environment]::GetEnvironmentVariable("Path","User"), "User")
```
**Note:** the error recurred later in a fresh terminal — the permanent set had been affected by
the double-paste issue (see Issue 2). Re-running the permanent command cleanly is the fix.

### Issue 2 — Commands pasted twice on one line (the recurring gremlin)
**Symptom:** e.g. `Test-Path "..."Test-Path "..."`, `git checkout -b feat/foundation-packaginggit checkout -b feat/foundation-packaging`, producing parser errors like
"A positional parameter cannot be found", "Array index expression is missing",
"'checkout' is not a commit".
**Root cause:** the terminal echoed the clipboard twice on paste (Ctrl+V), concatenating the
command with a second copy of itself.
**Solutions:**
- Type short commands by hand instead of pasting.
- Or: paste -> press **Esc** (clears the line) -> paste once -> Enter.
- Or: use right-click paste instead of Ctrl+V.
**Lesson:** when a command errors oddly, read the echoed line first — look for a doubled command.

### Issue 3 — Python 3.14.6 chosen initially (too new)
**Symptom/Risk:** key deps (Playwright, pydantic, boto3) may not ship 3.14 wheels -> install
failures or slow source builds.
**Solution:** target the 3.12 line. `uv python pin 3.12` + `requires-python = ">=3.12,<3.13"`.
uv downloads/manages 3.12 per-project; global 3.14 remains installed and untouched. Confirmed
via `uv run python --version` -> Python 3.12.3.

### Issue 4 — uv template shipped a CLI entry point we did not want
**Symptom:** generated `pyproject.toml` had `[project.scripts] ita-pw = "ita_pw:main"`, but
there is no `main` and we ship no CLI (would break the build).
**Solution:** removed `[project.scripts]`; added `[project.entry-points.pytest11]` instead.

### Issue 5 — `docs/` did not exist when expected
**Symptom:** `dir docs` -> PathNotFound; the ADR file's `New-Item` had not been run.
**Solution:** `New-Item -ItemType File -Force -Path "docs\ADR-notes.md"` ( `-Force` creates the
folder), then paste content.

### Non-issue clarified — "I want a new git repository"
uv had already run `git init` (branch `master`, no commits). That empty repo IS the new
repository. Created `feat/foundation-packaging` off it and committed there (not master),
following the no-direct-commit-to-main convention.

---

## 6. Verification evidence (what "done" looked like)

- `uv run python --version` -> `Python 3.12.3`
- `uv run pytest --trace-config ... | Select-String ita_pw` -> `PLUGIN registered: <module 'ita_pw.plugin' ...>`
- `uv run pytest -v` -> **3 passed**
- `git status` after staging -> source/tests/pyproject/uv.lock/docs staged; `.venv` NOT staged
- `git push -u origin feat/foundation-packaging` -> completed (on GitHub)

---

## 7. Deliverable & "done" definition

Installable empty `ita_pw` package + committed lockfile + auto-discovered pytest plugin +
3 green install-contract tests + ADR note + first commit pushed to GitHub. Spec tasks 1.1 and
1.2 complete.

**Manager explanation:** "We created the new Python project shell and locked its ingredients so
every machine builds it identically — the equivalent of the old Java build file. We also proved
the framework plugs into the test runner automatically."

---

## 8. Known manual check NOT covered by unit tests

Task 1.2 also mentions "out-of-sync lockfile fails install, no partial import." That is a
CLI/exit-code behavior, not a Python-importable assertion, so it is verified manually (a
corrupted lock makes `uv sync` exit non-zero) and will get a dedicated equivalence-harness
check on **Day 4**.

---

## 9. Open loose ends carried forward

1. **PATH permanence** — if a brand-new terminal reports "uv not recognized" again, re-run the
   permanent PATH command cleanly (single line, no double-paste) and restart the terminal.
2. **Knowledge check** (self-quiz; answers live in M1.1 / M1.2 / this file):
   1. Why pin exact versions instead of ranges?
   2. What does the plugin entry point buy consuming projects?
   3. How is `uv.lock` analogous to the `pom.xml` `<properties>` block?
   4. What fails, and how, if the lockfile is out of sync?

---

## 10. Next: Day 2 — Parameter cascade (`get_parameter`)

Implement `src/ita_pw/core/settings.py` `get_parameter(key, default=None)` with exact Java
precedence (env/CLI > class > suite > default; blank == unset; fail-soft to None), grounded in
`docs/M2.1-parameter-resolution-model.md`. Spec tasks 1.3 (impl) and 1.4 (unit tests).

### Quick commands to resume tomorrow
```powershell
cd C:\code\branch_0.0.10\automation-cqa-libraries\pw-webTestAutomation-py
uv --version            # confirm PATH; if missing, re-apply permanent PATH fix
git switch feat/foundation-packaging
uv run pytest -v        # confirm the 3 tests still pass
```
