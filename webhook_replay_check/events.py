"""Sample events. All data here is invented example data."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    id: str        # unique id given by the sender
    order_id: str  # the object the event is about
    type: str      # "payment.created" | "payment.paid" | "payment.refunded"
    seq: int       # per-order sequence number from the sender
    amount: int    # cents


def sample_events() -> list[Event]:
    """Three invented orders with a normal life cycle."""
    return [
        Event("evt_001", "ord_A", "payment.created", 1, 10_000),
        Event("evt_002", "ord_A", "payment.paid", 2, 10_000),
        Event("evt_003", "ord_B", "payment.created", 1, 4_500),
        Event("evt_004", "ord_B", "payment.paid", 2, 4_500),
        Event("evt_005", "ord_B", "payment.refunded", 3, 4_500),
        Event("evt_006", "ord_C", "payment.created", 1, 799),
    ]
