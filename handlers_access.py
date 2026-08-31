"""Chat functions for Check Point access control: access layers, access
rules, and the mandatory publish/discard staging layer plus policy
installation to gateways. Built on checkpoint_client.py / schemas.py.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import checkpoint_client as cc
from app import chat
from handlers_connection import _authed, _persist_if_refreshed
from schemas import (
    ListAccessLayersParams, AccessLayer, AccessLayerList,
    ListAccessRulesParams, AccessRule, AccessRuleList,
    GetAccessRuleParams, CreateAccessRuleParams, UpdateAccessRuleParams,
    DeleteAccessRuleParams, DeleteResult,
    PublishChangesParams, DiscardChangesParams, PublishResult,
    ListPolicyPackagesParams, PolicyPackage, PolicyPackageList,
    InstallPolicyParams, GetTaskStatusParams, TaskStatus,
    ListGatewaysParams, Gateway, GatewayList,
)


def _rule_from(entry: dict) -> AccessRule:
    def _names(key: str) -> list[str]:
        return [m.get("name", "") for m in entry.get(key, []) if isinstance(m, dict)]
    return AccessRule(
        id=entry.get("uid", ""), title=entry.get("name", "") or entry.get("uid", ""),
        name=entry.get("name", ""), source=_names("source"), destination=_names("destination"),
        service=_names("service"), action=(entry.get("action") or {}).get("name", ""),
        enabled=bool(entry.get("enabled", True)),
    )


@chat.function(
    "list_access_layers",
    "List access control policy layers configured on the connected Check Point Management Server.",
    action_type="read",
    data_model=AccessLayerList,
)
async def list_access_layers(ctx, params: ListAccessLayersParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "show-access-layers", {"limit": 100})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    items = [AccessLayer(id=l.get("uid", ""), title=l.get("name", "")) for l in data.get("access-layers", [])]
    return ActionResult.success(AccessLayerList(title=f"{len(items)} access layer(s)", items=items), summary="Access layers listed.")


@chat.function(
    "list_access_rules",
    "List access control rules in one policy layer on the connected Check Point Management Server.",
    action_type="read",
    data_model=AccessRuleList,
)
async def list_access_rules(ctx, params: ListAccessRulesParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "show-access-rulebase", {"name": params.layer, "limit": 500})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    items = [_rule_from(r) for r in data.get("rulebase", []) if r.get("type") == "access-rule"]
    return ActionResult.success(AccessRuleList(title=f"{len(items)} rule(s) in '{params.layer}'", items=items), summary="Access rules listed.")


@chat.function(
    "get_access_rule",
    "Read one access control rule in full by name.",
    action_type="read",
    data_model=AccessRule,
)
async def get_access_rule(ctx, params: GetAccessRuleParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "show-access-rule", {"layer": params.layer, "name": params.name})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(_rule_from(data), summary="Access rule retrieved.")


@chat.function(
    "create_access_rule",
    "Create a new access control rule in a policy layer. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=AccessRule,
)
async def create_access_rule(ctx, params: CreateAccessRuleParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    body = {
        "layer": params.layer, "name": params.name,
        "source": params.source or ["Any"], "destination": params.destination or ["Any"],
        "service": params.service or ["Any"], "action": params.action,
    }
    if params.position:
        body["position"] = params.position
    try:
        data = await cc.call(ctx, conn, "add-access-rule", body)
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(_rule_from(data), summary="Access rule created.")


@chat.function(
    "update_access_rule",
    "Update an existing access control rule's action and/or enabled status. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=AccessRule,
)
async def update_access_rule(ctx, params: UpdateAccessRuleParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    body = {"layer": params.layer, "name": params.name}
    if params.action:
        body["action"] = params.action
    if params.enabled is not None:
        body["enabled"] = params.enabled
    try:
        data = await cc.call(ctx, conn, "set-access-rule", body)
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(_rule_from(data), summary="Access rule updated.")


@chat.function(
    "delete_access_rule",
    "Permanently delete an access control rule by name. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=DeleteResult,
)
async def delete_access_rule(ctx, params: DeleteAccessRuleParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        await cc.call(ctx, conn, "delete-access-rule", {"layer": params.layer, "name": params.name})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(DeleteResult(id=params.name, title=params.name, deleted=True), summary="Access rule deleted.")


@chat.function(
    "publish_changes",
    "Publish all pending changes in the current session so they become visible to other administrators/API sessions -- Check Point's mandatory staging step, same convention as a Fortinet/PAN-OS commit but scoped to the whole session, not one config unit.",
    action_type="write",
    data_model=PublishResult,
)
async def publish_changes(ctx, params: PublishChangesParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "publish", {})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    task_id = data.get("task-id", "")
    return ActionResult.success(PublishResult(id=task_id, title="Publish", task_id=task_id, status="pending"), summary="Publish changes done.")


@chat.function(
    "discard_changes",
    "Discard all pending (unpublished) changes in the current session, reverting to the last published state.",
    action_type="write",
    data_model=PublishResult,
)
async def discard_changes(ctx, params: DiscardChangesParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        await cc.call(ctx, conn, "discard", {})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(PublishResult(id="", title="Discard", status="discarded"), summary="Discard changes done.")


@chat.function(
    "list_policy_packages",
    "List policy packages defined on the connected Check Point Management Server.",
    action_type="read",
    data_model=PolicyPackageList,
)
async def list_policy_packages(ctx, params: ListPolicyPackagesParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "show-packages", {"limit": 100})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    items = [PolicyPackage(id=p.get("uid", ""), title=p.get("name", "")) for p in data.get("packages", [])]
    return ActionResult.success(PolicyPackageList(title=f"{len(items)} policy package(s)", items=items), summary="Policy packages listed.")


@chat.function(
    "install_policy",
    "Install a published policy package onto its target gateways/clusters -- an asynchronous operation; use get_task_status with the returned task_id to check progress.",
    action_type="write",
    data_model=TaskStatus,
)
async def install_policy(ctx, params: InstallPolicyParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "install-policy", {
            "policy-package": params.policy_package, "targets": params.targets,
        })
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    task_id = data.get("task-id", "")
    return ActionResult.success(TaskStatus(id=task_id, title=f"Install policy task {task_id}", task_id=task_id, status="pending"), summary="Install policy done.")


@chat.function(
    "get_task_status",
    "Read the status of an asynchronous task (e.g. install_policy) by task id.",
    action_type="read",
    data_model=TaskStatus,
)
async def get_task_status(ctx, params: GetTaskStatusParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "show-task", {"task-id": params.task_id})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    tasks = data.get("tasks", [])
    task = tasks[0] if tasks else {}
    return ActionResult.success(TaskStatus(
        id=params.task_id, title=f"Task {params.task_id}", task_id=params.task_id,
        status=task.get("status", "unknown"), progress=task.get("progress-percentage", 0),
    ), summary="Task status retrieved.")


@chat.function(
    "list_gateways",
    "List gateway and cluster objects managed by the connected Check Point Management Server.",
    action_type="read",
    data_model=GatewayList,
)
async def list_gateways(ctx, params: ListGatewaysParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "show-gateways-and-servers", {"limit": 100})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    items = [
        Gateway(id=g.get("uid", ""), title=g.get("name", ""), ip_address=g.get("ipv4-address", ""), sofaware_version=g.get("version", ""))
        for g in data.get("objects", [])
    ]
    return ActionResult.success(GatewayList(title=f"{len(items)} gateway(s)/server(s)", items=items), summary="Gateways listed.")
