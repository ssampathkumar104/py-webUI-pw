"""Unit tests for the get_parameter cascade (spec task 1.4).

Covers: precedence (env > class > suite > default), blank==unset fall-through,
default/None fallback, raw-value fidelity, and fail-soft. Correctness Property 1
is additionally proven by a hypothesis property test on Day 3.
"""

import pytest

from ita_pw.core import settings
from ita_pw.core.settings import get_parameter, set_override


@pytest.fixture(autouse=True)
def _clean_overrides():
    """Isolate each test: clear in-process overrides before and after."""
    settings.clear_all_overrides()
    yield
    settings.clear_all_overrides()


# --- precedence --------------------------------------------------------------

def test_env_override_wins():
    set_override("browserName", "chrome")
    assert get_parameter("browserName") == "chrome"


def test_default_used_when_unset():
    assert get_parameter("missing", "firefox") == "firefox"


def test_none_when_unset_and_no_default():
    assert get_parameter("missing") is None


def test_env_override_beats_default():
    set_override("browserName", "webkit")
    assert get_parameter("browserName", "chrome") == "webkit"


# --- blank == unset (Java isBlank parity) ------------------------------------

def test_empty_string_override_falls_through_to_default():
    set_override("browserName", "")
    assert get_parameter("browserName", "chrome") == "chrome"


def test_whitespace_only_override_falls_through_to_default():
    set_override("browserName", "   ")
    assert get_parameter("browserName", "chrome") == "chrome"


# --- raw value fidelity (no normalization) -----------------------------------

def test_value_returned_verbatim_no_trim_or_case_change():
    set_override("headless", "  TRUE  ")
    assert get_parameter("headless") == "  TRUE  "


# --- env var tier (os.environ) ----------------------------------------------

def test_environment_variable_is_read(monkeypatch):
    monkeypatch.setenv("someKey", "fromEnv")
    assert get_parameter("someKey") == "fromEnv"


def test_override_takes_priority_over_environment(monkeypatch):
    monkeypatch.setenv("someKey", "fromEnv")
    set_override("someKey", "fromOverride")
    assert get_parameter("someKey") == "fromOverride"


# --- fail-soft ---------------------------------------------------------------

def test_fail_soft_returns_default_when_a_tier_raises(monkeypatch):
    def boom(_key):
        raise RuntimeError("simulated tier failure")
    monkeypatch.setattr(settings, "_class_param", boom)
    assert get_parameter("anything", "safe-default") == "safe-default"
