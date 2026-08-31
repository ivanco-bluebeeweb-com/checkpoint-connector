"""Pydantic params models + SDL entity contracts for Check Point Connector.
Module-scope params models per V17 federal invariant, same shape as
Fortinet/Palo Alto Networks Connector's schemas.py.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from imperal_sdk import sdl


class NoParams(BaseModel):
    """Explicit empty params model -- V17 disallows untyped handlers."""
    pass


# ──────────────────────────────────────────────────────────────────────────
# Connection
# ──────────────────────────────────────────────────────────────────────────


class ConnectCheckpointParams(BaseModel):
    host: str = Field(..., description="Check Point Management Server base URL, e.g. 'https://mgmt.company.com'.")
    username: str = Field(..., description="Management Server administrator username.")
    password: str = Field(..., description="Management Server administrator password (used to obtain a session id, not stored).")
    domain: str = Field("", description="Multi-Domain Security Management domain name -- leave empty for a standalone Management Server.")
    label: str = Field("", description="Optional friendly name for this connection.")


class ProviderConnection(sdl.Entity):
    id: str = ""
    title: str = ""
    connected: bool = False
    detail: str = ""


class ProviderConnectionList(sdl.Entity):
    id: str = "connection_list"
    title: str = ""
    items: list[ProviderConnection] = Field(default_factory=list)


class DisconnectParams(BaseModel):
    connection_id: str = Field(..., description="Connection id to disconnect, from list_connections.")


class DeleteResult(sdl.Entity):
    id: str = ""
    title: str = ""
    deleted: bool = False


class _Scoped(BaseModel):
    connection_id: str = Field("", description="Which connected Check Point Management Server to use. Omit if only one is connected.")


# ──────────────────────────────────────────────────────────────────────────
# Objects: hosts / networks / groups / services
# ──────────────────────────────────────────────────────────────────────────


class ListHostsParams(_Scoped):
    pass


class Host(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str = ""
    ipv4_address: str = ""


class HostList(sdl.Entity):
    id: str = "host_list"
    title: str = ""
    items: list[Host] = Field(default_factory=list)


class CreateHostParams(_Scoped):
    name: str = Field(..., description="New host object name.")
    ipv4_address: str = Field(..., description="IPv4 address, e.g. '10.0.0.5'.")


class UpdateHostParams(_Scoped):
    name: str = Field(..., description="Host object name to update.")
    ipv4_address: str = Field(..., description="New IPv4 address.")


class DeleteHostParams(_Scoped):
    name: str = Field(..., description="Host object name to permanently delete.")


class ListNetworksParams(_Scoped):
    pass


class Network(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str = ""
    subnet4: str = ""
    mask_length4: int = 0


class NetworkList(sdl.Entity):
    id: str = "network_list"
    title: str = ""
    items: list[Network] = Field(default_factory=list)


class CreateNetworkParams(_Scoped):
    name: str = Field(..., description="New network object name.")
    subnet4: str = Field(..., description="Network address, e.g. '10.0.0.0'.")
    mask_length4: int = Field(..., description="Subnet mask length, e.g. 24.")


class UpdateNetworkParams(_Scoped):
    name: str = Field(..., description="Network object name to update.")
    subnet4: str = Field("", description="New network address.")
    mask_length4: int = Field(0, description="New subnet mask length (0 = unchanged).")


class DeleteNetworkParams(_Scoped):
    name: str = Field(..., description="Network object name to permanently delete.")


class ListGroupsParams(_Scoped):
    pass


class Group(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str = ""
    member_count: int = 0


class GroupList(sdl.Entity):
    id: str = "group_list"
    title: str = ""
    items: list[Group] = Field(default_factory=list)


class CreateGroupParams(_Scoped):
    name: str = Field(..., description="New group name.")
    members: list[str] = Field(default_factory=list, description="Names of existing objects (hosts/networks/groups) to include as members.")


class ListServicesParams(_Scoped):
    protocol: str = Field("tcp", description="'tcp' or 'udp'.")


class ServiceObj(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str = ""
    port: str = ""
    protocol: str = ""


class ServiceList(sdl.Entity):
    id: str = "service_list"
    title: str = ""
    items: list[ServiceObj] = Field(default_factory=list)


class CreateServiceParams(_Scoped):
    name: str = Field(..., description="New service object name.")
    port: str = Field(..., description="Port or port range, e.g. '443' or '8000-8010'.")
    protocol: str = Field("tcp", description="'tcp' or 'udp'.")


class DeleteServiceParams(_Scoped):
    name: str = Field(..., description="Service object name to permanently delete.")
    protocol: str = Field("tcp", description="'tcp' or 'udp'.")


# ──────────────────────────────────────────────────────────────────────────
# Access Control
# ──────────────────────────────────────────────────────────────────────────


class ListAccessLayersParams(_Scoped):
    pass


class AccessLayer(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str = ""


class AccessLayerList(sdl.Entity):
    id: str = "access_layer_list"
    title: str = ""
    items: list[AccessLayer] = Field(default_factory=list)


class ListAccessRulesParams(_Scoped):
    layer: str = Field(..., description="Access layer name, from list_access_layers.")


class AccessRule(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str = ""
    action: str = ""
    source: list[str] = Field(default_factory=list)
    destination: list[str] = Field(default_factory=list)
    service: list[str] = Field(default_factory=list)
    enabled: bool = True


class AccessRuleList(sdl.Entity):
    id: str = "access_rule_list"
    title: str = ""
    items: list[AccessRule] = Field(default_factory=list)


class GetAccessRuleParams(_Scoped):
    layer: str = Field(..., description="Access layer name.")
    name: str = Field(..., description="Access rule name.")


class CreateAccessRuleParams(_Scoped):
    layer: str = Field(..., description="Access layer name to add the rule to.")
    name: str = Field(..., description="New access rule name.")
    position: str = Field("top", description="Where to insert the rule: 'top', 'bottom', or a number.")
    source: list[str] = Field(default_factory=lambda: ["Any"], description="Source object names, or ['Any'].")
    destination: list[str] = Field(default_factory=lambda: ["Any"], description="Destination object names, or ['Any'].")
    service: list[str] = Field(default_factory=lambda: ["Any"], description="Service object names, or ['Any'].")
    action: str = Field("Accept", description="'Accept', 'Drop', or 'Reject'.")


class UpdateAccessRuleParams(_Scoped):
    layer: str = Field(..., description="Access layer name.")
    name: str = Field(..., description="Access rule name to update.")
    action: str = Field("", description="New action, if changing.")
    enabled: bool = Field(True, description="Whether the rule should be enabled.")


class DeleteAccessRuleParams(_Scoped):
    layer: str = Field(..., description="Access layer name.")
    name: str = Field(..., description="Access rule name to permanently delete.")


class BulkAccessRuleActionParams(_Scoped):
    layer: str = Field(..., description="Access layer name the rules live in.")
    names: list[str] = Field(..., description="Access rule names to act on.")
    enabled: bool = Field(..., description="Whether to enable (true) or disable (false) each rule.")


class BulkActionOutcome(sdl.Entity):
    title: str = ""
    id: str = ""
    ok: bool = False
    error: str = ""


class BulkActionResult(sdl.Entity):
    id: str = "bulk_action_result"
    title: str = ""
    items: list[BulkActionOutcome] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────
# Policy lifecycle: publish / discard / packages / install-policy / tasks
# ──────────────────────────────────────────────────────────────────────────


class PublishChangesParams(_Scoped):
    pass


class DiscardChangesParams(_Scoped):
    pass


class PublishResult(sdl.Entity):
    id: str = ""
    title: str = ""
    task_id: str = ""


class ListPolicyPackagesParams(_Scoped):
    pass


class PolicyPackage(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str = ""


class PolicyPackageList(sdl.Entity):
    id: str = "policy_package_list"
    title: str = ""
    items: list[PolicyPackage] = Field(default_factory=list)


class InstallPolicyParams(_Scoped):
    policy_package: str = Field(..., description="Policy package name to install, from list_policy_packages.")
    targets: list[str] = Field(..., description="Gateway/cluster names to install the policy on, from list_gateways.")


class GetTaskStatusParams(_Scoped):
    task_id: str = Field(..., description="Task id returned by publish_changes or install_policy.")


class TaskStatus(sdl.Entity):
    id: str = ""
    title: str = ""
    status: str = ""
    progress_percentage: int = 0


# ──────────────────────────────────────────────────────────────────────────
# Gateways / audit
# ──────────────────────────────────────────────────────────────────────────


class ListGatewaysParams(_Scoped):
    pass


class Gateway(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str = ""
    ipv4_address: str = ""
    policy_installed: bool = False
    sw_version: str = ""


class GatewayList(sdl.Entity):
    id: str = "gateway_list"
    title: str = ""
    items: list[Gateway] = Field(default_factory=list)


class AuditCheckpointEstateParams(BaseModel):
    pass


class AuditFinding(sdl.Entity):
    id: str = ""
    title: str = ""
    severity: str = ""
    detail: str = ""


class AuditReport(sdl.Entity):
    id: str = "audit_report"
    title: str = ""
    findings: list[AuditFinding] = Field(default_factory=list)
