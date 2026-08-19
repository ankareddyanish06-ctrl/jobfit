"""SQLite persistence for JobFit analyses and verified company criteria."""
import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
DEFAULT_DB_PATH=Path(__file__).resolve().parent.parent/"database.db"
DB_PATH=Path(os.getenv("DATABASE_PATH",DEFAULT_DB_PATH))
def _connection():
 DB_PATH.parent.mkdir(parents=True,exist_ok=True); con=sqlite3.connect(DB_PATH,timeout=10); con.row_factory=sqlite3.Row; return con
def init_db():
 with _connection() as con:
  con.execute("CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT NOT NULL,cgpa REAL NOT NULL,internships INTEGER NOT NULL,projects INTEGER NOT NULL,skills TEXT NOT NULL,skill_score REAL NOT NULL,prediction REAL NOT NULL)")
  con.execute("CREATE TABLE IF NOT EXISTS career_analyses (id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT NOT NULL,student_name TEXT NOT NULL,target_role TEXT NOT NULL,readiness_score REAL NOT NULL,profile_json TEXT NOT NULL,analysis_json TEXT NOT NULL)")
  con.execute("CREATE TABLE IF NOT EXISTS company_requirements (id INTEGER PRIMARY KEY AUTOINCREMENT,company TEXT NOT NULL,target_role TEXT NOT NULL,min_cgpa REAL NOT NULL,max_backlogs INTEGER NOT NULL,branches_json TEXT NOT NULL,skills_json TEXT NOT NULL,graduation_year INTEGER,source_url TEXT NOT NULL,verified_at TEXT NOT NULL,UNIQUE(company,target_role,graduation_year))")
  con.execute("CREATE INDEX IF NOT EXISTS idx_career_analyses_timestamp ON career_analyses(timestamp DESC)")
def save_analysis(profile:dict[str,Any],analysis:dict[str,Any])->int:
 with _connection() as con:
  cur=con.execute("INSERT INTO career_analyses (timestamp,student_name,target_role,readiness_score,profile_json,analysis_json) VALUES (?,?,?,?,?,?)",(datetime.now(timezone.utc).isoformat(),profile["name"],profile["target_role"],analysis["readiness_score"],json.dumps(profile),json.dumps(analysis))); return int(cur.lastrowid)
def get_analysis_history(limit:int=8)->list[dict[str,Any]]:
 with _connection() as con: rows=con.execute("SELECT id,timestamp,student_name,target_role,readiness_score,analysis_json FROM career_analyses ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
 return [{**dict(row),"analysis":json.loads(row["analysis_json"])} for row in rows]
def upsert_requirement(item:dict[str,Any])->int:
 with _connection() as con:
  con.execute("DELETE FROM company_requirements WHERE company=? AND target_role=? AND graduation_year IS ?",(item["company"],item["target_role"],item.get("graduation_year")))
  cur=con.execute("INSERT INTO company_requirements (company,target_role,min_cgpa,max_backlogs,branches_json,skills_json,graduation_year,source_url,verified_at) VALUES (?,?,?,?,?,?,?,?,?,?)",(item["company"],item["target_role"],item["min_cgpa"],item["max_backlogs"],json.dumps(item["branches"]),json.dumps(item["skills"]),item.get("graduation_year"),item["source_url"],datetime.now(timezone.utc).isoformat())); return int(cur.lastrowid)
def get_requirements(role:str)->list[dict[str,Any]]:
 with _connection() as con: rows=con.execute("SELECT * FROM company_requirements WHERE target_role=? ORDER BY verified_at DESC",(role,)).fetchall()
 return [{"company":row["company"],"target_role":row["target_role"],"min_cgpa":row["min_cgpa"],"max_backlogs":row["max_backlogs"],"branches":json.loads(row["branches_json"]),"skills":json.loads(row["skills_json"]),"graduation_year":row["graduation_year"],"source_url":row["source_url"],"verified_at":row["verified_at"]} for row in rows]
def save_prediction(cgpa,internships,projects,skills,skill_score,prediction):
 with _connection() as con:
  cur=con.execute("INSERT INTO predictions (timestamp,cgpa,internships,projects,skills,skill_score,prediction) VALUES (?,?,?,?,?,?,?)",(datetime.now(timezone.utc).isoformat(),cgpa,internships,projects,json.dumps(skills),skill_score,prediction)); return int(cur.lastrowid)
def get_history(limit=10):
 with _connection() as con: rows=con.execute("SELECT id,timestamp,cgpa,internships,projects,skills,skill_score,prediction FROM predictions ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
 return [{**dict(row),"skills":json.loads(row["skills"])} for row in rows]
