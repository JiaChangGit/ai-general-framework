import json
from pathlib import Path

policy = json.loads(Path("policy.json").read_text())
expires_at = 100 + policy["ttl_seconds"]
print({"expires_at": expires_at, "valid_at_125": 125 < expires_at})
assert expires_at == 130
assert 125 < expires_at
