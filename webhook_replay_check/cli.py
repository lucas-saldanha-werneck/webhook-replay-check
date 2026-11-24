"""Command line: python -m webhook_replay_check [--handler module:Class] [--runs N] [--seed N]"""
import argparse
import importlib
import json
import sys

from .events import sample_events
from .handlers import IdempotentHandler, NaiveHandler
from .replay import check


def load(spec: str):
    module, _, name = spec.partition(":")
    return getattr(importlib.import_module(module), name)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="webhook-replay-check", description=__doc__)
    p.add_argument("--handler", help="your handler as module:Class (needs apply(event) and snapshot())")
    p.add_argument("--runs", type=int, default=200)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args(argv)

    targets = (
        [(args.handler, load(args.handler))]
        if args.handler
        else [("NaiveHandler", NaiveHandler), ("IdempotentHandler", IdempotentHandler)]
    )
    events = sample_events()
    bad = 0
    for name, factory in targets:
        r = check(factory, events, runs=args.runs, seed=args.seed)
        verdict = "PASS" if r.failures == 0 else "FAIL"
        print(f"{verdict}  {name}: {r.failures}/{r.runs} noisy runs ended in a different state")
        if r.example:
            print("  expected:", json.dumps(r.example["expected"]))
            print("  got:     ", json.dumps(r.example["got"]))
            bad += 1
    return 1 if (args.handler and bad) else 0


if __name__ == "__main__":
    sys.exit(main())
