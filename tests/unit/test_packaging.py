"""Install/packaging contract tests (spec task 1.2).

These verify the Day-1 deliverable: the ita_pw package is importable from the
installed environment, its subpackages exist, and the pytest plugin entry point
is wired. They are the first checkpoint the equivalence harness will build on.
"""
import importlib

import ita_pw

def test_ita_pw_is_importable():
    """The package installs and imports (proves the build + install contract)."""
    assert ita_pw is not None

def test_all_subpackages_import():
    """Every declared subpackage is a real importable package."""
    subpackages = [
        "core", "pages", "plugin", "events", "reporting",
        "data", "results_api", "sharepoint", "genai_summary", "integrations",
    ]
    for name in subpackages:
        module = importlib.import_module(f"ita_pw.{name}")
        assert module is not None, f"ita_pw.{name} failed to import"

def test_pytest_plugin_entrypoint_is_registered(pytestconfig):
    """The pytest11 entry point auto-registers ita_pw.plugin."""
    plugin = pytestconfig.pluginmanager.get_plugin("ita_pw")
    assert plugin is not None, "ita_pw plugin was not auto-discovered by pytest"
