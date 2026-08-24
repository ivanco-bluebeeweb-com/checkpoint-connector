"""Chat functions for Check Point Connector: connection management (single
Management Server surface, session-based auth via login -> sid). Built on
checkpoint_client.py / schemas.py, following the same shape as Fortinet/
Palo Alto Networks Connector's handlers_connection.py.
"""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import checkpoint_client as cc
from app import ext, chat
from schemas import (
    NoParams,
    ConnectCheckpointParams,
    ProviderConnection, ProviderConnectionList,
    DisconnectParams, DeleteResult,
)

_SECRET_NAME = "checkpoint_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


async def _resolve_connection(ctx, connection_id: str = "") -> dict | None:
    connections = await _load_connections(ctx)
    if not connections:
        return None
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        return None
    return connections[0]


async def _authed(ctx, connection_id: str = "") -> dict | ActionResult:
    """Resolve the stored connection dict for a call. checkpoint_client.call()
    handles 401 lazy re-login transparently -- callers must run
    _persist_if_refreshed(ctx, conn) afterward to save a rotated sid."""
    conn = await _resolve_connection(ctx, connection_id)
    if conn is None:
        return ActionResult(success=False, error=cc._MESSAGES[cc.ACCOUNT_MISSING])
    return conn


async def _persist_if_refreshed(ctx, conn: dict) -> None:
    if conn.pop("_sid_refreshed", False):
        connections = await _load_connections(ctx)
        for c in connections:
            if c.get("id") == conn.get("id"):
                c["sid"] = conn.get("sid", "")
        await _save_connections(ctx, connections)


@chat.function(
    "connect_checkpoint",
    "Connect a Check Point Security Management Server (or Multi-Domain Server) by saving its host and admin credentials, after exchanging them once for a session id.",
    action_type="write",
    data_model=ProviderConnection,
)
async def connect_checkpoint(ctx, params: ConnectCheckpointParams) -> ActionResult:
    try:
        sid = await cc.login(ctx, params.host, params.username, params.password, params.domain)
    except cc.ClientFail as exc:
        return ActionResult(success=False, error=exc.message())
    connections = await _load_connections(ctx)
    conn_id = str(uuid.uuid4())
    label = params.label or params.host
    connections.append({
        "id": conn_id, "host": params.host, "username": params.username,
        "password": params.password, "domain": params.domain,
        "sid": sid, "label": label,
    })
    await _save_connections(ctx, connections)
    return ActionResult(success=True, data=ProviderConnection(
        id=conn_id, title=label, connected=True, detail=params.host,
    ))


@chat.function(
    "list_connections",
    "List the connected Check Point Management Server(s).",
    action_type="read",
    data_model=ProviderConnectionList,
)
async def list_connections(ctx, params: NoParams) -> ActionResult:
    connections = await _load_connections(ctx)
    items = [
        ProviderConnection(
            id=c.get("id", ""), title=c.get("label", "") or c.get("host", ""),
            connected=True, detail=c.get("host", ""),
        )
        for c in connections
    ]
    return ActionResult(success=True, data=ProviderConnectionList(items=items))


@chat.function(
    "disconnect_checkpoint",
    "Disconnect a Check Point Management Server: deletes the saved session credentials. Nothing on the server itself is changed.",
    action_type="write",
    data_model=DeleteResult,
)
async def disconnect_checkpoint(ctx, params: DisconnectParams) -> ActionResult:
    connections = await _load_connections(ctx)
    target = next((c for c in connections if c.get("id") == params.connection_id), None)
    if target is None:
        return ActionResult(success=False, error="Connection not found.")
    await cc.logout(ctx, target)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    await _save_connections(ctx, remaining)
    return ActionResult(success=True, data=DeleteResult(deleted=True))
