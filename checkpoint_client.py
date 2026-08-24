"""Check Point Management API (web_api) client -- session-based auth
(login -> sid, sent as X-chkp-sid on every subsequent request), with
transparent re-login on session expiry. WHY `ctx.http.*`, NOT a raw
`httpx` client -- same convention as every other connector in this
portfolio: the SDK's own async HTTP client goes through the platform's
sandboxed egress path.

Every Check Point Management API operation is a POST to
`/web_api/<command>` with a JSON body (no GET endpoints, no query
params) -- e.g. `POST /web_api/show-hosts`, `POST /web_api/add-host`,
`POST /web_api/publish`. This module wraps that single-shape convention
in one `call()` helper plus a login/session-refresh layer.
"""
from __future__ import annotations

from typing import Any

ACCOUNT_MISSING = "CHKP_ACCOUNT_MISSING"
SESSION_EXPIRED = "CHKP_SESSION_EXPIRED"
AUTH_REJECTED = "CHKP_AUTH_REJECTED"
PERMISSION_DENIED = "CHKP_PERMISSION_DENIED"
NOT_FOUND = "CHKP_NOT_FOUND"
VALIDATION_FAILED = "CHKP_VALIDATION_FAILED"
RESPONSE_UNEXPECTED = "CHKP_RESPONSE_UNEXPECTED"
UNREACHABLE = "CHKP_UNREACHABLE"
RATE_LIMITED = "CHKP_RATE_LIMITED"
BACKEND_5XX = "CHKP_BACKEND_5XX"
BACKEND_TIMEOUT = "CHKP_BACKEND_TIMEOUT"

_MESSAGES = {
    ACCOUNT_MISSING: "No Check Point connection is set up yet.",
    SESSION_EXPIRED: "The Check Point session expired and could not be renewed automatically.",
    AUTH_REJECTED: "Check Point rejected these credentials. Check the host/username/password/domain.",
    PERMISSION_DENIED: "This Check Point administrator account does not have permission for this operation.",
    NOT_FOUND: "That object was not found on the connected Check Point Management Server.",
    VALIDATION_FAILED: "Check Point rejected the request -- check the field values.",
    RESPONSE_UNEXPECTED: "Check Point returned an unexpected response.",
    UNREACHABLE: "Could not reach the Check Point Management Server -- check the host and network path.",
    RATE_LIMITED: "Too many requests to the Check Point Management Server -- try again shortly.",
    BACKEND_5XX: "The Check Point Management Server reported an internal error.",
    BACKEND_TIMEOUT: "The Check Point Management Server did not respond in time.",
}


class ClientFail(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")

    def message(self) -> str:
        base = _MESSAGES.get(self.code, "Check Point request failed.")
        return f"{base} ({self.detail})" if self.detail else base


def _classify_status(status: int) -> str:
    if status == 401:
        return SESSION_EXPIRED
    if status == 403:
        return PERMISSION_DENIED
    if status == 404:
        return NOT_FOUND
    if status == 400:
        return VALIDATION_FAILED
    if status == 429:
        return RATE_LIMITED
    if 500 <= status < 600:
        return BACKEND_5XX
    return RESPONSE_UNEXPECTED


async def login(ctx, host: str, username: str, password: str, domain: str = "") -> str:
    """Exchange username/password for a session id (sid)."""
    body: dict[str, Any] = {"user": username, "password": password}
    if domain:
        body["domain"] = domain
    url = f"{host.rstrip('/')}/web_api/login"
    try:
        resp = await ctx.http.post(url, json=body, timeout=30)
    except Exception as exc:  # noqa: BLE001
        raise ClientFail(UNREACHABLE, str(exc)) from exc
    if resp.status_code == 401 or resp.status_code == 400:
        raise ClientFail(AUTH_REJECTED)
    if resp.status_code >= 400:
        raise ClientFail(_classify_status(resp.status_code))
    data = resp.json()
    sid = data.get("sid")
    if not sid:
        raise ClientFail(RESPONSE_UNEXPECTED, "login response had no sid")
    return sid


async def logout(ctx, conn: dict) -> None:
    try:
        await call(ctx, conn, "logout", {})
    except ClientFail:
        pass


async def call(ctx, conn: dict, command: str, body: dict[str, Any] | None = None, *, _retried: bool = False) -> dict:
    """POST /web_api/<command> with the stored sid. On a 401 (session
    expired), transparently re-login once and retry -- lazy-refresh, same
    convention as this portfolio's OAuth2 client_credentials connectors,
    but the trigger is Check Point's own session-expiry status, not an
    expired JWT.
    """
    host = conn.get("host", "")
    sid = conn.get("sid", "")
    url = f"{host.rstrip('/')}/web_api/{command}"
    headers = {"X-chkp-sid": sid, "Content-Type": "application/json"}
    try:
        resp = await ctx.http.post(url, json=body or {}, headers=headers, timeout=60)
    except Exception as exc:  # noqa: BLE001
        raise ClientFail(UNREACHABLE, str(exc)) from exc

    if resp.status_code == 401 and not _retried:
        new_sid = await login(ctx, host, conn.get("username", ""), conn.get("password", ""), conn.get("domain", ""))
        conn["sid"] = new_sid
        conn["_sid_refreshed"] = True
        return await call(ctx, conn, command, body, _retried=True)

    if resp.status_code >= 400:
        try:
            payload = resp.json()
            detail = payload.get("message", "") or str(payload.get("errors", ""))
        except Exception:  # noqa: BLE001
            detail = resp.text[:200] if hasattr(resp, "text") else ""
        raise ClientFail(_classify_status(resp.status_code), detail)

    try:
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        raise ClientFail(RESPONSE_UNEXPECTED, str(exc)) from exc
