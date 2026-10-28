# Day 3 — Property-Based Testing for the Parameter Cascade (Correctness Property 1)

> Detailed working reference for Day 3 of the Java -> Python framework migration.
> Local project: `C:\code\branch_0.0.10\automation-cqa-libraries\pw-webTestAutomation-py`
> GitHub remote: `https://github.com/ssampathkumar104/py-webUI-pw.git`
> Spec task completed: **1.5** (hypothesis property test for the get_parameter cascade).
> Builds on Day 2 (`get_parameter` in `src/ita_pw/core/settings.py`).

---

## 1. Objective

Prove the `get_parameter` cascade with a property-based test (Hypothesis): auto-generate
many (env, class, suite, default) combinations and assert the first-non-blank precedence
rule and blank==unset hold for all of them. This is **Correctness Property 1**.

---

## 2. Key concepts (the "why")

- **Example-based test** (Day 2): checks specific inputs you thought of.
- **Property-based test** (today): states an invariant true for ALL inputs; the library
  generates hundreds of random inputs trying to break it.
- **A property** = a universally-quantified invariant. Property 1: `get_parameter` returns the
  FIRST non-blank candidate in order env/CLI > class > suite; blank (empty/whitespace-only) is
  skipped; if all blank, return default.
- **Oracle technique:** because inputs are random you cannot hard-code expected outputs.
  Instead write a tiny, obviously-correct reference ("oracle") of the rule and assert the real
  function agrees with it for every generated case. The oracle must NOT reuse the
  implementation's helpers (or it would compare the code to itself).
- **Shrinking:** when a property fails, Hypothesis reduces the input to the simplest case that
  still fails, and saves it (reproducible). A property test only matters if it CAN fail
  ("has teeth").

Hypothesis mechanics:
- `@given(arg=strategy, ...)` runs the test many times with generated values.
- Strategies are data recipes: `st.text()` (random strings incl. empty/whitespace/unicode),
  `st.none()`, `st.one_of(...)` to mix.
- `@settings(max_examples=N)` controls how many cases (we used 200; plan requires >= 100).

---

## 3. Setup

```powershell
uv add --dev hypothesis==6.112.1
# installs hypothesis + attrs + sortedcontainers; updates pyproject.toml + uv.lock
```
`--dev` = test-only dependency group (not shipped to consumers).

---

## 4. The test — `tests/unit/test_settings_property.py`

```python
tier_value = st.one_of(st.none(), st.text())   # each tier: absent (None) or any string

def _is_blank(value):                           # independent copy of the blank rule
    return value is None or value.strip() == ""

def _expected(env, cls, suite, default):        # the ORACLE
    for candidate in (env, cls, suite):
        if not _is_blank(candidate):
            return candidate
    return default

@given(env=tier_value, cls=tier_value, suite=tier_value, default=tier_value)
def test_cascade_is_first_non_blank_in_precedence_order(env, cls, suite, default):
    key = "propKey"
    original_class = settings._class_param
    original_suite = settings._suite_param
    try:
        settings.clear_all_overrides()
        if env is not None:
            set_override(key, env)              # env/CLI tier via in-process override
        settings._class_param = lambda k: cls   # patch stub tiers to generated values
        settings._suite_param = lambda k: suite
        result = get_parameter(key, default)
        assert result == _expected(env, cls, suite, default)
    finally:
        settings._class_param = original_class  # restore per example
        settings._suite_param = original_suite
        settings.clear_all_overrides()
```

Run:
```powershell
uv run pytest tests/unit/test_settings_property.py -v   # 1 passed (200 examples inside)
uv run pytest -v                                        # 14 passed total
```

---

## 5. Issues encountered & solutions (the valuable part)

### Issue 1 — FailedHealthCheck: function-scoped fixture `monkeypatch` used under @given
**Symptom:** first version used the `monkeypatch` fixture in the `@given` test; Hypothesis
refused it with `FailedHealthCheck` about function-scoped fixtures not resetting between
generated examples.
**Root cause:** `@given` runs the test body ~N times, but a pytest fixture is created ONCE per
test function — so its patches do not reset between generated examples. This is a real
anti-pattern Hypothesis guards against (subtle, order-dependent bugs).
**Solution:** remove the `monkeypatch` fixture. Patch the tiers manually inside the test
(`settings._class_param = lambda k: cls`, etc.) and restore the originals in a `finally`
block, so every generated example gets clean setup/teardown. The override layer alone controls
the env tier, so no `os.environ` manipulation is needed.
**Lesson:** property tests manage their own setup/teardown; do not lean on function-scoped
fixtures under `@given`.

### Issue 2 (demonstration, not a bug) — proving the test "has teeth"
**Action:** deliberately reversed the cascade in `get_parameter`:
`for candidate in (_suite_param(key), _class_param(key), _env_override(key))`.
**Result:** the property FAILED with a shrunk falsifying example:
```
env=None,        # or any other generated value
cls='0',
suite='1',
default=None,    # or any other generated value
AssertionError: assert '1' == '0'
```
Hypothesis shrank to the simplest distinct strings and flagged env/default as irrelevant to the
failure — pointing straight at class-vs-suite precedence. Reverted the loop to the correct
order; test passed again (fast, because the saved counterexample is replayed first).
**Lesson:** a property test must be able to fail; the falsifying example is a minimal,
reproducible root-cause pointer.

### Housekeeping — .hypothesis/ example database
Hypothesis created `.hypothesis/` (its example DB). Added `.hypothesis/` to `.gitignore` so it
is never committed. Verified the Day 3 commit contained only: `.gitignore`, `docs/ADR-notes.md`,
`pyproject.toml`, `tests/unit/test_settings_property.py`, `uv.lock` — no `.hypothesis/`.

---

## 6. Verification evidence ("done" looked like)

- `uv run pytest tests/unit/test_settings_property.py -v` -> **1 passed** (200 examples)
- deliberate break -> **1 failed** with falsifying example `cls='0', suite='1'`; revert -> pass
- `uv run pytest -v` -> **14 passed**
- `git show --stat HEAD` -> 5 files, no `.hypothesis/`
- committed `test(core): hypothesis property for parameter cascade` and pushed.

---

## 7. Deliverable & "done" definition

Passing property test (Correctness Property 1) over >= 200 generated cases, with a demonstrated
failing example when the cascade is intentionally broken. Spec task 1.5 complete.

**Manager explanation:** "We now auto-generate hundreds of configuration scenarios each run to
prove settings behave correctly — not just the handful of cases we thought of by hand."

---

## 8. Knowledge check (self-quiz)

1. How does a property test differ from an example-based unit test?
2. What invariant does Property 1 encode?
3. Why run >= 100 generated cases?
4. What does a Hypothesis "counterexample" give you, and why does shrinking matter?

---

## 9. Next: Day 4 — Equivalence harness scaffold

Build `tests/equivalence/` : a checkpoint registry (M0-M2.1 checkpoints as named pass/fail
assertions), a per-component gate aggregator, and a Java-vs-Python output-diff helper. Encode
the M2.1 parameter precedence truth table as the first checkpoint, driven by `core/settings.py`.
Spec task 1.6.

### Resume commands
```powershell
cd C:\code\branch_0.0.10\automation-cqa-libraries\pw-webTestAutomation-py
uv --version
git switch feat/foundation-packaging
uv run pytest -v        # confirm 14 pass
```
