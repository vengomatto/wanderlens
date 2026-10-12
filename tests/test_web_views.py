import numpy as np

from wanderlens.db import connect, init_db
from wanderlens.web import views


def _seed(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    conn.execute("INSERT INTO users (id, name) VALUES (1, 'owner')")

    conn.execute(
        "INSERT INTO trips (user_id, id, start_at, end_at, country, city, lat, lon) "
        "VALUES (1, 0, '2023-07-01T10:00:00', '2023-07-05T18:00:00', 'Malta', 'Valletta', 35.90, 14.51)"
    )
    for i in range(3):
        conn.execute(
            "INSERT INTO photos (user_id, id, source, path, sha256, taken_at, lat, lon) "
            "VALUES (1, ?, 'folder', ?, ?, ?, 35.9, 14.5)",
            (f"p{i}", f"/photos/p{i}.jpg", f"sha{i}", f"2023-07-0{i + 1}T12:00:00"),
        )
        conn.execute(
            "INSERT INTO trip_photos (user_id, trip_id, photo_id) VALUES (1, 0, ?)", (f"p{i}",)
        )
    conn.execute("INSERT INTO trip_subjects (user_id, trip_id, subject) VALUES (1, 0, 'coastal')")
    conn.execute("INSERT INTO trip_subjects (user_id, trip_id, subject) VALUES (1, 0, 'water')")
    conn.execute(
        "INSERT INTO photo_embeddings (user_id, photo_id, dim, vector) VALUES (1, 'p0', 3, ?)",
        (np.array([1.0, 0.0, 0.0], dtype=np.float32).tobytes(),),
    )
    conn.execute(
        "INSERT INTO profile_entries (user_id, factor, key, value) VALUES (1, 'geography', 'Malta', 1.0)"
    )
    conn.execute(
        "INSERT INTO profile_entries (user_id, factor, key, value) VALUES (1, 'subjects', 'coastal', 0.6)"
    )
    conn.execute(
        "INSERT INTO recommendations "
        "(user_id, run_id, rank, destination_id, score, explanation, destination_name, "
        " destination_country, destination_lat, destination_lon, destination_description, "
        " embedding_score, attribute_score, matched_attributes, best_trip_label, nearest_trip_km) "
        "VALUES (1, 1, 1, 'wy:algarve', 0.83, 'fits your taste for coastal', 'Algarve', "
        " 'Portugal', 37.0, -8.0, 'A sun-drenched coast.', 0.7, 0.42, "
        " '{\"coastal\": 0.6, \"water\": 0.2}', 'Valletta, Malta', 500.0)"
    )
    conn.execute(
        "INSERT INTO destination_media "
        "(destination_id, title, page_url, extract, source, license, attribution, "
        " region_geojson, region_kind, region_radius_km, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "wy:algarve",
            "Algarve",
            "https://en.wikipedia.org/wiki/Algarve",
            "Algarve is a region in southern Portugal.",
            "wikimedia",
            "",
            "",
            '{"type":"Feature","geometry":{"type":"Polygon","coordinates":[]}}',
            "precise",
            None,
            "now",
        ),
    )
    conn.execute(
        "INSERT INTO destination_images (destination_id, position, filename, source, license, attribution) "
        "VALUES ('wy:algarve', 0, 'wy_algarve_0.jpg', 'commons', 'CC BY-SA 4.0', 'Jane')"
    )
    conn.execute(
        "INSERT INTO destination_embeddings (destination_id, model, dim, vector) VALUES ('wy:algarve', 'test', 3, ?)",
        (np.array([1.0, 0.0, 0.0], dtype=np.float32).tobytes(),),
    )
    conn.commit()
    return conn


def test_resolve_user_missing(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    assert views.resolve_user(conn, "nobody") is None


def test_profile_view_empty_without_user(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    view = views.profile_view(conn, "owner")
    assert not view.has_profile


def test_profile_view_with_data(tmp_path):
    conn = _seed(tmp_path)
    view = views.profile_view(conn, "owner")

    assert view.has_profile
    assert view.embedded_photos == 1
    assert ("Malta", 1.0) in view.geography
    assert ("coastal", 0.6) in view.subjects
    assert len(view.trips) == 1


def test_trips_view_carries_photos_and_attributes(tmp_path):
    conn = _seed(tmp_path)
    trips = views.trips_view(conn, 1)

    assert trips[0].label == "Valletta, Malta"
    assert trips[0].photo_count == 3
    assert trips[0].photo_ids == ["p0", "p1", "p2"]
    assert trips[0].attributes == ["coastal", "water"]


def test_trip_detail(tmp_path):
    conn = _seed(tmp_path)
    detail = views.trip_detail(conn, 1, 0)

    assert detail["trip"].label == "Valletta, Malta"
    assert [p.id for p in detail["photos"]] == ["p0", "p1", "p2"]
    assert detail["photos"][0].name == "p0.jpg"
    assert detail["attributes"] == ["coastal", "water"]
    assert views.trip_detail(conn, 1, 99) is None


def test_recommendations_view_maps_display_fields(tmp_path):
    conn = _seed(tmp_path)
    recs = views.recommendations_view(conn, 1)

    assert len(recs) == 1
    rec = recs[0]
    assert rec.name == "Algarve"
    assert rec.country == "Portugal"
    assert rec.score == 0.83
    assert rec.embedding_score == 0.7
    assert rec.attribute_score == 0.42
    assert rec.explanation.startswith("fits")


def test_recommendations_view_falls_back_when_columns_null(tmp_path):
    conn = _seed(tmp_path)
    conn.execute(
        "INSERT INTO recommendations (user_id, run_id, rank, destination_id, score) "
        "VALUES (1, 1, 2, 'wy:epirus', 0.5)"
    )
    conn.commit()

    rec = views.recommendations_view(conn, 1)[1]
    assert rec.name == "wy:epirus"
    assert rec.country == ""
    assert rec.lat is None
    assert rec.embedding_score is None


def test_map_points_include_trips_and_destinations(tmp_path):
    conn = _seed(tmp_path)
    points = views.map_points(conn, 1)

    kinds = {p.kind for p in points}
    assert kinds == {"trip", "destination"}
    trip = next(p for p in points if p.kind == "trip")
    assert (trip.lat, trip.lon) == (35.90, 14.51)


def test_recommendation_view_flags_image(tmp_path):
    conn = _seed(tmp_path)
    assert views.recommendations_view(conn, 1)[0].has_image is True


def test_recommendation_view_carries_evidence(tmp_path):
    conn = _seed(tmp_path)
    rec = views.recommendations_view(conn, 1)[0]

    assert rec.best_trip_label == "Valletta, Malta"
    assert ("coastal", 0.6) in rec.matched_attributes
    assert rec.matched_attributes[0][0] == "coastal"  # sorted by weight
    assert rec.nearest_trip_km == 500.0


def test_destination_detail_with_media(tmp_path):
    conn = _seed(tmp_path)
    detail = views.destination_detail(conn, 1, "wy:algarve")

    assert detail is not None
    assert detail.name == "Algarve"
    assert detail.country == "Portugal"
    assert detail.extract.startswith("Algarve is a region")
    assert detail.page_url.endswith("/Algarve")
    assert detail.region_kind == "precise"
    assert [image.position for image in detail.images] == [0]
    assert detail.images[0].license == "CC BY-SA 4.0"


def test_destination_detail_without_media(tmp_path):
    conn = _seed(tmp_path)
    conn.execute(
        "INSERT INTO recommendations (user_id, run_id, rank, destination_id, score, "
        "destination_name, destination_country) VALUES (1, 1, 2, 'wy:epirus', 0.5, 'Epirus', 'Greece')"
    )
    conn.commit()

    detail = views.destination_detail(conn, 1, "wy:epirus")
    assert detail is not None
    assert detail.extract == ""
    assert detail.images == []
    assert detail.score == 0.5


def test_destination_detail_unknown_is_none(tmp_path):
    conn = _seed(tmp_path)
    assert views.destination_detail(conn, 1, "nope") is None


def test_similar_trips_ranks_by_embedding(tmp_path):
    conn = _seed(tmp_path)
    similar = views.similar_trips(conn, 1, "wy:algarve")

    assert len(similar) == 1
    assert similar[0].trip.label == "Valletta, Malta"
    assert similar[0].score > 0
    assert similar[0].photo_ids  # the trip's own photos


def test_similar_trips_empty_without_embedding(tmp_path):
    conn = _seed(tmp_path)
    assert views.similar_trips(conn, 1, "wy:nowhere") == []
