"""Explicit, bounded single-page retrieval; remote content is never executed."""

from __future__ import annotations

import hashlib
from http.client import HTTPException
import math
from pathlib import Path
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from .common import AgfError


MAX_REDIRECTS = 3
ROBOTS_MAX_BYTES = 64 * 1024
USER_AGENT = "agf-webfetch/1.0"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _url(value):
    if not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise AgfError("URL must be HTTP(S) without control characters.")
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            raise ValueError("HTTP(S) URL required")
        if parts.username is not None or parts.password is not None:
            raise ValueError("URL userinfo is not supported")
        host = parts.hostname.encode("idna").decode("ascii").lower()
        supplied_port = parts.port
        port = supplied_port if supplied_port is not None else (443 if parts.scheme.lower() == "https" else 80)
        if not 1 <= port <= 65535:
            raise ValueError("invalid port")
    except (ValueError, UnicodeError) as exc:
        raise AgfError(f"Invalid fetch URL: {exc}") from exc
    authority = f"[{host}]" if ":" in host else host
    if parts.port is not None:
        authority += f":{parts.port}"
    scheme = parts.scheme.lower()
    return urlunsplit((scheme, authority, parts.path or "/", parts.query, "")), (scheme, host, port)


def _hosts(values):
    result = set()
    for value in values:
        try:
            parts = urlsplit("//" + value)
            if not parts.hostname or parts.username is not None or parts.password is not None or parts.port is not None or parts.path or parts.query or parts.fragment:
                raise ValueError("use a hostname without a scheme, port, path or userinfo")
            result.add(parts.hostname.encode("idna").decode("ascii").lower())
        except (ValueError, UnicodeError, TypeError) as exc:
            raise AgfError(f"Invalid allow-host: {exc}") from exc
    return result


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise AgfError("Fetch time budget exhausted; no page was saved.")
    return remaining


def _body(response, limit, deadline):
    if response.headers.get("Content-Encoding", "identity").lower() not in {"", "identity"}:
        raise AgfError("Compressed HTTP responses are unsupported; no page was saved.")
    length = response.headers.get("Content-Length")
    try:
        expected = int(length) if length is not None else None
    except ValueError as exc:
        raise AgfError("Invalid HTTP Content-Length; no page was saved.") from exc
    if expected is not None and (expected < 0 or expected > limit):
        raise AgfError(f"Response exceeds max-bytes ({limit}) or has an invalid length; no page was saved.")
    pieces, total = [], 0
    while True:
        _remaining(deadline)
        # read1 returns available data rather than waiting to fill a large read.
        piece = response.read1(min(64 * 1024, limit - total + 1))
        if not piece:
            break
        pieces.append(piece)
        total += len(piece)
        if total > limit:
            raise AgfError(f"Response exceeds max-bytes ({limit}); no page was saved.")
    if expected is not None and expected != total:
        raise AgfError("Incomplete HTTP response; no page was saved.")
    return b"".join(pieces)


def _chain(opener, url, origin, allowed, deadline, limit, before=None):
    visited, redirects = set(), []
    for hop in range(MAX_REDIRECTS + 1):
        current, destination = _url(url)
        if destination != origin and destination[1] not in allowed:
            raise AgfError("Cross-origin redirect requires an explicit --allow-host.")
        if origin[0] == "https" and destination[0] != "https":
            raise AgfError("HTTPS redirects may not downgrade to HTTP.")
        if current in visited:
            raise AgfError("Redirect loop; no page was saved.")
        visited.add(current)
        if before:
            before(current)
        request = Request(current, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
        try:
            response = opener.open(request, timeout=_remaining(deadline))
        except HTTPError as exc:
            response = exc
        with response:
            status = response.getcode()
            if status in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location")
                if not location or hop == MAX_REDIRECTS:
                    raise AgfError("Missing redirect Location or redirect limit exceeded; no page was saved.")
                url = urljoin(current, location)
                redirects.append({"url": current, "http_status": status, "location": url})
                continue
            payload = _body(response, limit, deadline) if 200 <= status < 300 else b""
            return {"url": current, "http_status": status,
                    "content_type": response.headers.get("Content-Type", ""),
                    "charset": response.headers.get_content_charset(), "redirects": redirects}, payload
    raise AgfError("Redirect limit exceeded.")


def fetch(url, output, *, execute=False, timeout=20, max_bytes=2 * 1024 * 1024, allow_hosts=()):
    current, origin = _url(url)
    allowed = _hosts(allow_hosts)
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise AgfError("timeout must be a positive finite number.")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
        raise AgfError("max-bytes must be a positive integer.")
    target = Path(output).absolute()
    if target.exists() or target.is_symlink():
        raise AgfError(f"Existing output is preserved: {target}")
    result = {"status": "PLAN", "requested_url": current, "output": str(target),
              "executed": execute, "timeout": timeout, "max_bytes": max_bytes,
              "max_redirects": MAX_REDIRECTS, "allow_hosts": sorted(allowed),
              "robots_policy": "Respect robots.txt; 404/410 means no rules, uncertainty stops retrieval."}
    if not execute:
        return result
    opener = build_opener(_NoRedirect(), HTTPSHandler(context=ssl.create_default_context()))
    deadline = time.monotonic() + timeout
    policies, robots = {}, []

    def check_robots(page):
        _, page_origin = _url(page)
        if page_origin not in policies:
            parsed = urlsplit(page)
            robot_url = urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))
            info, data = _chain(opener, robot_url, page_origin, allowed, deadline, ROBOTS_MAX_BYTES)
            status = info["http_status"]
            if status in {404, 410}:
                policy = None
                state = "NO_RULES"
            elif 200 <= status < 300:
                policy = RobotFileParser()
                policy.parse(data.decode("utf-8-sig", errors="strict").splitlines())
                state = "CHECKED"
            else:
                raise AgfError(f"Cannot confirm robots permission (HTTP {status}); no page was saved.")
            policies[page_origin] = policy
            robots.append({"url": info["url"], "http_status": status, "status": state})
        policy = policies[page_origin]
        if policy is not None and not policy.can_fetch(USER_AGENT, page):
            raise AgfError("robots.txt disallows this URL; no page was saved.")

    try:
        info, payload = _chain(opener, current, origin, allowed, deadline, max_bytes, check_robots)
    except (URLError, OSError, HTTPException, UnicodeError, ValueError) as exc:
        raise AgfError(f"Fetch or robots check failed; no page was saved: {exc}") from exc
    if not 200 <= info["http_status"] < 300:
        raise AgfError(f"Page returned HTTP {info['http_status']}; no page was saved.")
    # Complete retrieval and size checks happen before creating any output.
    created = False
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            created = True
            stream.write(payload)
    except OSError as exc:
        if created:
            target.unlink(missing_ok=True)
        raise AgfError(f"Cannot publish fetched page: {exc}") from exc
    result.update(info)
    result.update({"status": "FETCHED", "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                   "robots": robots, "trust": "Untrusted source data; no scripts, cookies or login flow were executed."})
    return result


def register(source_subparsers):
    item = source_subparsers.add_parser("fetch", help="Plan or explicitly retrieve one bounded static page")
    item.add_argument("url")
    item.add_argument("--output", required=True)
    item.add_argument("--execute", action="store_true", help="Permit network requests and creation of the output")
    item.add_argument("--timeout", type=float, default=20, help="Shared time budget checked between network reads")
    item.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)
    item.add_argument("--allow-host", action="append", default=[], help="Explicitly allow redirects to this hostname (repeatable)")
    item.set_defaults(func=lambda a: fetch(a.url, a.output, execute=a.execute, timeout=a.timeout,
                                          max_bytes=a.max_bytes, allow_hosts=a.allow_host))
