"""Check Point Connector -- center panels: base overview + Access Control/
Objects/Gateways overlay panels, per UI_COMPONENT_PLAN.md §1.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h
import handlers_objects as ho
import handlers_access as ha
from schemas import (
    ListHostsParams, ListNetworksParams, ListAccessLayersParams,
    ListGatewaysParams,
)


def _status_badge(status: str) -> ui.UINode:
    s = (status or "").lower()
    color = "success" if s in ("connected", "trusted", "online", "up") else ("error" if s in ("disconnected", "untrusted", "offline", "down") else "default")
    return ui.Badge(label=status or "unknown", color=color)


@ext.panel("checkpoint_center", slot="center")
async def checkpoint_center(ctx, **kwargs) -> ui.UINode:
    """Base (non-overlay) center panel -- rendered before any sidebar item is
    clicked, per UI_INTERFACE_STANDARD.md's mandatory base-center-panel rule."""
    result = await h.list_connections(ctx, h.NoParams())
    items = result.data.items if result.success and result.data else []
    if not items:
        return ui.Empty(message="Connect a Check Point Management Server first.", icon="Shield")
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Check Point", variant="heading"),
        ui.Text(
            "Ask Webbee to list access rules, hosts/networks/groups/services, gateways, publish pending changes, install policy, or run a health audit.",
            variant="caption",
        ),
    ])


@ext.panel("checkpoint_access_overview", slot="center", center_overlay=True)
async def checkpoint_access_overview(ctx, **kwargs) -> ui.UINode:
    layers_res = await ha.list_access_layers(ctx, ListAccessLayersParams())
    layers = layers_res.data.items if layers_res.success and layers_res.data else []
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Access Control", variant="heading"),
        ui.Stats(children=[
            ui.Stat(label="Access layers", value=str(len(layers))),
        ]),
        ui.Stack(direction="v", gap=1, align="stretch", children=[
            ui.Text(l.title, variant="body") for l in layers
        ]) if layers else ui.Text("No access layers found.", variant="caption"),
    ])


@ext.panel("checkpoint_objects_overview", slot="center", center_overlay=True)
async def checkpoint_objects_overview(ctx, **kwargs) -> ui.UINode:
    hosts_res = await ho.list_hosts(ctx, ListHostsParams())
    nets_res = await ho.list_networks(ctx, ListNetworksParams())
    hosts = hosts_res.data.items if hosts_res.success and hosts_res.data else []
    nets = nets_res.data.items if nets_res.success and nets_res.data else []
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Objects", variant="heading"),
        ui.Stats(children=[
            ui.Stat(label="Hosts", value=str(len(hosts))),
            ui.Stat(label="Networks", value=str(len(nets))),
        ]),
    ])


@ext.panel("checkpoint_gateways_overview", slot="center", center_overlay=True)
async def checkpoint_gateways_overview(ctx, **kwargs) -> ui.UINode:
    gw_res = await ha.list_gateways(ctx, ListGatewaysParams())
    gateways = gw_res.data.items if gw_res.success and gw_res.data else []
    if not gateways:
        return ui.Stack(direction="v", gap=2, children=[
            ui.Text("Gateways", variant="heading"),
            ui.Text("No gateways found.", variant="caption"),
        ])
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Gateways", variant="heading"),
        ui.Stack(direction="v", gap=2, align="stretch", children=[
            ui.Stack(direction="h", gap=2, align="center", children=[
                ui.Text(g.title, variant="body"),
                _status_badge(g.status),
            ])
            for g in gateways
        ]),
    ])
