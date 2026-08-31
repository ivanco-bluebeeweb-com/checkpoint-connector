"""Chat functions for Check Point object management: hosts, networks,
groups, services. Every write here lives only in the current session
until publish_changes is called (see handlers_access.py). Built on
checkpoint_client.py / schemas.py.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import checkpoint_client as cc
from app import chat
from handlers_connection import _authed, _persist_if_refreshed
from schemas import (
    ListHostsParams, Host, HostList,
    CreateHostParams, UpdateHostParams, DeleteHostParams, DeleteResult,
    ListNetworksParams, Network, NetworkList,
    CreateNetworkParams, UpdateNetworkParams, DeleteNetworkParams,
    ListGroupsParams, Group, GroupList, CreateGroupParams,
    ListServicesParams, ServiceObj, ServiceList,
    CreateServiceParams, DeleteServiceParams,
)


@chat.function(
    "list_hosts",
    "List host objects defined on the connected Check Point Management Server.",
    action_type="read",
    data_model=HostList,
)
async def list_hosts(ctx, params: ListHostsParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "show-hosts", {"limit": 500})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    items = [
        Host(id=h.get("uid", ""), title=h.get("name", ""), name=h.get("name", ""), ip_address=h.get("ipv4-address", ""))
        for h in data.get("objects", [])
    ]
    return ActionResult.success(HostList(title=f"{len(items)} host(s)", items=items), summary="Hosts listed.")


@chat.function(
    "create_host",
    "Create a new host object on the connected Check Point Management Server. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=Host,
)
async def create_host(ctx, params: CreateHostParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "add-host", {"name": params.name, "ip-address": params.ip_address})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(Host(id=data.get("uid", ""), title=params.name, name=params.name, ip_address=params.ip_address), summary="Host created.")


@chat.function(
    "update_host",
    "Update an existing host object's IP address. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=Host,
)
async def update_host(ctx, params: UpdateHostParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        await cc.call(ctx, conn, "set-host", {"name": params.name, "ip-address": params.ip_address})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(Host(id=params.name, title=params.name, name=params.name, ip_address=params.ip_address), summary="Host updated.")


@chat.function(
    "delete_host",
    "Permanently delete a host object by name. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=DeleteResult,
)
async def delete_host(ctx, params: DeleteHostParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        await cc.call(ctx, conn, "delete-host", {"name": params.name})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(DeleteResult(id=params.name, title=params.name, deleted=True), summary="Host deleted.")


@chat.function(
    "list_networks",
    "List network objects defined on the connected Check Point Management Server.",
    action_type="read",
    data_model=NetworkList,
)
async def list_networks(ctx, params: ListNetworksParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "show-networks", {"limit": 500})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    items = [
        Network(
            id=n.get("uid", ""), title=n.get("name", ""), name=n.get("name", ""),
            subnet=n.get("subnet4", ""), mask=n.get("subnet-mask", ""),
        )
        for n in data.get("objects", [])
    ]
    return ActionResult.success(NetworkList(title=f"{len(items)} network(s)", items=items), summary="Networks listed.")


@chat.function(
    "create_network",
    "Create a new network object on the connected Check Point Management Server. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=Network,
)
async def create_network(ctx, params: CreateNetworkParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "add-network", {
            "name": params.name, "subnet": params.subnet, "subnet-mask": params.mask,
        })
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(Network(id=data.get("uid", ""), title=params.name, name=params.name, subnet=params.subnet, mask=params.mask), summary="Network created.")


@chat.function(
    "update_network",
    "Update an existing network object's subnet/mask. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=Network,
)
async def update_network(ctx, params: UpdateNetworkParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    body = {"name": params.name}
    if params.subnet:
        body["subnet"] = params.subnet
    if params.mask:
        body["subnet-mask"] = params.mask
    try:
        await cc.call(ctx, conn, "set-network", body)
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(Network(id=params.name, title=params.name, name=params.name, subnet=params.subnet, mask=params.mask), summary="Network updated.")


@chat.function(
    "delete_network",
    "Permanently delete a network object by name. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=DeleteResult,
)
async def delete_network(ctx, params: DeleteNetworkParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        await cc.call(ctx, conn, "delete-network", {"name": params.name})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(DeleteResult(id=params.name, title=params.name, deleted=True), summary="Network deleted.")


@chat.function(
    "list_groups",
    "List group objects (named collections of hosts/networks) defined on the connected Check Point Management Server.",
    action_type="read",
    data_model=GroupList,
)
async def list_groups(ctx, params: ListGroupsParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        data = await cc.call(ctx, conn, "show-groups", {"limit": 500})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    items = [
        Group(id=g.get("uid", ""), title=g.get("name", ""), name=g.get("name", ""), member_count=len(g.get("members", [])))
        for g in data.get("objects", [])
    ]
    return ActionResult.success(GroupList(title=f"{len(items)} group(s)", items=items), summary="Groups listed.")


@chat.function(
    "create_group",
    "Create a new group object on the connected Check Point Management Server, optionally with initial members (by name). Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=Group,
)
async def create_group(ctx, params: CreateGroupParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    body = {"name": params.name}
    if params.members:
        body["members"] = params.members
    try:
        data = await cc.call(ctx, conn, "add-group", body)
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(Group(id=data.get("uid", ""), title=params.name, name=params.name, member_count=len(params.members)), summary="Group created.")


@chat.function(
    "list_services",
    "List TCP/UDP service (port) objects defined on the connected Check Point Management Server.",
    action_type="read",
    data_model=ServiceList,
)
async def list_services(ctx, params: ListServicesParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    try:
        tcp = await cc.call(ctx, conn, "show-services-tcp", {"limit": 500})
        udp = await cc.call(ctx, conn, "show-services-udp", {"limit": 500})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    items = [
        ServiceObj(id=s.get("uid", ""), title=s.get("name", ""), name=s.get("name", ""), protocol="tcp", port=s.get("port", ""))
        for s in tcp.get("objects", [])
    ] + [
        ServiceObj(id=s.get("uid", ""), title=s.get("name", ""), name=s.get("name", ""), protocol="udp", port=s.get("port", ""))
        for s in udp.get("objects", [])
    ]
    return ActionResult.success(ServiceList(title=f"{len(items)} service(s)", items=items), summary="Services listed.")


@chat.function(
    "create_service",
    "Create a new TCP or UDP service (port) object on the connected Check Point Management Server. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=ServiceObj,
)
async def create_service(ctx, params: CreateServiceParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    command = "add-service-tcp" if params.protocol == "tcp" else "add-service-udp"
    try:
        data = await cc.call(ctx, conn, command, {"name": params.name, "port": params.port})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(ServiceObj(id=data.get("uid", ""), title=params.name, name=params.name, protocol=params.protocol, port=params.port), summary="Service created.")


@chat.function(
    "delete_service",
    "Permanently delete a TCP or UDP service object by name. Changes are pending until publish_changes is called.",
    action_type="write",
    data_model=DeleteResult,
)
async def delete_service(ctx, params: DeleteServiceParams) -> ActionResult:
    conn = await _authed(ctx, params.connection_id)
    if isinstance(conn, ActionResult):
        return conn
    command = "delete-service-tcp" if params.protocol == "tcp" else "delete-service-udp"
    try:
        await cc.call(ctx, conn, command, {"name": params.name})
    except cc.ClientFail as e:
        return ActionResult.error(e.message())
    await _persist_if_refreshed(ctx, conn)
    return ActionResult.success(DeleteResult(id=params.name, title=params.name, deleted=True), summary="Service deleted.")
