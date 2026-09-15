"""SQLite persistence for JobFit analyses, verified company criteria, profiles, resumes, and applications."""
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
    db_env = os.getenv("DATABASE_PATH", "").strip()
    db_path = Path(db_env) if db_env else DEFAULT_DB_PATH
    if str(db_path) != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path), timeout=15)
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
                user_email TEXT,
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
        # Student Profile Table
        con.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT UNIQUE NOT NULL,
                profile_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Resumes Table (Multiple versions per user)
        con.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                title TEXT NOT NULL,
                target_role TEXT NOT NULL,
                template_id TEXT NOT NULL DEFAULT 'classic',
                resume_json TEXT NOT NULL,
                ats_score INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Saved Opportunities Bookmarks
        con.execute("""
            CREATE TABLE IF NOT EXISTS saved_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,
                opportunity_json TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                UNIQUE(user_email, opportunity_id)
            )
        """)
        # Application Tracker Table
        con.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                opportunity_id TEXT,
                status TEXT NOT NULL DEFAULT 'Saved',
                applied_date TEXT,
                interview_date TEXT,
                notes TEXT,
                url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Migration for existing databases
        cursor = con.execute("PRAGMA table_info(career_analyses)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        if "user_email" not in existing_cols:
            con.execute("ALTER TABLE career_analyses ADD COLUMN user_email TEXT")

        con.execute("CREATE INDEX IF NOT EXISTS idx_career_analyses_timestamp ON career_analyses(timestamp DESC)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_career_analyses_user ON career_analyses(user_email)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_company_requirements_role ON company_requirements(target_role)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_email)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes(user_email)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_saved_opps_user ON saved_opportunities(user_email)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_email)")

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


# ============================================================================
# Profile CRUD
# ============================================================================

def get_user_profile(user_email: str) -> dict[str, Any] | None:
    with _connection() as con:
        row = con.execute("SELECT profile_json, updated_at FROM profiles WHERE user_email = ?", (user_email.lower(),)).fetchone()
        if not row:
            return None
        data = json.loads(row["profile_json"])
        data["updated_at"] = row["updated_at"]
        return data


def upsert_user_profile(user_email: str, profile: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    cleaned_email = user_email.lower()
    profile["email"] = cleaned_email
    with _connection() as con:
        con.execute(
            """
            INSERT INTO profiles (user_email, profile_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_email) DO UPDATE SET
                profile_json = excluded.profile_json,
                updated_at = excluded.updated_at
            """,
            (cleaned_email, json.dumps(profile), now)
        )
    profile["updated_at"] = now
    return profile


# ============================================================================
# Resumes CRUD
# ============================================================================

def get_user_resumes(user_email: str) -> list[dict[str, Any]]:
    with _connection() as con:
        rows = con.execute(
            """
            SELECT id, user_email, title, target_role, template_id, resume_json, ats_score, created_at, updated_at
            FROM resumes
            WHERE user_email = ?
            ORDER BY updated_at DESC
            """,
            (user_email.lower(),)
        ).fetchall()
        result = []
        for r in rows:
            item = dict(r)
            item["content"] = json.loads(r["resume_json"])
            result.append(item)
        return result


def get_user_resume_by_id(user_email: str, resume_id: int) -> dict[str, Any] | None:
    with _connection() as con:
        row = con.execute(
            """
            SELECT id, user_email, title, target_role, template_id, resume_json, ats_score, created_at, updated_at
            FROM resumes
            WHERE id = ? AND user_email = ?
            """,
            (resume_id, user_email.lower())
        ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["content"] = json.loads(row["resume_json"])
        return item


def save_user_resume(user_email: str, resume_data: dict[str, Any]) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cleaned_email = user_email.lower()
    resume_id = resume_data.get("id")
    title = resume_data.get("title") or f"{resume_data.get('target_role', 'General')} Resume"
    target_role = resume_data.get("target_role", "Software Developer")
    template_id = resume_data.get("template_id", "classic")
    ats_score = int(resume_data.get("ats_score", 0))
    content_json = json.dumps(resume_data.get("content", {}))

    with _connection() as con:
        if resume_id:
            # Update existing
            con.execute(
                """
                UPDATE resumes
                SET title = ?, target_role = ?, template_id = ?, resume_json = ?, ats_score = ?, updated_at = ?
                WHERE id = ? AND user_email = ?
                """,
                (title, target_role, template_id, content_json, ats_score, now, resume_id, cleaned_email)
            )
            return int(resume_id)
        else:
            cur = con.execute(
                """
                INSERT INTO resumes (user_email, title, target_role, template_id, resume_json, ats_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (cleaned_email, title, target_role, template_id, content_json, ats_score, now, now)
            )
            return int(cur.lastrowid)


def delete_user_resume(user_email: str, resume_id: int) -> bool:
    with _connection() as con:
        cur = con.execute("DELETE FROM resumes WHERE id = ? AND user_email = ?", (resume_id, user_email.lower()))
        return cur.rowcount > 0


# ============================================================================
# Saved Opportunities Bookmarks CRUD
# ============================================================================

def get_saved_opportunities(user_email: str) -> list[dict[str, Any]]:
    with _connection() as con:
        rows = con.execute(
            """
            SELECT id, opportunity_id, opportunity_json, saved_at
            FROM saved_opportunities
            WHERE user_email = ?
            ORDER BY id DESC
            """,
            (user_email.lower(),)
        ).fetchall()
        result = []
        for r in rows:
            opp = json.loads(r["opportunity_json"])
            opp["saved_id"] = r["id"]
            opp["saved_at"] = r["saved_at"]
            result.append(opp)
        return result


def save_opportunity_bookmark(user_email: str, opp_data: dict[str, Any]) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cleaned_email = user_email.lower()
    opp_id = str(opp_data.get("id"))
    with _connection() as con:
        cur = con.execute(
            """
            INSERT OR REPLACE INTO saved_opportunities (user_email, opportunity_id, opportunity_json, saved_at)
            VALUES (?, ?, ?, ?)
            """,
            (cleaned_email, opp_id, json.dumps(opp_data), now)
        )
        return int(cur.lastrowid)


def delete_saved_opportunity(user_email: str, opportunity_id: str) -> bool:
    with _connection() as con:
        cur = con.execute(
            "DELETE FROM saved_opportunities WHERE user_email = ? AND (opportunity_id = ? OR id = ?)",
            (user_email.lower(), str(opportunity_id), int(opportunity_id) if str(opportunity_id).isdigit() else -1)
        )
        return cur.rowcount > 0


# ============================================================================
# Application Tracker CRUD
# ============================================================================

def get_user_applications(user_email: str) -> list[dict[str, Any]]:
    with _connection() as con:
        rows = con.execute(
            """
            SELECT id, company, role, opportunity_id, status, applied_date, interview_date, notes, url, created_at, updated_at
            FROM applications
            WHERE user_email = ?
            ORDER BY updated_at DESC
            """,
            (user_email.lower(),)
        ).fetchall()
        return [dict(r) for r in rows]


def add_user_application(user_email: str, app_data: dict[str, Any]) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cleaned_email = user_email.lower()
    with _connection() as con:
        cur = con.execute(
            """
            INSERT INTO applications
            (user_email, company, role, opportunity_id, status, applied_date, interview_date, notes, url, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cleaned_email,
                app_data["company"],
                app_data["role"],
                app_data.get("opportunity_id"),
                app_data.get("status", "Saved"),
                app_data.get("applied_date", now[:10]),
                app_data.get("interview_date"),
                app_data.get("notes", ""),
                app_data.get("url", ""),
                now,
                now,
            )
        )
        return int(cur.lastrowid)


def update_application_status(
    user_email: str,
    app_id: int,
    status: str,
    notes: str | None = None,
    interview_date: str | None = None
) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with _connection() as con:
        if notes is not None and interview_date is not None:
            cur = con.execute(
                """
                UPDATE applications
                SET status = ?, notes = ?, interview_date = ?, updated_at = ?
                WHERE id = ? AND user_email = ?
                """,
                (status, notes, interview_date, now, app_id, user_email.lower())
            )
        elif notes is not None:
            cur = con.execute(
                """
                UPDATE applications
                SET status = ?, notes = ?, updated_at = ?
                WHERE id = ? AND user_email = ?
                """,
                (status, notes, now, app_id, user_email.lower())
            )
        else:
            cur = con.execute(
                """
                UPDATE applications
                SET status = ?, updated_at = ?
                WHERE id = ? AND user_email = ?
                """,
                (status, now, app_id, user_email.lower())
            )
        return cur.rowcount > 0


def delete_user_application(user_email: str, app_id: int) -> bool:
    with _connection() as con:
        cur = con.execute("DELETE FROM applications WHERE id = ? AND user_email = ?", (app_id, user_email.lower()))
        return cur.rowcount > 0


# ============================================================================
# Career Analyses & Company Requirements (Preserved)
# ============================================================================

def save_analysis(profile: dict[str, Any], analysis: dict[str, Any], user_email: str | None = None) -> int:
    with _connection() as con:
        cur = con.execute(
            """
            INSERT INTO career_analyses (timestamp, student_name, user_email, target_role, readiness_score, profile_json, analysis_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                profile["name"],
                (user_email or "").lower(),
                profile["target_role"],
                analysis["readiness_score"],
                json.dumps(profile),
                json.dumps(analysis),
            ),
        )
        return int(cur.lastrowid)


def get_analysis_history(limit: int = 8, user_email: str | None = None) -> list[dict[str, Any]]:
    with _connection() as con:
        if user_email:
            rows = con.execute(
                """
                SELECT id, timestamp, student_name, target_role, readiness_score, analysis_json
                FROM career_analyses
                WHERE user_email = ? OR user_email = '' OR user_email IS NULL
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_email.lower(), limit),
            ).fetchall()
        else:
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
