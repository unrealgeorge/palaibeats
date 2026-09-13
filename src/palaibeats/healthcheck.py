"""A tiny HTTP health endpoint, useful for Docker `HEALTHCHECK` and
external uptime monitoring. Disabled unless `HEALTH_CHECK_PORT` is set.
"""

from __future__ import annotations

from aiohttp import web


async def _healthz(_request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def start_health_server(port: int) -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/healthz", _healthz)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner
