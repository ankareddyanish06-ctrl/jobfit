"""SQLite persistence for placement analyses."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "database.db"
DB_PATH = Path(os.getenv("DATABASE_PATH", DEFAULT_DB_PATH))


def _connection() -> sqlite3.Connection:
    """Create a short-lived connection for each request."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cgpa REAL NOT NULL,
                internships INTEGER NOT NULL,
                projects INTEGER NOT NULL,
                skills TEXT NOT NULL,
                skill_score REAL NOT NULL,
                prediction REAL NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_timestamp "
            "ON predictions(timestamp DESC)"
        )


def save_prediction(
    cgpa: float,
    internships: int,
    projects: int,
    skills: list[str],
    skill_score: float,
    prediction: float,
) -> int:
    with _connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO predictions
            (timestamp, cgpa, internships, projects, skills, skill_score, prediction)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                cgpa,
                internships,
                projects,
                json.dumps(skills),
                skill_score,
                prediction,
            ),
        )
        return int(cursor.lastrowid)


def get_history(limit: int = 10) -> list[dict[str, Any]]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, timestamp, cgpa, internships, projects, skills, skill_score, prediction
            FROM predictions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["skills"] = json.loads(item["skills"])
        results.append(item)
    return results
