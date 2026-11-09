"""Generate the same synthetic log for both arms; no random or external input."""
import json
from pathlib import Path
import sys


def content():
    records = [{"request_id": f"noise-{n}", "event": "heartbeat", "worker": n % 4}
               for n in range(1200)]
    records[419:419] = [
        {"request_id": "r41", "event": "submit", "route": "publish", "role": "editor", "payload": "alpha"},
        {"request_id": "r41", "event": "reply", "status": "accepted", "pending": ["r41"], "committed": []},
        {"request_id": "r42", "event": "submit", "route": "publish", "role": "viewer", "payload": "beta"},
        {"request_id": "r42", "event": "reply", "status": "forbidden", "pending": ["r41"], "committed": []},
        {"request_id": "r41", "event": "flush", "pending": [], "committed": ["r41"]},
    ]
    return "\n".join(json.dumps(record) for record in records) + "\n"


if __name__ == "__main__":
    destination = Path(sys.argv[1])
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content())
