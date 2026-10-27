
## Day 2 - Parameter resolution (get_parameter, M2.1 parity)

- Precedence (highest first): env/CLI override > class-level param > suite/test-level param > literal default.
- Blank == unset: an empty or whitespace-only value is skipped and falls through (Java isBlank, NOT a null check).
- Fail-soft: never raises; on missing context or a tier error, returns the default or None.
- Raw value: returned verbatim (no trim, no case change); callers do their own exact comparisons.
- Env/CLI tier = in-process override dict (checked first) then os.environ. Class/suite tiers are STUBS (return None) until the pytest plugin wires them.
- Enforced by tests/unit/test_settings.py (10 tests); Correctness Property 1 is proven by a hypothesis property test on Day 3.
