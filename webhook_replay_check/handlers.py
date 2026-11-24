"""Two example handlers. A handler has apply(event) and snapshot()."""
from .events import Event

STATUS_BY_TYPE = {
    "payment.created": "pending",
    "payment.paid": "paid",
    "payment.refunded": "refunded",
}


class NaiveHandler:
    """Trusts every delivery: adds money on each 'paid' event and keeps the last status."""

    def __init__(self):
        self.status: dict[str, str] = {}
        self.revenue = 0

    def apply(self, e: Event) -> None:
        self.status[e.order_id] = STATUS_BY_TYPE[e.type]
        if e.type == "payment.paid":
            self.revenue += e.amount
        elif e.type == "payment.refunded":
            self.revenue -= e.amount

    def snapshot(self) -> dict:
        return {"status": dict(sorted(self.status.items())), "revenue": self.revenue}


class IdempotentHandler:
    """Drops repeated event ids and buffers events that arrive early (by seq)."""

    def __init__(self):
        self.seen: set[str] = set()
        self.next_seq: dict[str, int] = {}
        self.waiting: dict[str, dict[int, Event]] = {}
        self.status: dict[str, str] = {}
        self.revenue = 0

    def apply(self, e: Event) -> None:
        if e.id in self.seen:
            return
        self.seen.add(e.id)
        expected = self.next_seq.get(e.order_id, 1)
        if e.seq < expected:
            return
        self.waiting.setdefault(e.order_id, {})[e.seq] = e
        queue = self.waiting[e.order_id]
        while expected in queue:
            self._commit(queue.pop(expected))
            expected += 1
        self.next_seq[e.order_id] = expected

    def _commit(self, e: Event) -> None:
        self.status[e.order_id] = STATUS_BY_TYPE[e.type]
        if e.type == "payment.paid":
            self.revenue += e.amount
        elif e.type == "payment.refunded":
            self.revenue -= e.amount

    def snapshot(self) -> dict:
        return {"status": dict(sorted(self.status.items())), "revenue": self.revenue}
