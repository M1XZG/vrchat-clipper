"""FastAPI server for the VRChat Clipper backend."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .clipper import Clipper
from .config import load_config, merge_config, save_config
from .paths import web_dir

_CLIPPER = Clipper(config_getter=load_config)


def _web_dir() -> Path:
    return web_dir()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title="VRChat Clipper", version=__version__)

    # The default server binds to loopback, so permissive CORS is acceptable for
    # the local OVR Toolkit Chromium app.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    web_dir = _web_dir()
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    @app.get("/", response_model=None)
    async def index() -> FileResponse | HTMLResponse:
        index_path = web_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse(
            "<!doctype html><html><body><h1>VRChat Clipper</h1>"
            "<p>The web UI has not been built yet.</p></body></html>"
        )

    @app.get("/api/config")
    async def get_config() -> dict[str, Any]:
        return load_config()

    @app.post("/api/config")
    async def post_config(request: Request) -> dict[str, Any]:
        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Expected JSON object") from exc
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Expected JSON object")
        merged = merge_config(load_config(), payload)
        return save_config(merged)

    @app.post("/api/clip")
    async def post_clip() -> JSONResponse:
        if _CLIPPER.busy:
            return JSONResponse({"status": "busy"})
        _CLIPPER.state.busy = True
        asyncio.create_task(_CLIPPER.run_clip(load_config()))
        return JSONResponse({"status": "started"}, status_code=202)

    @app.get("/api/status")
    async def get_status() -> dict[str, Any]:
        return _CLIPPER.state.to_dict()

    @app.get("/api/health")
    async def get_health() -> dict[str, Any]:
        return {"ok": True, "version": __version__}

    return app


def run() -> None:
    """Start uvicorn using the configured server host and port."""

    import uvicorn

    cfg = load_config()
    server_cfg = cfg["server"]
    uvicorn.run(create_app(), host=server_cfg["host"], port=server_cfg["port"])
