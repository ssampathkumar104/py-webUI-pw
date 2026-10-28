
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
