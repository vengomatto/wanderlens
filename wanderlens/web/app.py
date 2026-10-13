from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageOps

from wanderlens.db import connect, init_db
from wanderlens.web import views

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

THUMBNAIL_MAX_PX = 480


def _open(conn: sqlite3.Connection) -> None:
    init_db(conn)


def _thumbnail(config, source: Path, photo_id: str) -> Path:
    cache_dir = config.data_dir / "thumbnails"
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{photo_id}\0{source}".encode()).hexdigest()
    dest = cache_dir / f"{key}.jpg"
    if dest.exists():
        return dest
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((THUMBNAIL_MAX_PX, THUMBNAIL_MAX_PX))
        image.save(dest, "JPEG", quality=82)
    return dest


def create_app(config, user_name: str = "owner") -> FastAPI:
    app = FastAPI(title="Wanderlens", docs_url=None, redoc_url=None)
    app.state.config = config
    app.state.user_name = user_name

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    def render(request: Request, template: str, **context) -> HTMLResponse:
        context.setdefault(
            "tiles",
            {
                "url": app.state.config.tile_url,
                "attribution": app.state.config.tile_attribution,
            },
        )
        return templates.TemplateResponse(request, template, context)

    @app.get("/", response_class=HTMLResponse)
    def profile(request: Request) -> HTMLResponse:
        conn = connect(app.state.config.db_path)
        try:
            _open(conn)
            view = views.profile_view(conn, app.state.user_name)
        finally:
            conn.close()
        return render(request, "profile.html", active="profile", view=view)

    @app.get("/recommendations", response_class=HTMLResponse)
    def recommendations(request: Request) -> HTMLResponse:
        conn = connect(app.state.config.db_path)
        try:
            _open(conn)
            user_id = views.resolve_user(conn, app.state.user_name)
            recs = views.recommendations_view(conn, user_id) if user_id is not None else []
        finally:
            conn.close()
        return render(request, "recommendations.html", active="recommendations", recs=recs)

    @app.get("/trips/{trip_id}", response_class=HTMLResponse)
    def trip(request: Request, trip_id: int) -> HTMLResponse:
        conn = connect(app.state.config.db_path)
        try:
            _open(conn)
            user_id = views.resolve_user(conn, app.state.user_name)
            detail = views.trip_detail(conn, user_id, trip_id) if user_id is not None else None
        finally:
            conn.close()
        if detail is None:
            raise HTTPException(status_code=404, detail="Trip not found")
        return render(request, "trip.html", active="profile", detail=detail)

    @app.get("/destinations/{destination_id}", response_class=HTMLResponse)
    def destination(request: Request, destination_id: str) -> HTMLResponse:
        conn = connect(app.state.config.db_path)
        try:
            _open(conn)
            user_id = views.resolve_user(conn, app.state.user_name)
            detail = (
                views.destination_detail(conn, user_id, destination_id)
                if user_id is not None
                else None
            )
            similar = (
                views.similar_trips(conn, user_id, destination_id)
                if user_id is not None
                else []
            )
        finally:
            conn.close()
        if detail is None:
            raise HTTPException(status_code=404, detail="Destination not found")
        map_payload = {
            "name": detail.name,
            "country": detail.country,
            "lat": detail.lat,
            "lon": detail.lon,
            "region_geojson": detail.region_geojson,
            "region_kind": detail.region_kind,
            "region_radius_km": detail.region_radius_km,
            "pois": detail.pois,
        }
        return render(
            request,
            "destination.html",
            active="recommendations",
            detail=detail,
            similar=similar,
            map_payload=map_payload,
        )

    @app.get("/destinations/{destination_id}/feedback")
    def destination_feedback(destination_id: str, action: str = "") -> RedirectResponse:
        conn = connect(app.state.config.db_path)
        try:
            _open(conn)
            user_id = views.resolve_user(conn, app.state.user_name)
            if user_id is not None:
                views.record_feedback(conn, user_id, destination_id, action)
        finally:
            conn.close()
        return RedirectResponse(url=f"/destinations/{destination_id}", status_code=303)

    @app.get("/destination-image/{destination_id}/{position}")
    def destination_image(request: Request, destination_id: str, position: int) -> FileResponse:
        conn = connect(app.state.config.db_path)
        try:
            _open(conn)
            row = conn.execute(
                "SELECT filename FROM destination_images WHERE destination_id = ? AND position = ?",
                (destination_id, position),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            raise HTTPException(status_code=404, detail="Image not found")
        path = app.state.config.data_dir / "media" / row["filename"]
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(path)

    @app.get("/map", response_class=HTMLResponse)
    def map_view(request: Request) -> HTMLResponse:
        conn = connect(app.state.config.db_path)
        try:
            _open(conn)
            user_id = views.resolve_user(conn, app.state.user_name)
            points = views.map_points(conn, user_id) if user_id is not None else []
        finally:
            conn.close()
        payload = [
            {"kind": p.kind, "label": p.label, "lat": p.lat, "lon": p.lon} for p in points
        ]
        return render(
            request, "map.html", active="map", points=points, points_payload=payload
        )

    @app.get("/photos/{photo_id}")
    def photo(request: Request, photo_id: str) -> FileResponse:
        conn = connect(app.state.config.db_path)
        try:
            _open(conn)
            user_id = views.resolve_user(conn, app.state.user_name)
            row = None
            if user_id is not None:
                row = conn.execute(
                    "SELECT path FROM photos WHERE user_id = ? AND id = ?",
                    (user_id, photo_id),
                ).fetchone()
        finally:
            conn.close()

        source = Path(row["path"]) if row is not None else None
        if source is None or not source.is_file():
            raise HTTPException(status_code=404, detail="Photo not found")
        try:
            thumbnail = _thumbnail(app.state.config, source, photo_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Photo not readable")
        return FileResponse(thumbnail, media_type="image/jpeg")

    return app
