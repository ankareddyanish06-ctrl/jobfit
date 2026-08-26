"""JobFit API: authenticated career analysis and live multi-provider job search."""
from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load local environment configuration
load_dotenv()

from authlib.integrations.starlette_client import OAuth

from fastapi import FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from backend.career_engine import analyze_profile, analyze_resume, normalize_skills, suggested_roles
from backend.database import get_analysis_by_id, get_analysis_history, get_requirements, init_db, save_analysis, upsert_requirement
from backend.live_data import live_jobs, provider_status

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="JobFit Career Intelligence API",
    version="4.0.0",
    description="Live IT career analytics, skill-gap diagnostics, and verified employer criteria platform.",
    lifespan=lifespan
)

session_secret = os.getenv("SESSION_SECRET", "development-only-change-this-before-deployment-secret-key-398217")
cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
app.add_middleware(SessionMiddleware, secret_key=session_secret, https_only=cookie_secure, same_site="lax")

origins = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "").split(",") if item.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Admin-Key"]
    )

oauth = OAuth()
if os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"):
    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"}
    )


def clean_list(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        key = item.lower()
        if item and len(item) <= 80 and key not in seen:
            result.append(item)
            seen.add(key)
    return result


def current_user(request: Request) -> dict[str, Any]:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Sign in with Google or a developer session to use JobFit.")
    return user


class StudentProfile(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    degree: str = Field(min_length=2, max_length=80)
    branch: str = Field(min_length=2, max_length=30)
    graduation_year: int = Field(ge=2020, le=2040)
    cgpa: float = Field(ge=0, le=10)
    backlogs: int = Field(default=0, ge=0, le=20)
    technical_skills: list[str] = Field(min_length=1, max_length=50)
    soft_skills: list[str] = Field(default_factory=list, max_length=20)
    certifications: list[str] = Field(default_factory=list, max_length=30)
    projects: int = Field(default=0, ge=0, le=40)
    internships: int = Field(default=0, ge=0, le=20)
    aptitude_score: float = Field(default=60.0, ge=0, le=100)
    interview_score: float = Field(default=55.0, ge=0, le=100)
    target_role: str = Field(min_length=2, max_length=100)

    @field_validator("name", "degree", "target_role")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("branch")
    @classmethod
    def normalize_branch(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("technical_skills", "soft_skills", "certifications")
    @classmethod
    def valid_lists(cls, values: list[str], info) -> list[str]:
        cleaned = clean_list(values)
        if info.field_name == "technical_skills" and not cleaned:
            raise ValueError("Add at least one technical skill.")
        return cleaned


class ResumeTextRequest(BaseModel):
    text: str = Field(min_length=30, max_length=100000)
    target_role: str = Field(min_length=2, max_length=100)


class CompanyRequirement(BaseModel):
    company: str = Field(min_length=2, max_length=100)
    target_role: str = Field(min_length=2, max_length=100)
    min_cgpa: float = Field(ge=0, le=10)
    max_backlogs: int = Field(ge=0, le=20)
    branches: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    graduation_year: int | None = Field(default=None, ge=2020, le=2040)
    source_url: str = Field(min_length=10, max_length=500)

    @field_validator("branches", "skills")
    @classmethod
    def valid_lists(cls, values: list[str]) -> list[str]:
        return clean_list(values)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "jobfit-live-career-intelligence",
        "version": "4.0.0",
        "providers": provider_status()
    }


@app.get("/api/auth/config")
async def auth_config():
    return {
        "google_enabled": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),
        "development_login_enabled": os.getenv("ENABLE_DEV_LOGIN", "false").lower() == "true",
        "providers": provider_status()
    }


@app.get("/auth/google/login")
async def google_login(request: Request):
    if not (os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")):
        raise HTTPException(503, "Google OAuth is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env.")
    return await oauth.google.authorize_redirect(request, request.url_for("google_callback"))


@app.get("/auth/google/callback", name="google_callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo") or await oauth.google.parse_id_token(request, token)
    request.session["user"] = {
        "name": userinfo.get("name") or userinfo.get("email", "JobFit User"),
        "email": userinfo.get("email"),
        "picture": userinfo.get("picture")
    }
    return RedirectResponse(url="/")


@app.post("/auth/dev-login")
async def development_login(request: Request):
    if os.getenv("ENABLE_DEV_LOGIN", "false").lower() != "true":
        raise HTTPException(404, "Development sign-in is disabled in production configuration.")
    request.session["user"] = {
        "name": "Local Developer",
        "email": "dev.session@jobfit.local",
        "picture": None
    }
    return {"success": True, "user": request.session["user"]}


@app.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"success": True}


@app.get("/api/auth/me")
async def me(request: Request):
    return {"user": request.session.get("user")}


@app.get("/api/role-suggestions")
async def roles():
    return {"data": suggested_roles()}


@app.get("/api/jobs")
async def jobs(
    request: Request,
    query: str = Query("Software Developer", min_length=2, max_length=100),
    location: str | None = Query(None, max_length=100),
    country: str = Query("in", pattern="^[a-z]{2}$"),
    page: int = Query(1, ge=1, le=20),
    level: str | None = Query(None)
):
    current_user(request)
    return {"success": True, "data": await live_jobs(query, location, country, page, level)}


@app.post("/api/career/analyze")
async def analyze(request: Request, profile: StudentProfile):
    current_user(request)
    data = profile.model_dump()
    job_data = await live_jobs(profile.target_role, user_skills=normalize_skills(profile.technical_skills))
    analysis = analyze_profile(data, get_requirements(profile.target_role), job_data.get("jobs", []))
    analysis["recommended_jobs"] = job_data.get("jobs", [])[:8]
    analysis["job_source"] = {key: job_data.get(key) for key in ("provider", "provider_url", "live", "updated_at", "notice", "error")}
    analysis["id"] = save_analysis(data, analysis)
    return {
        "success": True,
        "profile": data,
        "analysis": analysis,
        "disclaimer": "Readiness is educational career intelligence based on your profile evidence and live job signals; it is not a hiring decision or recruitment guarantee."
    }


@app.get("/api/career/history")
async def career_history(request: Request, limit: int = Query(8, ge=1, le=20)):
    current_user(request)
    return {"success": True, "data": get_analysis_history(limit)}


@app.get("/api/career/history/{analysis_id}")
async def career_history_item(request: Request, analysis_id: int):
    current_user(request)
    item = get_analysis_by_id(analysis_id)
    if not item:
        raise HTTPException(404, "Assessment record not found.")
    return {"success": True, "data": item}


@app.post("/api/resume/analyze-text")
async def resume_text(request: Request, payload: ResumeTextRequest):
    current_user(request)
    return {"success": True, "data": analyze_resume(payload.text, payload.target_role)}


@app.post("/api/resume/analyze")
async def resume_file(request: Request, target_role: str = Form(...), file: UploadFile = File(...)):
    current_user(request)
    if not file.filename or Path(file.filename).suffix.lower() not in {".pdf", ".txt"}:
        raise HTTPException(422, "Upload a valid text-based PDF or TXT résumé.")
    content = await file.read()
    if len(content) > 4 * 1024 * 1024:
        raise HTTPException(413, "File size exceeds the 4 MB limit.")
    try:
        if file.filename.lower().endswith(".pdf"):
            import pypdf
            reader = pypdf.PdfReader(BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            text = content.decode("utf-8", errors="ignore")
    except Exception as exc:
        raise HTTPException(422, "The résumé could not be read. Please upload a standard text PDF or plain text file.") from exc
    if len(text.strip()) < 30:
        raise HTTPException(422, "The résumé does not contain sufficient extractable text (e.g. scanned image PDFs).")
    return {"success": True, "filename": file.filename, "data": analyze_resume(text, target_role)}


@app.get("/api/company-requirements")
async def company_requirements(request: Request, role: str | None = Query(default=None, max_length=100)):
    current_user(request)
    return {"success": True, "data": get_requirements(role)}


@app.post("/api/company-requirements")
async def register_requirement(request: Request, item: CompanyRequirement, x_admin_key: str | None = Header(default=None)):
    current_user(request)
    expected = os.getenv("ADMIN_API_KEY")
    if not expected or not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(403, "Valid admin authorization key (X-Admin-Key) is required to register verified employer criteria.")
    return {"success": True, "id": upsert_requirement(item.model_dump())}


@app.get("/login")
async def login_page():
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/")
async def index(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/login")
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")

