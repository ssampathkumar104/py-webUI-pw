
## Day 2 - Parameter resolution (get_parameter, M2.1 parity)

- Precedence (highest first): env/CLI override > class-level param > suite/test-level param > literal default.
- Blank == unset: an empty or whitespace-only value is skipped and falls through (Java isBlank, NOT a null check).
- Fail-soft: never raises; on missing context or a tier error, returns the default or None.
- Raw value: returned verbatim (no trim, no case change); callers do their own exact comparisons.
- Env/CLI tier = in-process override dict (checked first) then os.environ. Class/suite tiers are STUBS (return None) until the pytest plugin wires them.
- Enforced by tests/unit/test_settings.py (10 tests); Correctness Property 1 is proven by a hypothesis property test on Day 3.

## Day 3 - Property-based test (Correctness Property 1)

- Added hypothesis (dev dep, pinned 6.112.1) and tests/unit/test_settings_property.py.
- Property 1: get_parameter returns the first non-blank candidate in order env/CLI > class > suite, blank==unset, else default. Verified against 200 generated (env,class,suite,default) cases via an independent oracle.
- Do NOT use the function-scoped monkeypatch fixture under @given (state does not reset per example); patch tiers manually and restore in finally.
- Verified the test has teeth: reversing the cascade order produced a shrunk falsifying example (cls='0', suite='1'). Reverted.
- .hypothesis/ example DB is gitignored.

## Day 4 - Equivalence harness scaffold (task 1.6)

- tests/equivalence/eq_harness.py: CheckpointRegistry (named checkpoints tagged by component + M-doc source), run_gate (go/no-go aggregation), diff_outputs/assert_equivalent (Java-vs-Python comparison).
- Gate rule: a component gate passes only if ALL its checkpoints pass; a gate with ZERO checkpoints FAILS (existing code is not validated behaviour). A crashing checkpoint counts as a FAIL, never a harness crash.
- First checkpoint (eq_checkpoints.py): the M2.1 parameter-precedence truth table, 9 rows, component foundation.
- Verified the gate has teeth: reversing the cascade failed rows 1, 3 and 4 (the rows where multiple tiers compete); single-tier rows still passed. Reverted.
- Files use an eq_ prefix and no __init__.py so pytest's rootdir import mode can import them without clashing with installed packages.

## Day 5 - CI skeleton (task 1.7) on GitHub Actions

- Platform decision: the project lives on GitHub, so CI is a GitHub Actions workflow (.github/workflows/ci.yml). The spec (Requirement 15 / task 1.7) names GitLab and .gitlab-ci.yml; this is a recorded deviation. Concepts map 1:1: stages -> jobs chained with `needs`, CI/CD variables -> repository Secrets. Spec documents still say GitLab until they are updated.
- Fail-fast chain: lint -> unit -> equivalence -> integration -> package. Each job `needs` the previous one, so a failing job stops all later jobs.
- Lockfile enforcement: every uv job runs `uv sync --locked`, which fails if uv.lock is out of sync with pyproject.toml. This delivers the "out-of-sync lock fails install" check deferred from task 1.2.
- Toolchain pins: uv 0.13.5 (matches local), Python from .python-version (3.12), actions/checkout@v7 and actions/setup-python@v7 (latest majors verified from the releases API, Oct 2026). Hardening later: pin actions to full commit SHAs.
- Secrets rule: no secret appears in the workflow. Future credentials come from repository Secrets via ${{ secrets.NAME }} inside the publish step only. permissions.contents is read-only.
- Stubs (hardened in task 16.1): Playwright browser pre-provisioning (integration job) and the private-index publish (package job). The package job builds with `uv build` and runs only on v* tags.
- Lint: ruff added as a pinned dev dependency.
