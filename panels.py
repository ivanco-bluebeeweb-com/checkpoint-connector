"""Panel UI -- connection list/connect form + navigation for Check Point
Connector.

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule (same convention as every other
SASE connector's panels.py). Every section is a plain ui.Stack, sections
separated by ui.Divider() -- no Card border/background/shadow anywhere in
this slot. Disconnect lives only in the "App settings" screen
(panels_settings.py). The one secondary "App settings" button is always
the LAST element at the bottom of the sidebar.

PER ~/UI_INTERFACE_STANDARD.md (2026-08-21 addendum): every Input carries
its own visible label (rendered here as a sibling ui.Text caption, since
ui.Input/ui.Password/ui.Select take no label= kwarg), the placeholder text
is always contextually specific to what's being entered, the connect
form's container is stretched full-width, and its content fills that
width. The "How do I set this up?" walkthrough lives ONLY in the help
panel below -- never duplicated as static sidebar text.

Real DUI-validator lessons from this SASE build (do NOT repeat): ui.Stack
has no width=; ui.ListItem takes title=/subtitle=, not label=; ui.Badge
takes label=/color=, not text=/variant=; ui.Alert takes type=, not
variant=; @ext.panel(..., slot="center", center_overlay=True) + trigger
ui.Call("__panel__<name>"), not a nonexistent @ext.modal.

Implements UI_COMPONENT_PLAN.md §1 exactly (built alongside that plan,
not after -- APP_PREPARATION_STANDARD.md §9).
"""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
from app import ext


def _connect_help_panel_body() -> ui.UINode:
    return ui.Stack(direction="v", gap=3, children=[
        ui.Text("1. Sign in to your Check Point Security Management Server (or Multi-Domain Server) web admin.", variant="body"),
        ui.Text("2. Use an administrator account with Web Services / API access enabled."),
        ui.Text("3. Enter the host, username, and password below -- for Multi-Domain Security Management also enter the domain name; leave it empty for a standalone Management Server."),
        ui.Text("4. The connector logs in once to obtain a session id and stores only that -- not your password."),
        ui.Text("5. Any change you make (hosts, rules, etc.) stays in that session until you explicitly publish it -- ask Webbee to \"publish changes\" when you're ready."),
    ])


@ext.panel("checkpoint_connect_help", slot="center", center_overlay=True)
async def checkpoint_connect_help_panel(ctx) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("How do I set this up?", variant="heading"),
        _connect_help_panel_body(),
    ])


def _connect_form() -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Stack(direction="v", gap=1, children=[
            ui.Text("Management Server host", variant="caption"),
            ui.Input(param_name="host", placeholder="https://mgmt.company.com"),
        ]),
        ui.Stack(direction="v", gap=1, children=[
            ui.Text("Username", variant="caption"),
            ui.Input(param_name="username", placeholder="admin"),
        ]),
        ui.Stack(direction="v", gap=1, children=[
            ui.Text("Password", variant="caption"),
            ui.Password(param_name="password", placeholder="Management Server password"),
        ]),
        ui.Stack(direction="v", gap=1, children=[
            ui.Text("Domain (Multi-Domain Security Management only)", variant="caption"),
            ui.Input(param_name="domain", placeholder="Leave empty for a standalone Management Server"),
        ]),
        ui.Button("Connect", variant="primary", on_click=ui.Call("connect_checkpoint", {})),
    ])


@ext.panel("checkpoint_sidebar", slot="left")
async def checkpoint_sidebar(ctx) -> ui.UINode:
    result = await h.list_connections(ctx, h.NoParams())
    items = result.data.items if result.success and result.data else []

    children: list[ui.UINode] = [ui.Text("Check Point", variant="heading")]

    if items:
        for c in items:
            children.append(ui.Text(c.title, variant="body"))
        children.append(ui.Divider())
        children.append(ui.ListItem(title="Access Control", on_click=ui.Call("__panel__checkpoint_access_overview")))
        children.append(ui.ListItem(title="Objects", on_click=ui.Call("__panel__checkpoint_objects_overview")))
        children.append(ui.ListItem(title="Gateways", on_click=ui.Call("__panel__checkpoint_gateways_overview")))
        children.append(ui.ListItem(title="Health Audit", on_click=ui.Call("audit_checkpoint_estate", {})))
        children.append(ui.Divider())

    children.append(ui.Stack(direction="v", gap=2, align="stretch", children=[
        _connect_form(),
        ui.Button("How do I set this up?", variant="ghost", size="sm", on_click=ui.Call("__panel__checkpoint_connect_help")),
    ]))

    children.append(ui.Divider())
    children.append(ui.Button("App settings", variant="ghost", size="sm", on_click=ui.Call("__panel__checkpoint_settings")))

    return ui.Stack(direction="v", gap=3, align="stretch", children=children)
