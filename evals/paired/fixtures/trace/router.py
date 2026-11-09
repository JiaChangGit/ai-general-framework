from dataclasses import dataclass


@dataclass
class Request:
    request_id: str
    route: str
    role: str
    payload: str


class Router:
    def __init__(self, capacity=2):
        self.capacity = capacity
        self.pending = []
        self.committed = set()

    def submit(self, request):
        route = {"publish": "write", "fetch": "read"}.get(request.route, request.route)
        if route == "write" and request.role != "editor":
            return {"request_id": request.request_id, "status": "forbidden"}
        if request.request_id in self.committed:
            return {"request_id": request.request_id, "status": "duplicate"}
        if len(self.pending) >= self.capacity:
            return {"request_id": request.request_id, "status": "busy"}
        self.pending.append((request.request_id, route, request.payload))
        return {"request_id": request.request_id, "status": "accepted"}

    def flush_one(self):
        request_id, route, payload = self.pending.pop(0)
        self.committed.add(request_id)
        return request_id, route, payload
