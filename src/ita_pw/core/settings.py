"""Parameter/settings resolution for ita_pw (spec task 1.3).

Reproduces the Java BaseClass.getParameter cascade (see docs/M2.1):

    precedence:  env/CLI override  >  class-level param  >  suite/test-level param  >  default
    blank rule:  an empty or whitespace-only value is treated as "not set" and falls
                 through to the next tier (Java isBlank, NOT a null check)
    fail-soft:   never raises if a tier's source is unavailable — returns default/None
    raw value:   returns the string verbatim (no trim, no case change); callers decide
                 truthiness with their own exact comparisons

The class-level and suite-level tiers are STUBS today: they return None. They will be
wired to pytest markers / config when the plugin is built (later day). The env/CLI tier
is live, backed by an in-process override dict (checked first) then os.environ.
"""

from __future__ import annotations

import os

# In-process override layer for the env/CLI tier. Checked before os.environ.
# This is where a future CLI "-D"-style flag plugs in, and it lets tests inject
# values without mutating the real process environment.

_overrides: dict[str, str] = {}

def set_override(key:str, value:str) -> None:
    """Set an in-process env/CLI-tier override (highest precedence)."""
    _overrides[key] = value 

def clear_override(key:str) -> None:
    """Remove a single in-process override (no error if absent)."""
    _overrides.pop(key,None)

def clear_all_overrides() -> None:
    """Remove all in-process overrides (handy for test isolation)."""
    _overrides.clear()

def _is_blank(value: str | None) -> bool:
    """Java isBlank parity: None, empty, or whitespace-only counts as 'not set'."""
    return value is None or value.strip() == ""

# --- precedence tiers (each returns a raw string or None) --------------------

def _env_override(key: str) -> str | None:
    """Tier 1 (highest): in-process override, then environment variable (= Java -Dkey)."""
    if key in _overrides:
        return _overrides[key]
    return os.environ.get(key)

def _class_param(key: str) -> str | None:
    """Tier 2: Class level parameter. STUB - wired to the pytest plugin later."""
    return None 

def _suite_param(key: str) -> str | None:
    """Tier 3: suite/test-level parameter. STUB - wired to the pytest plugin later."""
    return None 

# --- public API --------------------------------------------------------------

def get_parameter(key: str, default: str | None = None) -> str | None:
    """Resolve a parameter by the Java getParameter cascade.

    Returns the first non-blank candidate in order:
        env/CLI override  >  class-level  >  suite/test-level  >  default

    A blank (empty/whitespace-only) candidate is skipped (Java isBlank).
    Never raises: on any unexpected error, falls back to default/None.
    The returned value is the raw string, unmodified.
    """
    try:
        for candidate in (_env_override(key), _class_param(key), _suite_param(key)):
            if not _is_blank(candidate):
                return candidate
        return default
    except Exception: # fail-soft, matching the Java try/catch -> null
        return default