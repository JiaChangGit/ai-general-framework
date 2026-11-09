class Admitter:
    def __init__(self, capacity=1, ttl=10):
        self.capacity = capacity
        self.ttl = ttl
        self.pending = []
        self.seen_until = {}

    def admit(self, identifier, now):
        if self.seen_until.get(identifier, float("-inf")) > now:
            return "duplicate"
        self.seen_until[identifier] = now + self.ttl
        if len(self.pending) >= self.capacity:
            return "busy"
        self.pending.append(identifier)
        return "accepted"

    def drain(self):
        return self.pending.pop(0)
