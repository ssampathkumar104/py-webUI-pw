"""Property-based test for the get_parameter cascade (spec task 1.5).

Correctness Property 1: resolution is a total function of (env, class, suite, default);
the result is the FIRST non-blank candidate in precedence order
(env/CLI > class > suite), with blank (empty/whitespace-only) treated as unset;
if all tiers are blank, the default is returned.

Hypothesis generates many (env, class, suite, default) combinations and asserts the
real implementation agrees with an independent reference ("oracle") of the rule.

Note: we do NOT use the function-scoped `monkeypatch` fixture here. Under @given the
test body runs many times but a fixture is created once, so its state would not reset
between generated examples (Hypothesis flags this). Instead we patch the tiers manually
inside the test and restore them in a finally block, giving each example clean setup.
"""

from hypothesis import given
from hypothesis import strategies as st

from ita_pw.core import settings
from ita_pw.core.settings import get_parameter, set_override

# A value for any tier is either "absent" (None) or a generated string
# (which may be blank, whitespace, or real text — all important edge cases).
tier_value = st.one_of(st.none(), st.text())


def _is_blank(value):
    """Independent copy of the blank rule (the oracle must not reuse the impl helper)."""
    return value is None or value.strip() == ""


def _expected(env, cls, suite, default):
    """Reference implementation of Property 1 — obviously correct, computed independently."""
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
        # env/CLI tier via the in-process override (cleared when env is absent)
        settings.clear_all_overrides()
        if env is not None:
            set_override(key, env)
        # class/suite tiers patched to the generated values for this example
        settings._class_param = lambda k: cls
        settings._suite_param = lambda k: suite

        result = get_parameter(key, default)
        assert result == _expected(env, cls, suite, default)
    finally:
        settings._class_param = original_class
        settings._suite_param = original_suite
        settings.clear_all_overrides()
