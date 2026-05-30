"""Rate-limiting helpers.

The Limiter is instantiated here so it can be imported by both main.py
(to attach to app.state and add middleware) and search.py (to decorate
the route), without circular imports.

Key-func note
-------------
Behind Azure Static Web Apps the client IP arrives in X-Forwarded-For,
NOT in the socket remote_address (which will be the SWA edge IP, shared
by every user).  We extract the *first* hop of X-Forwarded-For — that is
the original client IP as seen by the edge before any internal hops are
appended.  Fallback to socket IP for direct local connections.
"""

from __future__ import annotations

from starlette.requests import Request
from slowapi import Limiter


def _real_ip(request: Request) -> str:
    """Return the originating client IP, respecting X-Forwarded-For."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Header may contain multiple IPs: "client, proxy1, proxy2"
        # The first entry is the original client.
        first_hop = forwarded_for.split(",")[0].strip()
        if first_hop:
            return first_hop
    # Direct connection (local dev, health-check from same host, etc.)
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=_real_ip)
