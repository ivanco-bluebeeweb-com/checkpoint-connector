"""Chat functions for Check Point Connector -- bulk operations and a
combined estate health audit (Tier 3 value-add), same shape as Fortinet/
Palo Alto Networks Connector's handlers_bulk_audit.py.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import checkpoint_client as cc
from app import chat
from handlers_connection import _authed, _load_connections, _persist_if_refreshed
from schemas import (
    BulkAccessRuleActionParams, BulkActionOutcome, BulkActionResult,
    AuditFinding, AuditReport, NoParams,
)


@chat.function(
    "bulk_access_rule_action",
    "Enable or disable several Check Point access rules in one call, by explicit rule names. Continues past per-item failures and reports each outcome, same convention as every other bulk_* tool in the portfolio.",
    action_type="write",
)
async def bulk_access_rule_action(ctx, params: BulkAccessRuleActionParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    items: list[BulkActionOutcome] = []
    for name in params.names:
        try:
            await cc.call(ctx, conn, "set-access-rule", {
                "name": name, "layer": params.layer, "enabled": not params.disabled,
            })
            items.append(BulkActionOutcome(id=name, ok=True))
        except cc.ClientFail as e:
            items.append(BulkActionOutcome(id=name, ok=False, error=e.message()))
    await _persist_if_refreshed(ctx, conn)
    return ActionResult(success=True, data=BulkActionResult(title="Bulk access rule status change", items=items))


@chat.function(
    "audit_checkpoint_estate",
    "Run a read-only health audit across all connected Check Point Management Servers: overly broad access rules (any/any with allow), rules with no logging, and unpublished pending changes.",
    action_type="read",
    data_model=AuditReport,
)
async def audit_checkpoint_estate(ctx, params: NoParams) -> ActionResult:
    connections = await _load_connections(ctx)
    if not connections:
        return ActionResult(success=False, error=cc._MESSAGES[cc.ACCOUNT_MISSING])
    findings: list[AuditFinding] = []
    for conn in connections:
        label = conn.get("label", "") or conn.get("host", "")
        try:
            layers = await cc.call(ctx, conn, "show-access-layers", {"limit": 50})
        except cc.ClientFail as e:
            findings.append(AuditFinding(id=f"{conn.get('id','')}:conn", severity="error", message=f"{label}: {e.message()}"))
            continue
        await _persist_if_refreshed(ctx, conn)
        for layer in layers.get("objects", []):
            layer_name = layer.get("name", "")
            try:
                rules = await cc.call(ctx, conn, "show-access-rulebase", {"name": layer_name, "limit": 500})
            except cc.ClientFail:
                continue
            for entry in rules.get("rulebase", []):
                if entry.get("type") != "access-rule":
                    continue
                name = entry.get("name", "") or entry.get("uid", "")
                action = (entry.get("action") or {}).get("name", "")
                src = entry.get("source", [])
                dst = entry.get("destination", [])
                src_any = any(m.get("name") == "Any" for m in src) if src else True
                dst_any = any(m.get("name") == "Any" for m in dst) if dst else True
                if action == "Accept" and src_any and dst_any:
                    findings.append(AuditFinding(
                        id=entry.get("uid", ""), severity="warning",
                        message=f"{label} / {layer_name}: rule '{name}' allows Any source to Any destination.",
                    ))
                if not entry.get("track", {}).get("type") or entry.get("track", {}).get("type", {}).get("name") == "None":
                    findings.append(AuditFinding(
                        id=f"{entry.get('uid','')}:log", severity="info",
                        message=f"{label} / {layer_name}: rule '{name}' has no logging configured.",
                    ))
        try:
            status = await cc.call(ctx, conn, "show-changes", {})
            if status.get("task-list") or status.get("changes"):
                findings.append(AuditFinding(
                    id=f"{conn.get('id','')}:pending", severity="warning",
                    message=f"{label}: there are unpublished pending changes in this session.",
                ))
        except cc.ClientFail:
            pass
    return ActionResult(success=True, data=AuditReport(title=f"{len(findings)} finding(s)", items=findings))
