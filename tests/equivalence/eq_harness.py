"""Equivalence harness core (spec task 1.6).

The harness is the strangler gate: every migrated component must pass its
checkpoints (executable versions of the M0-M2.1 behaviours) before the next
component begins.

Three pieces:
  1. CheckpointRegistry  - named, individually pass/fail checkpoints tagged by component
  2. run_gate            - aggregates one component's checkpoints into a go/no-go result
  3. diff_outputs        - Java-vs-Python output comparison helper

Design rule: a gate with ZERO checkpoints FAILS. Code merely existing does not
mean a component is migrated - behaviour must be validated.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Checkpoint:
    name: str
    component: str
    source: str  # the M-doc / property the checkpoint encodes, e.g. "M2.1"
    func: Callable[[], None]  # raises AssertionError (or anything) on failure


@dataclass(frozen=True)
class CheckpointResult:
    name: str
    component: str
    source: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class GateResult:
    component: str
    results: tuple[CheckpointResult, ...]

    @property
    def passed(self) -> bool:
        return len(self.results) > 0 and all(r.passed for r in self.results)

    def report(self) -> str:
        if not self.results:
            return (
                f"GATE {self.component}: FAIL "
                "(no checkpoints registered - nothing was validated)"
            )
        lines = [f"GATE {self.component}: {'PASS' if self.passed else 'FAIL'}"]
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            line = f"  [{status}] {r.name} ({r.source})"
            if r.detail:
                line += f" -- {r.detail}"
            lines.append(line)
        return "\n".join(lines)


def run_checkpoint(cp: Checkpoint) -> CheckpointResult:
    """Run one checkpoint. Any exception is a FAIL with a readable detail."""
    try:
        cp.func()
    except AssertionError as exc:
        return CheckpointResult(cp.name, cp.component, cp.source, False, str(exc) or "assertion failed")
    except Exception as exc:  # noqa: BLE001 - a crashing checkpoint is a failing checkpoint
        return CheckpointResult(
            cp.name, cp.component, cp.source, False, f"{type(exc).__name__}: {exc}"
        )
    return CheckpointResult(cp.name, cp.component, cp.source, True)


class CheckpointRegistry:
    def __init__(self) -> None:
        self._checkpoints: dict[str, Checkpoint] = {}

    def register(
        self, name: str, component: str, source: str, func: Callable[[], None]
    ) -> None:
        if name in self._checkpoints:
            raise ValueError(f"checkpoint already registered: {name!r}")
        self._checkpoints[name] = Checkpoint(name, component, source, func)

    def for_component(self, component: str) -> list[Checkpoint]:
        return [c for c in self._checkpoints.values() if c.component == component]

    def run_gate(self, component: str) -> GateResult:
        results = tuple(run_checkpoint(c) for c in self.for_component(component))
        return GateResult(component, results)


DEFAULT_REGISTRY = CheckpointRegistry()


def checkpoint(
    name: str,
    component: str,
    source: str,
    registry: CheckpointRegistry | None = None,
) -> Callable[[Callable[[], None]], Callable[[], None]]:
    """Decorator: register a function as a named checkpoint."""

    def decorator(func: Callable[[], None]) -> Callable[[], None]:
        (registry or DEFAULT_REGISTRY).register(name, component, source, func)
        return func

    return decorator


def diff_outputs(java: Any, python: Any, path: str = "$") -> list[str]:
    """Return human-readable differences between a Java-side and Python-side output.

    An empty list means the outputs are equivalent. Dicts and lists are compared
    recursively; the path shows exactly where they diverge.
    """
    diffs: list[str] = []
    if isinstance(java, dict) and isinstance(python, dict):
        for key in sorted(set(java) | set(python), key=str):
            if key not in python:
                diffs.append(f"{path}.{key}: missing in python (java={java[key]!r})")
            elif key not in java:
                diffs.append(f"{path}.{key}: missing in java (python={python[key]!r})")
            else:
                diffs.extend(diff_outputs(java[key], python[key], f"{path}.{key}"))
    elif isinstance(java, (list, tuple)) and isinstance(python, (list, tuple)):
        if len(java) != len(python):
            diffs.append(f"{path}: length java={len(java)} python={len(python)}")
        for i, (j, p) in enumerate(zip(java, python)):
            diffs.extend(diff_outputs(j, p, f"{path}[{i}]"))
    elif java != python:
        diffs.append(f"{path}: java={java!r} python={python!r}")
    return diffs


def assert_equivalent(java: Any, python: Any, label: str = "output") -> None:
    """Raise AssertionError listing every difference (for use inside checkpoints)."""
    diffs = diff_outputs(java, python)
    assert not diffs, f"{label} differs: " + "; ".join(diffs)

