"""Foundation equivalence gate (runs the registered foundation checkpoints under pytest)."""

import eq_checkpoints  # noqa: F401  (importing registers the checkpoints)
from eq_harness import DEFAULT_REGISTRY


def test_foundation_gate_passes():
    result = DEFAULT_REGISTRY.run_gate("foundation")
    assert result.passed, "\n" + result.report()
