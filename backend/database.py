"""SQLite persistence for JobFit analyses and verified company criteria."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "database.db"
_db_env = os.getenv("DATABASE_PATH", "").strip()
DB_PATH = Path(_db_env) if _db_env else DEFAULT_DB_PATH


def _connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    return con



SEED_REQUIREMENTS = [
    {
        "company": "Google",
        "target_role": "Software Developer",
        "min_cgpa": 7.5,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE"],
        "skills": ["data structures", "python", "java", "c++", "git", "system design", "rest api"],
        "graduation_year": None,
        "source_url": "https://careers.google.com/jobs/results/",
    },
    {
        "company": "Microsoft",
        "target_role": "Software Developer",
        "min_cgpa": 7.5,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE"],
        "skills": ["data structures", "c++", "c#", "azure", "sql", "git", "rest api"],
        "graduation_year": None,
        "source_url": "https://careers.microsoft.com/v2/global/en/home.html",
    },
    {
        "company": "Amazon",
        "target_role": "Software Developer",
        "min_cgpa": 7.0,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE"],
        "skills": ["java", "python", "aws", "data structures", "linux", "distributed systems"],
        "graduation_year": None,
        "source_url": "https://amazon.jobs/en/job_categories/software-development",
    },
    {
        "company": "Tata Consultancy Services (TCS)",
        "target_role": "Software Developer",
        "min_cgpa": 6.0,
        "max_backlogs": 1,
        "branches": ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"],
        "skills": ["python", "java", "sql", "data structures", "html", "css"],
        "graduation_year": None,
        "source_url": "https://www.tcs.com/careers/india/entry-level-hiring",
    },
    {
        "company": "Infosys",
        "target_role": "Software Developer",
        "min_cgpa": 6.0,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE", "EEE"],
        "skills": ["java", "python", "sql", "git", "rest api"],
        "graduation_year": None,
        "source_url": "https://www.infosys.com/careers.html",
    },
    {
        "company": "Accenture",
        "target_role": "Software Developer",
        "min_cgpa": 6.5,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE", "EEE", "MECH"],
        "skills": ["java", "python", "cloud", "rest api", "sql", "git"],
        "graduation_year": None,
        "source_url": "https://www.accenture.com/in-en/careers/jobsearch",
    },
    {
        "company": "Deloitte",
        "target_role": "Data Analyst",
        "min_cgpa": 6.5,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE", "EEE"],
        "skills": ["sql", "python", "power bi", "excel", "tableau", "data analysis"],
        "graduation_year": None,
        "source_url": "https://www2.deloitte.com/ui/en/pages/careers/articles/technology-consulting.html",
    },
    {
        "company": "Cisco",
        "target_role": "Cloud Engineer",
        "min_cgpa": 7.0,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE"],
        "skills": ["linux", "networking", "python", "aws", "docker", "kubernetes"],
        "graduation_year": None,
        "source_url": "https://jobs.cisco.com/jobs/SearchJobs",
    },
    {
        "company": "IBM",
        "target_role": "Cloud Engineer",
        "min_cgpa": 6.5,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE"],
        "skills": ["linux", "docker", "kubernetes", "cloud", "python", "ci/cd"],
        "graduation_year": None,
        "source_url": "https://www.ibm.com/employment/",
    },
    {
        "company": "Cognizant",
        "target_role": "Full Stack Developer",
        "min_cgpa": 6.0,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE"],
        "skills": ["javascript", "react", "node.js", "sql", "html", "css", "git"],
        "graduation_year": None,
        "source_url": "https://careers.cognizant.com/global/en",
    },
    {
        "company": "Amazon AWS",
        "target_role": "DevOps Engineer",
        "min_cgpa": 7.0,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE"],
        "skills": ["linux", "aws", "docker", "kubernetes", "ci/cd", "python", "git"],
        "graduation_year": None,
        "source_url": "https://amazon.jobs/en/teams/aws",
    },
    {
        "company": "Palo Alto Networks",
        "target_role": "Cybersecurity Analyst",
        "min_cgpa": 7.0,
        "max_backlogs": 0,
        "branches": ["CSE", "IT", "ECE"],
        "skills": ["cybersecurity", "networking", "linux", "python", "firewall", "git"],
        "graduation_year": None,
        "source_url": "https://jobs.paloaltonetworks.com/",
    }
]


def init_db() -> None:
    with _connection() as con:
        con.execute("""
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
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS career_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                student_name TEXT NOT NULL,
                target_role TEXT NOT NULL,
                readiness_score REAL NOT NULL,
                profile_json TEXT NOT NULL,
                analysis_json TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS company_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                target_role TEXT NOT NULL,
                min_cgpa REAL NOT NULL,
                max_backlogs INTEGER NOT NULL,
                branches_json TEXT NOT NULL,
                skills_json TEXT NOT NULL,
                graduation_year INTEGER,
                source_url TEXT NOT NULL,
                verified_at TEXT NOT NULL,
                UNIQUE(company, target_role, graduation_year)
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_career_analyses_timestamp ON career_analyses(timestamp DESC)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_company_requirements_role ON company_requirements(target_role)")

        count = con.execute("SELECT COUNT(*) FROM company_requirements").fetchone()[0]
        if count == 0:
            now = datetime.now(timezone.utc).isoformat()
            for item in SEED_REQUIREMENTS:
                con.execute(
                    """
                    INSERT OR IGNORE INTO company_requirements
                    (company, target_role, min_cgpa, max_backlogs, branches_json, skills_json, graduation_year, source_url, verified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["company"],
                        item["target_role"],
                        item["min_cgpa"],
                        item["max_backlogs"],
                        json.dumps(item["branches"]),
                        json.dumps(item["skills"]),
                        item.get("graduation_year"),
                        item["source_url"],
                        now,
                    ),
                )


def save_analysis(profile: dict[str, Any], analysis: dict[str, Any]) -> int:
    with _connection() as con:
        cur = con.execute(
            """
            INSERT INTO career_analyses (timestamp, student_name, target_role, readiness_score, profile_json, analysis_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                profile["name"],
                profile["target_role"],
                analysis["readiness_score"],
                json.dumps(profile),
                json.dumps(analysis),
            ),
        )
        return int(cur.lastrowid)


def get_analysis_history(limit: int = 8) -> list[dict[str, Any]]:
    with _connection() as con:
        rows = con.execute(
            """
            SELECT id, timestamp, student_name, target_role, readiness_score, analysis_json
            FROM career_analyses
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [{**dict(row), "analysis": json.loads(row["analysis_json"])} for row in rows]


def get_analysis_by_id(analysis_id: int) -> dict[str, Any] | None:
    with _connection() as con:
        row = con.execute(
            """
            SELECT id, timestamp, student_name, target_role, readiness_score, profile_json, analysis_json
            FROM career_analyses
            WHERE id = ?
            """,
            (analysis_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "student_name": row["student_name"],
            "target_role": row["target_role"],
            "readiness_score": row["readiness_score"],
            "profile": json.loads(row["profile_json"]),
            "analysis": json.loads(row["analysis_json"]),
        }


def upsert_requirement(item: dict[str, Any]) -> int:
    with _connection() as con:
        con.execute(
            """
            DELETE FROM company_requirements
            WHERE company = ? AND target_role = ? AND graduation_year IS ?
            """,
            (item["company"], item["target_role"], item.get("graduation_year")),
        )
        cur = con.execute(
            """
            INSERT INTO company_requirements
            (company, target_role, min_cgpa, max_backlogs, branches_json, skills_json, graduation_year, source_url, verified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["company"],
                item["target_role"],
                item["min_cgpa"],
                item["max_backlogs"],
                json.dumps(item["branches"]),
                json.dumps(item["skills"]),
                item.get("graduation_year"),
                item["source_url"],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return int(cur.lastrowid)


def get_requirements(role: str | None = None) -> list[dict[str, Any]]:
    with _connection() as con:
        if role and role.strip():
            canonical = role.strip().lower()
            rows = con.execute("SELECT * FROM company_requirements ORDER BY verified_at DESC").fetchall()
            matching_rows = []
            for row in rows:
                db_role = row["target_role"].lower()
                if canonical in db_role or db_role in canonical or any(w in db_role for w in canonical.split() if len(w) > 3):
                    matching_rows.append(row)
            if not matching_rows:
                # If no direct match, return software developer/general baseline if available
                matching_rows = [r for r in rows if "software" in r["target_role"].lower()][:4]
            rows_to_return = matching_rows or rows[:6]
        else:
            rows_to_return = con.execute("SELECT * FROM company_requirements ORDER BY verified_at DESC").fetchall()

    return [
        {
            "company": row["company"],
            "target_role": row["target_role"],
            "min_cgpa": row["min_cgpa"],
            "max_backlogs": row["max_backlogs"],
            "branches": json.loads(row["branches_json"]),
            "skills": json.loads(row["skills_json"]),
            "graduation_year": row["graduation_year"],
            "source_url": row["source_url"],
            "verified_at": row["verified_at"],
        }
        for row in rows_to_return
    ]

