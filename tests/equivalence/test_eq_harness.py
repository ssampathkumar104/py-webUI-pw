"""Tests for the equivalence harness itself (spec task 1.6)."""

import pytest

from eq_harness import (
    CheckpointRegistry,
    assert_equivalent,
    checkpoint,
    diff_outputs,
)


def _passing():
    assert 1 == 1


def _failing():
    assert 1 == 2, "one is not two"


def _erroring():
    raise RuntimeError("boom")


# --- gate aggregation --------------------------------------------------------

def test_gate_passes_when_all_checkpoints_pass():
    reg = CheckpointRegistry()
    reg.register("a", "comp", "M0", _passing)
    reg.register("b", "comp", "M0", _passing)
    gate = reg.run_gate("comp")
    assert gate.passed
    assert all(r.passed for r in gate.results)


def test_one_failing_checkpoint_fails_the_gate_with_detail():
    reg = CheckpointRegistry()
    reg.register("ok", "comp", "M0", _passing)
    reg.register("bad", "comp", "M0", _failing)
    gate = reg.run_gate("comp")
    assert not gate.passed
    bad = [r for r in gate.results if r.name == "bad"][0]
    assert not bad.passed
    assert "one is not two" in bad.detail


def test_crashing_checkpoint_is_a_failure_not_a_harness_crash():
    reg = CheckpointRegistry()
    reg.register("crash", "comp", "M0", _erroring)
    gate = reg.run_gate("comp")
    assert not gate.passed
    assert "RuntimeError" in gate.results[0].detail
    assert "boom" in gate.results[0].detail


def test_empty_gate_fails():
    reg = CheckpointRegistry()
    gate = reg.run_gate("nothing-registered")
    assert not gate.passed
    assert "no checkpoints" in gate.report()


def test_gate_only_runs_its_own_component():
    reg = CheckpointRegistry()
    reg.register("mine", "comp-a", "M0", _passing)
    reg.register("other", "comp-b", "M0", _failing)
    assert reg.run_gate("comp-a").passed
    assert not reg.run_gate("comp-b").passed


def test_duplicate_checkpoint_name_is_rejected():
    reg = CheckpointRegistry()
    reg.register("dup", "comp", "M0", _passing)
    with pytest.raises(ValueError):
        reg.register("dup", "comp", "M0", _passing)


def test_decorator_registers_on_the_given_registry():
    reg = CheckpointRegistry()

    @checkpoint(name="decorated", component="comp", source="M0", registry=reg)
    def _cp():
        assert True

    assert [c.name for c in reg.for_component("comp")] == ["decorated"]


def test_report_lists_each_checkpoint_with_status():
    reg = CheckpointRegistry()
    reg.register("ok", "comp", "M1.3", _passing)
    reg.register("bad", "comp", "M1.4", _failing)
    report = reg.run_gate("comp").report()
    assert "GATE comp: FAIL" in report
    assert "[PASS] ok (M1.3)" in report
    assert "[FAIL] bad (M1.4)" in report


# --- diff helper -------------------------------------------------------------

def test_equal_outputs_have_no_diff():
    assert diff_outputs({"a": [1, 2], "b": "x"}, {"a": [1, 2], "b": "x"}) == []


def test_scalar_difference_reports_path_and_both_values():
    assert diff_outputs({"a": 1}, {"a": 2}) == ["$.a: java=1 python=2"]


def test_missing_keys_are_reported_on_each_side():
    diffs = diff_outputs({"only_java": 1}, {"only_python": 2})
    assert "$.only_java: missing in python (java=1)" in diffs
    assert "$.only_python: missing in java (python=2)" in diffs


def test_list_length_and_element_differences():
    diffs = diff_outputs([1, 2, 3], [1, 9])
    assert "$: length java=3 python=2" in diffs
    assert "$[1]: java=2 python=9" in diffs


def test_assert_equivalent_raises_with_all_differences():
    with pytest.raises(AssertionError) as exc:
        assert_equivalent({"a": 1, "b": 2}, {"a": 9, "b": 8}, label="report")
    message = str(exc.value)
    assert "report differs" in message
    assert "$.a" in message and "$.b" in message
