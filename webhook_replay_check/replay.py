"""Build delivery schedules (duplicates, reordering) and compare final state."""
import random
from dataclasses import dataclass
from typing import Callable

from .events import Event


def schedule(events: list[Event], rng: random.Random, dup_rate: float = 0.5) -> list[Event]:
    """At-least-once delivery: some events repeat, and order is shuffled."""
    out = list(events)
    for e in events:
        while rng.random() < dup_rate:
            out.append(e)
    rng.shuffle(out)
    return out


def run(handler_factory: Callable, deliveries: list[Event]) -> dict:
    h = handler_factory()
    for e in deliveries:
        h.apply(e)
    return h.snapshot()


@dataclass
class Result:
    runs: int
    failures: int
    example: dict | None  # first failing case: deliveries, expected, got


def check(handler_factory: Callable, events: list[Event], runs: int = 200, seed: int = 1) -> Result:
    """Compare each noisy run with a clean in-order, once-only delivery."""
    ordered = sorted(events, key=lambda e: (e.order_id, e.seq))
    expected = run(handler_factory, ordered)
    rng = random.Random(seed)
    failures, example = 0, None
    for _ in range(runs):
        deliveries = schedule(events, rng)
        got = run(handler_factory, deliveries)
        if got != expected:
            failures += 1
            if example is None:
                example = {
                    "deliveries": [f"{e.id}({e.type})" for e in deliveries],
                    "expected": expected,
                    "got": got,
                }
    return Result(runs, failures, example)
