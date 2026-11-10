"""Foundation checkpoints (spec task 1.6).

Importing this module registers the checkpoints on the default registry.
First checkpoint: the M2.1 parameter-precedence truth table, driven by
ita_pw.core.settings.get_parameter.

The class/suite tiers are still stubs in settings.py, so each row patches them
for the duration of one resolution and restores them afterwards.
"""

from eq_harness import checkpoint

from ita_pw.core import settings
from ita_pw.core.settings import get_parameter, set_override

_KEY = "browserName"

# (env/-D, class-level, suite/test-level, default, expected, why)
M21_TRUTH_TABLE = [
    (None, "webkit", "firefox", None, "webkit", "class-level beats test-level (M2.1 row 1)"),
    (None, None, "firefox", None, "firefox", "no class-level falls to test-level (M2.1 row 2)"),
    ("safari", "webkit", "firefox", None, "safari", "-D beats everything (M2.1 row 3)"),
    ("", "webkit", "firefox", None, "webkit", "blank -D falls through to class"),
    (None, "", "firefox", None, "firefox", "blank class falls through to test-level"),
    (None, "   ", "firefox", None, "firefox", "whitespace-only class falls through"),
    (None, None, None, "chrome", "chrome", "literal default applies last"),
    (None, None, None, None, None, "nothing set and no default -> None"),
    ("  TRUE  ", None, None, None, "  TRUE  ", "raw value returned verbatim"),
]


def _resolve(env, cls, suite, default):
    original_class = settings._class_param
    original_suite = settings._suite_param
    try:
        settings.clear_all_overrides()
        if env is not None:
            set_override(_KEY, env)
        settings._class_param = lambda k: cls
        settings._suite_param = lambda k: suite
        return get_parameter(_KEY, default)
    finally:
        settings._class_param = original_class
        settings._suite_param = original_suite
        settings.clear_all_overrides()


@checkpoint(
    name="M2.1 parameter precedence truth table",
    component="foundation",
    source="M2.1",
)
def m21_parameter_precedence_truth_table():
    failures = []
    for env, cls, suite, default, expected, why in M21_TRUTH_TABLE:
        actual = _resolve(env, cls, suite, default)
        if actual != expected:
            failures.append(f"{why}: expected {expected!r}, got {actual!r}")
    assert not failures, "; ".join(failures)
