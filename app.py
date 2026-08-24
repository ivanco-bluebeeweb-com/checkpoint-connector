"""Check Point Connector -- app + extension setup.

Single connect surface: Check Point Security Management Server (or
Multi-Domain Server via optional domain field). Session-based auth
(login -> sid, X-chkp-sid header), with a mandatory publish/discard
staging layer and a separate install-policy deployment step. See
PREPARATION.md for the full why.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "checkpoint-connector",
    version="0.1.0",
    display_name="Check Point",
    icon="icon.svg",
    description=(
        "Connect your own Check Point Security Management Server (or "
        "Multi-Domain Server) to manage hosts, networks, groups, TCP/UDP "
        "services, access control rules across layers, policy packages, "
        "and gateway inventory -- plus publish/discard of pending session "
        "changes, policy installation to gateways, bulk rule operations, "
        "and a Check Point estate health audit. Uses your own Management "
        "Server admin credentials, exchanged for a session id via the "
        "standard login endpoint -- nothing is hosted or proxied by "
        "Imperal beyond the request itself."
    ),
)

ext.secret("checkpoint_connections", description="Stored Check Point Management Server connection credentials (JSON array)")

chat = ChatExtension(
    ext,
    tool_name="checkpoint",
    description="Manage Check Point Security Management: access control rules, objects, policy publish/install.",
)
