from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Callable, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobRunner:
    """A single-flight, in-process background job runner.

    State is kept in the ``jobs`` table so any request can read it; only one job
    runs at a time (the dashboard's main loop is one operation at a time).
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def submit(self, kind: str, fn: Callable[[], None]) -> Optional[int]:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return None
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute(
                "INSERT INTO jobs (kind, status, progress, message, created_at, updated_at) "
                "VALUES (?, 'queued', 0, '', ?, ?)",
                (kind, _now(), _now()),
            )
            job_id = int(cursor.lastrowid)
            conn.commit()
            conn.close()
            self._thread = threading.Thread(target=self._run, args=(job_id, fn), daemon=True)
            self._thread.start()
            return job_id

    def _run(self, job_id: int, fn: Callable[[], None]) -> None:
        self._update(job_id, status="running", progress=10, message="running")
        try:
            fn()
            self._update(job_id, status="done", progress=100, message="done")
        except Exception as exc:  # never let a job crash the server
            self._update(job_id, status="error", message=str(exc))

    def _update(self, job_id: int, status=None, progress=None, message=None) -> None:
        fields: list[str] = []
        values: list = []
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if progress is not None:
            fields.append("progress = ?")
            values.append(progress)
        if message is not None:
            fields.append("message = ?")
            values.append(message)
        fields.append("updated_at = ?")
        values.append(_now())
        values.append(job_id)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        conn.close()


def load_job(conn: sqlite3.Connection, job_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def latest_job(conn: sqlite3.Connection) -> Optional[dict]:
    row = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None
