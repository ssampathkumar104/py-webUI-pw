# Day 2 — Core: Parameter Resolution Cascade (get_parameter, M2.1 parity)

> Detailed working reference for Day 2 of the Java -> Python framework migration.
> Local project: `C:\code\branch_0.0.10\automation-cqa-libraries\pw-webTestAutomation-py`
> GitHub remote: `https://github.com/ssampathkumar104/py-webUI-pw.git`
> Spec tasks completed: **1.3** (settings cascade impl) and **1.4** (unit tests).
> Grounded in: `docs/M2.1-parameter-resolution-model.md`.

---

## 1. Objective

Implement `get_parameter(key, default=None)` in `src/ita_pw/core/settings.py` that resolves
configuration with the SAME precedence as the Java `BaseClass.getParameter`, and cover it with
unit tests.

---

## 2. Key concepts (the "why")

Java reference behavior being reproduced:

```java
String value         = System.getProperty(key);                                 // (1) -D / env
String defValue      = getITestContext().getCurrentXmlTest().getParameter(key);  // (3) test/suite
String defLocalValue = getLocalClassParameter(key);                              // (2) class
return isBlank(value) ? (isBlank(defLocalValue) ? defValue : defLocalValue) : value;
// two-arg overload applies a literal default only when getParameter(key) == null
```

Four parity rules:
- **Precedence (highest first):** env/CLI override > class-level > suite/test-level > default.
- **Blank == unset:** empty or whitespace-only value is skipped and falls through (Java
  `isBlank`, NOT a null check). This is the most important subtlety.
- **Fail-soft:** never throws; on missing context / a tier error, returns default or None.
- **Raw value:** returned verbatim (no trim, no case change); callers do their own exact
  comparisons (so "TRUE" != "true" — the M2.1 caller-side gotcha is preserved).

Design choices for this project:
- **Env/CLI tier = Option 2:** an in-process `_overrides` dict (checked first) THEN
  `os.environ`. The override dict is the testable, future-CLI injection point.
- **Class/suite tiers are STUBS** (`return None`) until the pytest plugin wires them (later day).
- **`get_bool` deferred** — keep raw-string parity today; add convenience later only if needed.

---

## 3. Implementation — `src/ita_pw/core/settings.py`

Public API: `get_parameter(key, default=None)`, plus `set_override` / `clear_override` /
`clear_all_overrides` for the in-process tier. Internals: `_is_blank`, `_env_override`,
`_class_param` (stub), `_suite_param` (stub).

Core logic:
```python
def get_parameter(key: str, default: str | None = None) -> str | None:
    try:
        for candidate in (_env_override(key), _class_param(key), _suite_param(key)):
            if not _is_blank(candidate):
                return candidate
        return default
    except Exception:
        return default
```
- `_is_blank(v)` = `v is None or v.strip() == ""` (the isBlank parity).
- `_env_override(key)` = `_overrides[key]` if present, else `os.environ.get(key)`.
- The `for` loop over the three tiers = the Java nested ternary, made readable.

Manual smoke test (confirmed working):
```powershell
uv run python -c "from ita_pw.core.settings import get_parameter, set_override; print(repr(get_parameter('browserName'))); set_override('browserName','chrome'); print(repr(get_parameter('browserName'))); print(repr(get_parameter('missing','fallback')))"
# -> None / 'chrome' / 'fallback'
```

---

## 4. Tests — `tests/unit/test_settings.py` (10 tests)

- precedence: env override wins; default when unset; None when unset+no default; env beats
  default.
- blank == unset: empty-string and whitespace-only both fall through to default.
- raw value: "  TRUE  " returned verbatim (no trim/case change).
- env var tier: os.environ read via `monkeypatch.setenv`; override beats env var.
- fail-soft: `monkeypatch` swaps `_class_param` to raise; get_parameter returns the default.

An `autouse` fixture `_clean_overrides` clears the module-global `_overrides` before/after each
test for isolation.

Run:
```powershell
uv run pytest tests/unit/test_settings.py -v   # 10 passed
uv run pytest -v                               # 13 passed (Day 1 + Day 2)
```

---

## 5. Issues encountered & solutions (the valuable part)

### Issue 1 — IndentationError: "unindent does not match any outer indentation level"
**Symptom:** import/collection failed at the `try:` line in `get_parameter`.
**Root cause:** mixed tabs/spaces / a misaligned inline comment introduced during hand-edit or
paste. Python treats indentation as syntax and rejects inconsistent whitespace.
**Solution:** make the file uniformly 4-space indented. The specific culprit here was an inline
comment on the `except Exception:` line whose leading whitespace did not match. Removing/aligning
it fixed import.
**Prevention:** write Python files via a verified copy, not multi-line paste; set the editor to
4-space indent and "convert indentation to spaces".

### Issue 2 — PowerShell here-string written literally into the file
**Symptom:** `SyntaxError: unterminated string literal` with line 1 = `@'`.
**Root cause:** the here-string (`@' ... '@`) got mangled on paste, so PowerShell did not treat
it as a here-string; the literal text (including `@'`) landed in the file.
**Solution / new workflow:** stop pasting multi-line content. Author the file once in a known-good
location, then bring it in with a single-line `Copy-Item`. A one-line copy cannot be
double-pasted or whitespace-corrupted.

### Issue 3 — NameError: name 'overrides' is not defined
**Symptom:** all 10 tests ERRORed at setup; `clear_all_overrides()` and `_env_override()`
referenced `overrides` instead of `_overrides`.
**Root cause:** typo (dropped leading underscore) in two places during hand-edit.
**Solution:** changed `overrides.clear()` -> `_overrides.clear()` and
`if key in overrides:` -> `if key in _overrides:`. Python's error even suggested the right name.
**Lesson:** read the error's suggestion ("Did you mean ...?"); module-global names must match
exactly between module and tests.

### Issue 4 — function-name mismatch between module and tests
**Symptom (earlier variant):** `has no attribute 'clear_all_overrides'. Did you mean
'clear_all_override'?`
**Root cause:** module defined the singular `clear_all_override`; tests called the plural.
**Solution:** standardize on the plural `clear_all_overrides` in both.

### Carried-over gremlin — double-paste
Commands still occasionally pasted twice on one line. Mitigation: type short commands, or paste
-> Esc -> paste once; prefer single-line `Copy-Item` for file content.

---

## 6. Verification evidence ("done" looked like)

- smoke test -> `None` / `'chrome'` / `'fallback'`
- `uv run pytest tests/unit/test_settings.py -v` -> **10 passed**
- `uv run pytest -v` -> **13 passed**
- committed `feat(core): parameter resolution cascade (M2.1 parity)` and pushed to GitHub.

---

## 7. Deliverable & "done" definition

Working `get_parameter` with M2.1 parity + 10 unit tests green (13 total) + ADR note + commit
pushed. Spec tasks 1.3 and 1.4 complete.

**Manager explanation:** "Settings now resolve in the same priority order as the old framework,
so existing configuration keeps working exactly as before."

---

## 8. Known stubs / not-yet-covered

- `_class_param` and `_suite_param` return None (stubs) — wired to the pytest plugin on a later
  day. No test pretends to cover "class beats suite" yet.
- Correctness Property 1 (resolution is a total function; first non-blank wins) is proven on
  **Day 3** with a hypothesis property test.

---

## 9. Knowledge check (self-quiz; answers in M2.1 + settings.py)

1. What are the three precedence tiers, highest first?
2. Why is a whitespace-only value treated as unset?
3. What does the function return when nothing matches and no default is given?
4. Why must it never throw when called outside a live test?

---

## 10. Next: Day 3 — Property-based test for the cascade

Add a hypothesis property test (>= 100 cases) over (env, class, suite, default) asserting the
first-non-blank rule and blank==unset (Correctness Property 1). Deliberately break the cascade
order once to confirm the property fails (shows it has teeth).

### Resume commands
```powershell
cd C:\code\branch_0.0.10\automation-cqa-libraries\pw-webTestAutomation-py
uv --version
git switch feat/foundation-packaging
uv run pytest -v        # confirm 13 pass
```
