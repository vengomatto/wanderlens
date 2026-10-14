import json
import subprocess
import sys

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from wanderlens.config import Config
from wanderlens.db import connect, init_db
from wanderlens.web.app import create_app


def _config(tmp_path):
    return Config(
        data_dir=tmp_path,
        photos_dir=tmp_path / "photos",
        db_path=tmp_path / "wl.sqlite3",
        catalog_path=tmp_path / "catalog",
        vlm_provider="t",
        vlm_model="t",
        api_key=None,
    )


def _seed(config, name="owner", user_id=1, trip_id=0):
    config.photos_dir.mkdir(parents=True, exist_ok=True)
    conn = connect(config.db_path)
    init_db(conn)
    conn.execute("INSERT INTO users (id, name) VALUES (?, ?)", (user_id, name))
    conn.execute(
        "INSERT INTO trips (user_id, id, start_at, end_at, country, city, lat, lon) "
        "VALUES (?, ?, '2023-07-01T10:00:00', '2023-07-05T18:00:00', 'Malta', 'Valletta', 35.9, 14.51)",
        (user_id, trip_id),
    )
    for i, color in enumerate([(200, 80, 40), (40, 120, 200)]):
        path = config.photos_dir / f"p{i}.jpg"
        Image.new("RGB", (400, 300), color).save(path)
        pid = f"u{user_id}-p{i}"
        conn.execute(
            "INSERT INTO photos (user_id, id, source, path, sha256, taken_at) VALUES (?, ?, 'folder', ?, ?, ?)",
            (user_id, pid, str(path), f"sha-{pid}", f"2023-07-0{i + 1}T12:00:00"),
        )
        conn.execute(
            "INSERT INTO trip_photos (user_id, trip_id, photo_id) VALUES (?, ?, ?)",
            (user_id, trip_id, pid),
        )
        conn.execute(
            "INSERT INTO photo_embeddings (user_id, photo_id, dim, vector) VALUES (?, ?, 3, ?)",
            (user_id, pid, np.array([1.0, 0.0, 0.0], dtype=np.float32).tobytes()),
        )
    conn.execute(
        "INSERT INTO profile_entries (user_id, factor, key, value) VALUES (?, 'geography', 'Malta', 1.0)",
        (user_id,),
    )
    conn.execute(
        "INSERT INTO profile_entries (user_id, factor, key, value) VALUES (?, 'subjects', 'coastal', 0.5)",
        (user_id,),
    )
    conn.execute(
        "INSERT INTO recommendations "
        "(user_id, run_id, rank, destination_id, score, explanation, destination_name, "
        " destination_country, destination_lat, destination_lon, destination_description, "
        " embedding_score, attribute_score, matched_attributes, best_trip_label, nearest_trip_km, popularity_label) "
        "VALUES (?, 1, 1, 'wy:algarve', 0.83, 'fits your taste for coastal', 'Algarve', "
        " 'Portugal', 37.0, -8.0, 'A sun-drenched coast.', 0.7, 0.42, "
        " '{\"coastal\": 0.6, \"water\": 0.2}', 'Valletta, Malta', 500.0, 'famous')",
        (user_id,),
    )
    _seed_media(config, conn)
    conn.commit()
    conn.close()
    return config


def _seed_media(config, conn):
    media_dir = config.data_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (600, 400), (200, 120, 60)).save(media_dir / "wy_algarve_0.jpg")
    conn.execute(
        "INSERT OR REPLACE INTO destination_images "
        "(destination_id, position, filename, source, license, attribution) "
        "VALUES ('wy:algarve', 0, 'wy_algarve_0.jpg', 'commons', 'CC BY-SA 4.0', 'Jane Doe')"
    )
    conn.execute(
        "INSERT OR REPLACE INTO destination_media "
        "(destination_id, title, page_url, extract, source, license, attribution, "
        " region_geojson, region_kind, region_radius_km, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "wy:algarve",
            "Algarve",
            "https://en.wikipedia.org/wiki/Algarve",
            "Algarve is a region in southern Portugal, known for its coast and cliffs.",
            "wikimedia",
            "",
            "",
            json.dumps(
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {"type": "Point", "coordinates": [-8.0, 37.0]},
                }
            ),
            "approximate",
            40.0,
            "now",
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO destination_embeddings (destination_id, model, dim, vector) "
        "VALUES ('wy:algarve', 'test', 3, ?)",
        (np.array([1.0, 0.0, 0.0], dtype=np.float32).tobytes(),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO destination_guide "
        "(destination_id, understand, links, books, pois, climate, films, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'now')",
        (
            "wy:algarve",
            "Travel prose about the Algarve.",
            json.dumps([{"label": "Wikivoyage", "url": "https://en.wikivoyage.org/wiki/Algarve"}]),
            json.dumps([{"title": "Algarve Blues", "author": "A. Author", "url": ""}]),
            json.dumps([{"name": "Benagil Cave", "kind": "see", "lat": 37.08, "lon": -8.42}]),
            json.dumps([{"month": m, "temp_c": 10 + m, "precip_mm": 50} for m in range(1, 13)]),
            json.dumps([{"title": "The Last Train to Lisbon", "url": ""}]),
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO destination_itineraries "
        "(destination_id, position, title, summary, days, source, model, prompt_version, url, fetched_at) "
        "VALUES ('wy:algarve', 0, 'Algarve in 4 days', '', ?, 'llm', 'test-model', 'itinerary-v1', '', 'now')",
        (json.dumps([{"title": "Day 1", "summary": "Arrive", "items": ["Beach"]}]),),
    )


def _client(config):
    return TestClient(create_app(config))


def test_profile_page_renders(tmp_path):
    config = _seed(_config(tmp_path))
    response = _client(config).get("/")

    assert response.status_code == 200
    body = response.text
    assert "Taste profile" in body
    assert "Valletta, Malta" in body
    assert "/photos/u1-p0" in body


def test_brief_panel_and_save(tmp_path):
    import sqlite3

    config = _seed(_config(tmp_path))
    client = _client(config)

    assert "Trip brief" in client.get("/").text

    response = client.post(
        "/brief",
        data={
            "adults": "2",
            "children": "1",
            "pace": "relaxed",
            "season": "summer",
            "max_travel_km": "1000",
            "home": "44.1,9.6",
            "budget": "medium",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    conn = sqlite3.connect(config.db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM traveller_brief WHERE user_id = 1").fetchone()
    assert row["adults"] == 2
    assert row["children"] == 1
    assert row["season"] == "summer"
    assert row["max_travel_km"] == 1000.0


def test_feedback_post_records_and_returns_fragment(tmp_path):
    import sqlite3

    config = _seed(_config(tmp_path))
    client = _client(config)

    response = client.post(
        "/destinations/wy:algarve/feedback?action=like", headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert 'fb-like active' in response.text
    conn = sqlite3.connect(config.db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT action FROM feedback WHERE user_id = 1 AND destination_id = 'wy:algarve'"
    ).fetchone()
    assert row["action"] == "like"


def test_feedback_post_redirects_without_htmx(tmp_path):
    config = _seed(_config(tmp_path))
    response = _client(config).post(
        "/destinations/wy:algarve/feedback?action=save", follow_redirects=False
    )
    assert response.status_code == 303


def test_discover_page_renders(tmp_path):
    config = _seed(_config(tmp_path))
    body = _client(config).get("/discover").text
    assert "Discover" in body
    assert "disc-card" in body


def test_recommendations_grid_toggle(tmp_path):
    config = _seed(_config(tmp_path))
    body = _client(config).get("/recommendations").text
    assert "rec-view-toggle" in body


def test_saved_page_renders_and_lists_saved(tmp_path):
    config = _seed(_config(tmp_path))
    client = _client(config)

    assert "Nothing saved yet" in client.get("/saved").text

    client.post("/destinations/wy:algarve/feedback?action=save", headers={"HX-Request": "true"})
    body = client.get("/saved").text
    assert "Algarve" in body


def test_recommendations_page_renders(tmp_path):
    config = _seed(_config(tmp_path))
    response = _client(config).get("/recommendations")

    assert response.status_code == 200
    body = response.text
    assert "Algarve" in body
    assert "Portugal" in body
    assert "emb 0.700" in body
    assert "attr 0.420" in body


def test_trip_detail_page_renders(tmp_path):
    config = _seed(_config(tmp_path))
    response = _client(config).get("/trips/0")

    assert response.status_code == 200
    assert "Valletta, Malta" in response.text
    assert "/photos/u1-p0" in response.text


def test_unknown_trip_is_404(tmp_path):
    config = _seed(_config(tmp_path))
    assert _client(config).get("/trips/99").status_code == 404


def test_map_page_renders_markers_and_leaflet(tmp_path):
    config = _seed(_config(tmp_path))
    response = _client(config).get("/map")

    assert response.status_code == 200
    body = response.text
    assert 'id="map"' in body
    assert "vendor/leaflet/leaflet.js" in body
    assert "Algarve" in body
    assert "Valletta, Malta" in body


def test_empty_states_guide_the_user(tmp_path):
    client = _client(_config(tmp_path))

    profile = client.get("/").text
    assert "No taste profile yet" in profile
    assert "wanderlens ingest" in profile

    recs = client.get("/recommendations").text
    assert "No recommendations yet" in recs
    assert "wanderlens recommend" in recs

    assert "Nothing to plot yet" in client.get("/map").text


def test_thumbnail_returns_image(tmp_path):
    config = _seed(_config(tmp_path))
    response = _client(config).get("/photos/u1-p0")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content[:2] == b"\xff\xd8"  # JPEG magic bytes


def test_photo_route_is_user_scoped(tmp_path):
    config = _seed(_config(tmp_path), name="owner", user_id=1)
    _seed(config, name="other", user_id=2, trip_id=1)
    client = _client(config)

    assert client.get("/photos/u1-p0").status_code == 200
    assert client.get("/photos/u2-p0").status_code == 404
    assert client.get("/photos/does-not-exist").status_code == 404


def test_render_does_not_mutate_state(tmp_path):
    config = _seed(_config(tmp_path))
    client = _client(config)

    conn = connect(config.db_path)
    before = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("photos", "trips", "trip_photos", "recommendations")
    }
    conn.close()

    for url in ["/", "/recommendations", "/trips/0", "/map", "/photos/u1-p0"]:
        client.get(url)

    conn = connect(config.db_path)
    after = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("photos", "trips", "trip_photos", "recommendations")
    }
    conn.close()
    assert before == after


def test_read_only_flow_walk(tmp_path):
    config = _seed(_config(tmp_path))
    client = _client(config)

    assert client.get("/").status_code == 200
    assert client.get("/recommendations").status_code == 200
    assert client.get("/trips/0").status_code == 200
    assert client.get("/map").status_code == 200
    thumbnail = client.get("/photos/u1-p0")
    assert thumbnail.status_code == 200
    assert thumbnail.headers["content-type"] == "image/jpeg"


def test_recommendation_card_has_hero_and_link(tmp_path):
    config = _seed(_config(tmp_path))
    body = _client(config).get("/recommendations").text

    assert "/destination-image/" in body
    assert "/destinations/wy" in body
    assert "gauge" in body


def test_destination_page_renders(tmp_path):
    config = _seed(_config(tmp_path))
    response = _client(config).get("/destinations/wy:algarve")

    assert response.status_code == 200
    body = response.text
    assert "Algarve" in body
    assert "Why this is for you" in body
    assert "Travel prose about the Algarve" in body
    assert "wikipedia.org/wiki/Algarve" in body
    assert "CC BY-SA 4.0" in body
    assert 'id="world-map"' in body
    assert 'id="region-map"' in body
    assert "approximate" in body
    assert "vendor/leaflet/leaflet.js" in body
    assert "You loved places like this" in body
    assert "/photos/u1-p0" in body
    assert "Valletta, Malta" in body  # closest trip
    assert "coastal" in body  # shared-attribute chip
    assert "famous" in body  # fame label
    assert "Travel prose about the Algarve" in body
    assert "Read before you go" in body
    assert "Algarve Blues" in body
    assert "When to go" in body
    assert "Films &amp; series set here" in body
    assert "Suggested itineraries" in body
    assert "AI-generated" in body
    assert "Points of interest" in body
    assert "Benagil Cave" in body


def test_destination_page_without_media_degrades(tmp_path):
    config = _seed(_config(tmp_path))
    conn = connect(config.db_path)
    conn.execute(
        "INSERT INTO recommendations (user_id, run_id, rank, destination_id, score, destination_name) "
        "VALUES (1, 1, 2, 'wy:epirus', 0.4, 'Epirus')"
    )
    conn.commit()
    conn.close()

    response = _client(config).get("/destinations/wy:epirus")
    assert response.status_code == 200
    assert "Epirus" in response.text
    assert "No description available yet" in response.text


def test_destination_similar_omitted_without_embedding(tmp_path):
    config = _seed(_config(tmp_path))
    conn = connect(config.db_path)
    conn.execute(
        "INSERT INTO recommendations (user_id, run_id, rank, destination_id, score, destination_name) "
        "VALUES (1, 1, 2, 'wy:epirus', 0.4, 'Epirus')"
    )
    conn.commit()
    conn.close()

    body = _client(config).get("/destinations/wy:epirus").text
    assert "You loved places like this" not in body


def test_destination_unknown_is_404(tmp_path):
    config = _seed(_config(tmp_path))
    assert _client(config).get("/destinations/nope").status_code == 404


def test_destination_image_route(tmp_path):
    config = _seed(_config(tmp_path))
    client = _client(config)

    image = client.get("/destination-image/wy:algarve/0")
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"

    assert client.get("/destination-image/wy:algarve/9").status_code == 404
    assert client.get("/destination-image/nope/0").status_code == 404


def test_rich_destination_flow_walk(tmp_path):
    config = _seed(_config(tmp_path))
    client = _client(config)

    assert client.get("/recommendations").status_code == 200
    page = client.get("/destinations/wy:algarve")
    assert page.status_code == 200
    assert "world-map" in page.text and "region-map" in page.text
    assert client.get("/destination-image/wy:algarve/0").status_code == 200
    assert "You loved places like this" in page.text
    assert client.get("/map").status_code == 200


def test_motion_and_assets_served(tmp_path):
    client = _client(_config(tmp_path))

    css = client.get("/static/app.css")
    assert css.status_code == 200
    assert "view-transition" in css.text

    js = client.get("/static/destination.js")
    assert js.status_code == 200
    assert "__tiles" in js.text


def test_map_uses_configured_keyless_tiles(tmp_path):
    config = _config(tmp_path)
    body = _client(config).get("/map").text
    assert "tile.openstreetmap.org" in body


def test_rendering_web_loads_no_model_runtime(tmp_path):
    code = (
        "import sys, pathlib\n"
        "from fastapi.testclient import TestClient\n"
        "from wanderlens.config import Config\n"
        "from wanderlens.web.app import create_app\n"
        f"d = pathlib.Path({str(tmp_path)!r})\n"
        "cfg = Config(data_dir=d, photos_dir=d/'p', db_path=d/'wl.sqlite3', "
        "catalog_path=d/'c', vlm_provider='t', vlm_model='t', api_key=None)\n"
        "client = TestClient(create_app(cfg))\n"
        "assert client.get('/').status_code == 200\n"
        "heavy = [m for m in ('onnxruntime', 'tokenizers', 'torch', 'open_clip') if m in sys.modules]\n"
        "print('HEAVY:' + ','.join(heavy))\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "HEAVY:"
