"""JobFit API: authenticated career intelligence, multi-provider opportunities, and resume center."""
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
from fastapi import FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from backend.ats_engine import evaluate_ats_readiness, optimize_resume_for_job
from backend.career_engine import analyze_profile, analyze_resume, normalize_skills, suggested_roles
from backend.database import (
    add_user_application,
    delete_saved_opportunity,
    delete_user_application,
    delete_user_resume,
    get_analysis_by_id,
    get_analysis_history,
    get_requirements,
    get_saved_opportunities,
    get_user_applications,
    get_user_profile,
    get_user_resume_by_id,
    get_user_resumes,
    init_db,
    save_analysis,
    save_opportunity_bookmark,
    save_user_resume,
    update_application_status,
    upsert_requirement,
    upsert_user_profile,
)
from backend.live_data import live_jobs, provider_status
from backend.opportunity_engine import explain_opportunity_match, normalize_opportunity
from backend.resume_engine import (
    extract_resume_text,
    generate_resume_docx,
    generate_resume_pdf,
    parse_raw_resume_to_document,
)

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="JobFit Career Intelligence API",
    version="4.0.0",
    description="Live student IT career analytics, ATS resume center, and verified opportunities hub.",
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
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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
        item = str(value).strip()
        key = item.lower()
        if item and len(item) <= 100 and key not in seen:
            result.append(item)
            seen.add(key)
    return result


def current_user(request: Request) -> dict[str, Any]:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Sign in with Google or a developer session to use JobFit.")
    return user


# ============================================================================
# Pydantic Request Models
# ============================================================================

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


class StudentProfileComprehensive(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str | None = None
    phone: str = Field(default="", max_length=30)
    location: str = Field(default="", max_length=100)
    degree: str = Field(default="B.Tech", max_length=80)
    branch: str = Field(default="CSE", max_length=50)
    college: str = Field(default="", max_length=120)
    academic_year: str = Field(default="Final Year", max_length=40)
    graduation_year: int = Field(default=2026, ge=2020, le=2040)
    cgpa: float = Field(default=8.0, ge=0.0, le=10.0)
    backlogs: int = Field(default=0, ge=0, le=20)
    skills: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    projects: list[dict[str, Any]] | int = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    internships: list[dict[str, Any]] | int = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    github: str = Field(default="", max_length=200)
    linkedin: str = Field(default="", max_length=200)
    portfolio: str = Field(default="", max_length=200)
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: str = Field(default="Any", max_length=30)
    target_roles: list[str] = Field(default_factory=list)
    opportunity_preference: str = Field(default="Both", max_length=30)


class ResumeTextRequest(BaseModel):
    text: str = Field(min_length=30, max_length=100000)
    target_role: str = Field(min_length=2, max_length=100)


class ResumeSavePayload(BaseModel):
    id: int | None = None
    title: str = Field(default="My Resume", min_length=2, max_length=120)
    target_role: str = Field(default="Software Developer", min_length=2, max_length=100)
    template_id: str = Field(default="classic", max_length=40)
    content: dict[str, Any]
    ats_score: int = Field(default=0, ge=0, le=100)


class ResumeATSCheckPayload(BaseModel):
    resume_data: dict[str, Any] | str
    target_role: str = Field(default="Software Developer", min_length=2, max_length=100)


class ResumeOptimizePayload(BaseModel):
    resume_data: dict[str, Any] | str
    job_description: str = Field(min_length=10, max_length=100000)
    job_title: str = Field(default="Target Opportunity", min_length=2, max_length=100)


class ResumeExportPayload(BaseModel):
    resume_data: dict[str, Any]
    template_id: str = Field(default="classic", max_length=40)


class OpportunityBookmarkPayload(BaseModel):
    opportunity: dict[str, Any]


class WhyMatchPayload(BaseModel):
    opportunity: dict[str, Any]
    profile: dict[str, Any] | None = None


class ApplicationPayload(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    opportunity_id: str | None = None
    status: str = Field(default="Saved", max_length=40)
    applied_date: str | None = None
    interview_date: str | None = None
    notes: str = Field(default="", max_length=2000)
    url: str = Field(default="", max_length=500)


class ApplicationStatusUpdatePayload(BaseModel):
    status: str = Field(min_length=2, max_length=40)
    notes: str | None = None
    interview_date: str | None = None


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


# ============================================================================
# System & Auth Endpoints
# ============================================================================

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "jobfit-student-career-intelligence",
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
        "name": "Local Student Developer",
        "email": "student.dev@jobfit.local",
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


# ============================================================================
# Profile Endpoints
# ============================================================================

@app.get("/api/profile")
async def get_profile(request: Request):
    user = current_user(request)
    profile = get_user_profile(user["email"])
    if not profile:
        profile = {
            "name": user.get("name", "Student Candidate"),
            "email": user.get("email"),
            "degree": "B.Tech",
            "branch": "CSE",
            "college": "",
            "academic_year": "Final Year",
            "graduation_year": 2026,
            "cgpa": 8.0,
            "backlogs": 0,
            "skills": ["Python", "SQL", "Git", "REST API"],
            "projects": 2,
            "internships": 0,
            "target_roles": ["Software Developer"],
            "opportunity_preference": "Both",
            "remote_preference": "Any",
            "preferred_locations": ["Bengaluru", "Hyderabad", "Remote"],
        }
    return {"success": True, "data": profile}


@app.put("/api/profile")
async def update_profile(request: Request, payload: StudentProfileComprehensive):
    user = current_user(request)
    data = payload.model_dump()
    data["email"] = user["email"]
    saved = upsert_user_profile(user["email"], data)
    return {"success": True, "data": saved}


# ============================================================================
# Career Analysis Endpoints (Preserved & Enhanced)
# ============================================================================

@app.post("/api/career/analyze")
async def analyze(request: Request, profile: StudentProfile):
    user = current_user(request)
    data = profile.model_dump()
    job_data = await live_jobs(profile.target_role, user_skills=normalize_skills(profile.technical_skills))
    analysis = analyze_profile(data, get_requirements(profile.target_role), job_data.get("jobs", []))
    analysis["recommended_jobs"] = job_data.get("jobs", [])[:8]
    analysis["job_source"] = {key: job_data.get(key) for key in ("provider", "provider_url", "live", "updated_at", "notice", "error")}
    analysis["id"] = save_analysis(data, analysis, user_email=user["email"])
    return {
        "success": True,
        "profile": data,
        "analysis": analysis,
        "disclaimer": "Readiness is educational career intelligence based on your profile evidence and live job signals; it is not a hiring decision or recruitment guarantee."
    }


@app.get("/api/career/history")
async def career_history(request: Request, limit: int = Query(8, ge=1, le=20)):
    user = current_user(request)
    return {"success": True, "data": get_analysis_history(limit, user_email=user["email"])}


@app.get("/api/career/history/{analysis_id}")
async def career_history_item(request: Request, analysis_id: int):
    current_user(request)
    item = get_analysis_by_id(analysis_id)
    if not item:
        raise HTTPException(404, "Assessment record not found.")
    return {"success": True, "data": item}


# ============================================================================
# Opportunities Hub Endpoints
# ============================================================================

@app.get("/api/jobs")
@app.get("/api/opportunities")
async def get_opportunities(
    request: Request,
    query: str = Query("Software Developer", min_length=1, max_length=100),
    category: str | None = Query(None, max_length=50),
    location: str | None = Query(None, max_length=100),
    country: str = Query("in", pattern="^[a-z]{2}$"),
    page: int = Query(1, ge=1, le=20),
    level: str | None = Query(None)
):
    user = current_user(request)
    profile = get_user_profile(user["email"])
    user_skills = None
    if profile:
        raw_skills = profile.get("skills") or profile.get("technical_skills") or []
        user_skills = set(normalize_skills(raw_skills))

    data = await live_jobs(
        query=query,
        location=location,
        country=country,
        page=page,
        level=level,
        category=category,
        user_skills=user_skills
    )
    return {"success": True, "data": data}


@app.post("/api/opportunities/why-match")
async def why_opportunity_match(request: Request, payload: WhyMatchPayload):
    user = current_user(request)
    profile_data = payload.profile
    if not profile_data:
        profile_data = get_user_profile(user["email"]) or {}
    match_evidence = explain_opportunity_match(payload.opportunity, profile_data)
    return {"success": True, "data": match_evidence}


@app.get("/api/opportunities/saved")
async def list_saved_opportunities(request: Request):
    user = current_user(request)
    saved = get_saved_opportunities(user["email"])
    return {"success": True, "data": saved}


@app.post("/api/opportunities/save")
async def bookmark_opportunity(request: Request, payload: OpportunityBookmarkPayload):
    user = current_user(request)
    bookmark_id = save_opportunity_bookmark(user["email"], payload.opportunity)
    return {"success": True, "id": bookmark_id, "message": "Opportunity saved to your workspace."}


@app.delete("/api/opportunities/save/{opportunity_id}")
async def unbookmark_opportunity(request: Request, opportunity_id: str):
    user = current_user(request)
    deleted = delete_saved_opportunity(user["email"], opportunity_id)
    return {"success": deleted}


# ============================================================================
# Resume Center Endpoints
# ============================================================================

@app.post("/api/resume/analyze-text")
async def resume_text(request: Request, payload: ResumeTextRequest):
    current_user(request)
    return {"success": True, "data": analyze_resume(payload.text, payload.target_role)}


@app.post("/api/resume/upload-and-analyze")
@app.post("/api/resume/analyze")
async def resume_file_upload(
    request: Request,
    target_role: str = Form("Software Developer"),
    file: UploadFile = File(...)
):
    current_user(request)
    if not file.filename:
        raise HTTPException(422, "Please select a resume file to upload.")

    suffix = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in {"pdf", "docx", "txt"}:
        raise HTTPException(422, "Unsupported format. Please upload a .pdf, .docx, or .txt resume.")

    content = await file.read()
    if len(content) > 4 * 1024 * 1024:
        raise HTTPException(413, "File size exceeds the 4 MB limit.")

    try:
        extracted_text = extract_resume_text(file.filename, content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(422, f"Could not process {file.filename}: {str(exc)}") from exc

    structured_doc = parse_raw_resume_to_document(extracted_text)
    ats_result = evaluate_ats_readiness(structured_doc, target_role)

    return {
        "success": True,
        "filename": file.filename,
        "text_preview": extracted_text[:400],
        "document": structured_doc,
        "ats_result": ats_result,
        "data": ats_result,  # Backward compatibility
    }


@app.post("/api/resume/ats-check")
async def run_ats_check(request: Request, payload: ResumeATSCheckPayload):
    current_user(request)
    result = evaluate_ats_readiness(payload.resume_data, payload.target_role)
    return {"success": True, "data": result}


@app.post("/api/resume/optimize-for-job")
async def run_job_optimization(request: Request, payload: ResumeOptimizePayload):
    current_user(request)
    result = optimize_resume_for_job(payload.resume_data, payload.job_description, payload.job_title)
    return {"success": True, "data": result}


@app.get("/api/resume/my-resumes")
async def list_my_resumes(request: Request):
    user = current_user(request)
    resumes = get_user_resumes(user["email"])
    return {"success": True, "data": resumes}


@app.post("/api/resume/save")
@app.post("/api/resume/create")
async def save_or_create_resume(request: Request, payload: ResumeSavePayload):
    user = current_user(request)
    doc_id = save_user_resume(user["email"], payload.model_dump())
    return {"success": True, "id": doc_id, "message": "Resume saved successfully."}


@app.get("/api/resume/{resume_id}")
async def get_single_resume(request: Request, resume_id: int):
    user = current_user(request)
    item = get_user_resume_by_id(user["email"], resume_id)
    if not item:
        raise HTTPException(404, "Resume not found.")
    return {"success": True, "data": item}


@app.delete("/api/resume/{resume_id}")
async def delete_resume(request: Request, resume_id: int):
    user = current_user(request)
    deleted = delete_user_resume(user["email"], resume_id)
    return {"success": deleted}


@app.post("/api/resume/export-pdf")
async def export_pdf(request: Request, payload: ResumeExportPayload):
    current_user(request)
    try:
        pdf_bytes = generate_resume_pdf(payload.resume_data, template_id=payload.template_id)
    except Exception as exc:
        raise HTTPException(500, f"Error generating PDF: {str(exc)}") from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=JobFit_Resume.pdf"}
    )


@app.post("/api/resume/export-docx")
async def export_docx(request: Request, payload: ResumeExportPayload):
    current_user(request)
    try:
        docx_bytes = generate_resume_docx(payload.resume_data, template_id=payload.template_id)
    except Exception as exc:
        raise HTTPException(500, f"Error generating DOCX: {str(exc)}") from exc

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=JobFit_Resume.docx"}
    )


# ============================================================================
# Application Tracker Endpoints
# ============================================================================

@app.get("/api/applications")
async def list_applications(request: Request):
    user = current_user(request)
    apps = get_user_applications(user["email"])
    return {"success": True, "data": apps}


@app.post("/api/applications")
async def create_application(request: Request, payload: ApplicationPayload):
    user = current_user(request)
    app_id = add_user_application(user["email"], payload.model_dump())
    return {"success": True, "id": app_id, "message": "Application tracked successfully."}


@app.patch("/api/applications/{app_id}/status")
async def update_app_status(request: Request, app_id: int, payload: ApplicationStatusUpdatePayload):
    user = current_user(request)
    updated = update_application_status(
        user["email"],
        app_id,
        status=payload.status,
        notes=payload.notes,
        interview_date=payload.interview_date
    )
    if not updated:
        raise HTTPException(404, "Application record not found.")
    return {"success": True, "message": f"Application status updated to {payload.status}."}


@app.delete("/api/applications/{app_id}")
async def remove_application(request: Request, app_id: int):
    user = current_user(request)
    deleted = delete_user_application(user["email"], app_id)
    return {"success": deleted}


# ============================================================================
# Student Dashboard Aggregator
# ============================================================================

@app.get("/api/dashboard/summary")
async def dashboard_summary(request: Request):
    user = current_user(request)
    email = user["email"]

    profile = get_user_profile(email)
    resumes = get_user_resumes(email)
    saved_opps = get_saved_opportunities(email)
    applications = get_user_applications(email)
    analyses = get_analysis_history(1, user_email=email)

    top_ats = max((r.get("ats_score", 0) for r in resumes), default=0)
    latest_analysis = analyses[0]["analysis"] if analyses else None

    # Compute application status counts
    app_counts: dict[str, int] = {}
    for a in applications:
        st = a.get("status", "Saved")
        app_counts[st] = app_counts.get(st, 0) + 1

    next_steps = []
    if not profile:
        next_steps.append("Complete your Student Profile to unlock tailored opportunity matching.")
    if not resumes:
        next_steps.append("Create or upload your resume in Resume Center to verify ATS readiness.")
    elif top_ats < 75:
        next_steps.append("Run ATS Readiness Checker and add quantifiable STAR project metrics.")
    if len(applications) < 3:
        next_steps.append("Explore Opportunities Hub and track your initial 3 target internships or fresher roles.")
    if latest_analysis and latest_analysis.get("skill_gap", {}).get("priority"):
        p_skill = latest_analysis["skill_gap"]["priority"][0]
        next_steps.append(f"Master priority skill gap: {p_skill} to strengthen your target role readiness.")

    return {
        "success": True,
        "data": {
            "student_name": profile.get("name") if profile else user.get("name", "Student"),
            "target_role": profile.get("target_role", "Software Developer") if profile else "Software Developer",
            "ats_readiness_score": top_ats or (latest_analysis.get("readiness_score", 65) if latest_analysis else 65),
            "resumes_count": len(resumes),
            "saved_opportunities_count": len(saved_opps),
            "applications_count": len(applications),
            "application_stats": app_counts,
            "next_best_actions": next_steps[:4],
            "recent_saved": saved_opps[:3],
        }
    }


# ============================================================================
# Verified Company Requirements (Preserved)
# ============================================================================

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


# ============================================================================
# Frontend Static Routing
# ============================================================================

@app.get("/login")
async def login_page():
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/")
async def index(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/login")
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
