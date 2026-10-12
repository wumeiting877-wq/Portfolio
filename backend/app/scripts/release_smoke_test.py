"""Release smoke test against a running backend. Does not print secrets."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib import error, request

def resolve_base_url(argv: list[str] | None = None) -> str:
    """Prefer CLI, then BASE_URL, then SMOKE_BASE. Port 8010 is only the unset default."""
    parser = argparse.ArgumentParser(description="Release smoke test")
    parser.add_argument("--base-url", dest="base_url", default=None)
    parser.add_argument("base_url_positional", nargs="?", default=None)
    args, _unknown = parser.parse_known_args(argv)
    for candidate in (
        args.base_url,
        args.base_url_positional,
        os.environ.get("BASE_URL"),
        os.environ.get("SMOKE_BASE"),
    ):
        if candidate and str(candidate).strip():
            return str(candidate).strip().rstrip("/")
    return "http://127.0.0.1:8010"


BASE = "http://127.0.0.1:8010"
USERNAME = "admin"
PASSWORD = ""


def _request(method: str, path: str, *, token: str | None = None, body: dict | None = None):
    data = None
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=20) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload) if payload else {}
    except error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8") or "{}")


def main(argv: list[str] | None = None) -> int:
    global BASE, USERNAME, PASSWORD
    BASE = resolve_base_url(argv)
    USERNAME = os.environ.get("SMOKE_USERNAME", "admin")
    PASSWORD = os.environ.get("SMOKE_PASSWORD", "change_me")
    results: list[dict] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append({"name": name, "ok": ok, "detail": detail})
        print(f"{'PASS' if ok else 'FAIL'} {name} {detail}".strip())

    status, body = _request("GET", "/health")
    check("health", status == 200 and body.get("status") == "ok")

    status, body = _request("GET", "/health/db")
    check("health/db", status == 200 and body.get("status") == "ok")

    status, body = _request("GET", "/version")
    check(
        "version",
        status == 200
        and body.get("name") == "project-cost-hub"
        and body.get("version") == "1.0.0"
        and "secret" not in json.dumps(body).lower()
        and "password" not in json.dumps(body).lower(),
        f"version={body.get('version')}",
    )

    status, body = _request("POST", "/api/auth/login", body={"username": USERNAME, "password": PASSWORD})
    token = body.get("access_token") if status == 200 else None
    check("login", bool(token))
    if not token:
        print(json.dumps({"results": results, "passed": False}, ensure_ascii=False, indent=2))
        return 1

    status, body = _request("GET", "/api/projects?page=1&page_size=5", token=token)
    check("projects", status == 200 and "items" in body)

    status, body = _request("GET", "/api/resources?page=1&page_size=5", token=token)
    check("resources", status == 200 and "items" in body)

    status, body = _request("GET", "/api/expenses?page=1&page_size=5", token=token)
    check("expenses", status == 200 and "items" in body)

    status, body = _request("GET", "/api/statistics/overview", token=token)
    check("statistics", status == 200 and "amounts_by_currency" in body)

    raw_req = request.Request(
        BASE + "/api/exports/projects",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        method="GET",
    )
    try:
        with request.urlopen(raw_req, timeout=30) as response:
            export_ok = response.status == 200 and (
                "spreadsheet" in (response.headers.get("Content-Type") or "")
                or len(response.read()) > 0
            )
    except error.HTTPError:
        export_ok = False
    check("export", export_ok)

    status, body = _request("POST", "/api/notifications/refresh", token=token)
    check("notifications", status == 200 and "items" in body)

    passed = all(item["ok"] for item in results)
    print(json.dumps({"passed": passed, "count": len(results)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
