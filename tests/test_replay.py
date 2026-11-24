import random

from webhook_replay_check.cli import main
from webhook_replay_check.events import Event, sample_events
from webhook_replay_check.handlers import IdempotentHandler, NaiveHandler
from webhook_replay_check.replay import check, run, schedule


def test_clean_delivery_gives_same_state_for_both_handlers():
    ordered = sorted(sample_events(), key=lambda e: (e.order_id, e.seq))
    assert run(NaiveHandler, ordered) == run(IdempotentHandler, ordered)


def test_expected_state_of_sample_data():
    ordered = sorted(sample_events(), key=lambda e: (e.order_id, e.seq))
    snap = run(IdempotentHandler, ordered)
    assert snap["status"] == {"ord_A": "paid", "ord_B": "refunded", "ord_C": "pending"}
    assert snap["revenue"] == 10_000  # A paid; B paid then refunded


def test_naive_handler_double_counts_a_duplicate():
    paid = Event("evt_x", "ord_Z", "payment.paid", 1, 1_000)
    assert run(NaiveHandler, [paid, paid])["revenue"] == 2_000
    assert run(IdempotentHandler, [paid, paid])["revenue"] == 1_000


def test_naive_handler_keeps_stale_status_when_events_swap():
    paid = Event("e2", "o", "payment.paid", 2, 100)
    created = Event("e1", "o", "payment.created", 1, 100)
    assert run(NaiveHandler, [paid, created])["status"]["o"] == "pending"
    assert run(IdempotentHandler, [paid, created])["status"]["o"] == "paid"


def test_check_fails_naive_and_passes_idempotent():
    events = sample_events()
    assert check(NaiveHandler, events).failures > 0
    assert check(IdempotentHandler, events).failures == 0


def test_check_returns_a_counterexample_for_failures():
    r = check(NaiveHandler, sample_events())
    assert r.example and r.example["expected"] != r.example["got"]


def test_schedule_is_repeatable_with_same_seed():
    ev = sample_events()
    a = schedule(ev, random.Random(7))
    b = schedule(ev, random.Random(7))
    assert a == b
    assert set(a) == set(ev)


def test_cli_default_runs_and_exits_zero(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "FAIL  NaiveHandler" in out and "PASS  IdempotentHandler" in out


def test_cli_exit_code_is_one_for_bad_custom_handler(capsys):
    assert main(["--handler", "webhook_replay_check.handlers:NaiveHandler"]) == 1
    assert main(["--handler", "webhook_replay_check.handlers:IdempotentHandler"]) == 0
