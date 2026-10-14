import threading
import time

from wanderlens.db import connect, init_db
from wanderlens.web.jobs import JobRunner, latest_job, load_job


def _runner(tmp_path):
    conn = connect(tmp_path / "j.sqlite3")
    init_db(conn)
    conn.close()
    return JobRunner(tmp_path / "j.sqlite3")


def _read(tmp_path, job_id):
    conn = connect(tmp_path / "j.sqlite3")
    try:
        return load_job(conn, job_id)
    finally:
        conn.close()


def test_job_runs_to_done(tmp_path):
    runner = _runner(tmp_path)
    done = threading.Event()

    job_id = runner.submit("ingest", lambda: done.set())
    done.wait(timeout=5)
    time.sleep(0.1)

    job = _read(tmp_path, job_id)
    assert job["status"] == "done"
    assert job["progress"] == 100


def test_single_flight_refuses_overlap(tmp_path):
    runner = _runner(tmp_path)
    release = threading.Event()

    assert runner.submit("ingest", lambda: release.wait(timeout=5)) is not None
    time.sleep(0.1)
    assert runner.submit("recommend", lambda: None) is None
    release.set()


def test_job_error_recorded(tmp_path):
    runner = _runner(tmp_path)

    def boom():
        raise RuntimeError("nope")

    job_id = runner.submit("recommend", boom)
    for _ in range(50):
        job = _read(tmp_path, job_id)
        if job["status"] == "error":
            break
        time.sleep(0.05)

    assert job["status"] == "error"
    assert "nope" in job["message"]


def test_latest_job(tmp_path):
    runner = _runner(tmp_path)
    runner.submit("ingest", lambda: None)
    time.sleep(0.2)
    conn = connect(tmp_path / "j.sqlite3")
    try:
        job = latest_job(conn)
    finally:
        conn.close()
    assert job["kind"] == "ingest"
