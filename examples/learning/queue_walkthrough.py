"""Small in-memory tracing fixture; BuggyQueue deliberately violates atomicity.

Run from the framework root with:
    python examples/learning/queue_walkthrough.py

No files, processes, services, or network resources are changed.
"""

import json


class Queue:
    def __init__(self, capacity, pending=()):
        self.capacity = capacity
        self.pending = list(pending)

    def submit(self, jobs):
        batch = list(jobs)
        if not batch:
            return "empty"
        if len(set(batch)) != len(batch) or any(job in self.pending for job in batch):
            return "duplicate"
        return self._commit(batch)

    def _commit(self, batch):
        if len(self.pending) + len(batch) > self.capacity:
            return "capacity"
        self.pending.extend(batch)
        return "accepted"


class BuggyQueue(Queue):
    """Teaching defect: a later capacity failure leaves earlier jobs behind."""

    def _commit(self, batch):
        for job in batch:
            if len(self.pending) >= self.capacity:
                return "capacity"
            self.pending.append(job)
        return "accepted"


def observe(queue_type, jobs):
    queue = queue_type(capacity=2, pending=["A"])
    before = list(queue.pending)
    result = queue.submit(jobs)
    return {
        "implementation": queue_type.__name__,
        "input": jobs,
        "result": result,
        "before": before,
        "after": list(queue.pending),
    }


def main():
    for queue_type, jobs in (
        (Queue, ["B"]),
        (Queue, ["B", "C"]),
        (BuggyQueue, ["B", "C"]),
    ):
        print(json.dumps(observe(queue_type, jobs), ensure_ascii=False))


if __name__ == "__main__":
    main()
