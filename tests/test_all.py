"""Automated test suite for JobFit Student Career Intelligence & Opportunity Hub."""
import os
import pytest
from starlette.testclient import TestClient

from backend.main import app
from backend.career_engine import analyze_profile, required_skills, suggested_roles
from backend.live_data import live_jobs, normalize_skills
from backend.opportunity_engine import (
    classify_opportunity_type,
    classify_workplace_type,
    explain_opportunity_match,
    normalize_opportunity,
    STUDENT_BASELINE_PROGRAMS,
)
from backend.resume_engine import (
    generate_resume_docx,
    generate_resume_pdf,
    parse_raw_resume_to_document,
)
from backend.ats_engine import evaluate_ats_readiness, optimize_resume_for_job
from backend.database import (
    add_user_application,
    delete_saved_opportunity,
    delete_user_application,
    delete_user_resume,
    get_saved_opportunities,
    get_user_applications,
    get_user_profile,
    get_user_resumes,
    init_db,
    save_opportunity_bookmark,
    save_user_resume,
    update_application_status,
    upsert_user_profile,
)


TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_jobfit.db")


@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass
    os.environ["DATABASE_PATH"] = TEST_DB_FILE
    init_db()
    yield
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass


# ============================================================================
# 1. Career Engine Tests
# ============================================================================

def test_career_engine_known_role():
    skills, source = required_skills("Software Developer", [])
    assert "python" in skills or "java" in skills
    assert "Role Framework" in source


def test_career_engine_unknown_role():
    skills, source = required_skills("Quantum Cloud Systems Specialist", [])
    assert len(skills) > 0
    assert "Keyword" in source or "Baseline" in source


def test_career_engine_analyze_profile():
    sample_profile = {
        "name": "Alex Student",
        "degree": "B.Tech",
        "branch": "CSE",
        "graduation_year": 2026,
        "cgpa": 8.5,
        "backlogs": 0,
        "technical_skills": ["Python", "SQL", "Git", "REST API", "Docker"],
        "soft_skills": ["Problem Solving"],
        "certifications": ["AWS Cloud Practitioner"],
        "projects": 3,
        "internships": 1,
        "aptitude_score": 80.0,
        "interview_score": 75.0,
        "target_role": "Full Stack Developer",
    }
    result = analyze_profile(sample_profile, [], [])
    assert "readiness_score" in result
    assert 10 <= result["readiness_score"] <= 100
    assert "roadmap" in result
    assert len(result["roadmap"]) == 4  # 7-week sprint phases
    assert "interview_prep" in result
    assert "project_ideas" in result


# ============================================================================
# 2. Opportunity Engine Tests
# ============================================================================

def test_opportunity_type_classification():
    assert classify_opportunity_type("Software Engineer Intern", "Summer internship") == "Internships"
    assert classify_opportunity_type("Graduate Engineer Trainee", "Campus hiring") == "Graduate Programs"
    assert classify_opportunity_type("Junior Associate Developer", "Entry level role") == "Fresher Jobs"
    assert classify_opportunity_type("MLH Open Source Fellow", "Student fellowship") == "Student Programs"
    assert classify_opportunity_type("Senior Architect", "10+ years experience") == "Jobs"


def test_workplace_type_classification():
    assert classify_workplace_type("Developer", "Remote", "Work from home") == "Remote"
    assert classify_workplace_type("Engineer", "Bengaluru", "Hybrid workplace") == "Hybrid"
    assert classify_workplace_type("Analyst", "Hyderabad", "On-site office role") == "On-site"


def test_explain_opportunity_match_no_fake_prediction():
    opp = {
        "id": "test-1",
        "title": "Python Data Intern",
        "company": "Tech Corp",
        "location": "Bengaluru",
        "type": "Internships",
        "workplace_type": "Hybrid",
        "skills": ["Python", "SQL", "Git"],
    }
    profile = {
        "skills": ["Python", "Git"],
        "opportunity_preference": "Internship",
        "remote_preference": "Hybrid",
        "preferred_locations": ["Bengaluru"],
    }
    explanation = explain_opportunity_match(opp, profile)
    assert "matched_skills" in explanation
    assert "Python" in explanation["matched_skills"]
    assert "SQL" in explanation["missing_skills"]
    assert "alignment_tier" in explanation
    # Must NOT claim a fake percentage chance of hiring
    assert "chance of getting hired" not in str(explanation).lower()


# ============================================================================
# 3. Resume Engine & ATS Checker Tests
# ============================================================================

def test_raw_resume_parsing():
    raw_text = """
    Jane Doe
    jane.doe@example.com | +1 555-019-2834 | github.com/janedoe | linkedin.com/in/janedoe
    
    Summary
    Passionate computer science graduate experienced in building distributed backend services.
    
    Technical Skills
    Python, SQL, PostgreSQL, Docker, Git, REST API, React
    
    Education
    B.Tech in Computer Science — ABC University (2022-2026) | CGPA: 8.8
    
    Projects
    E-Commerce Cloud Platform | Python, Docker
    • Architected high-throughput REST APIs handling 5,000 requests per minute with 99.9% uptime.
    • Automated CI/CD deployment pipeline reducing release cycles by 40%.
    
    Certifications
    AWS Certified Cloud Practitioner
    """
    doc = parse_raw_resume_to_document(raw_text)
    assert doc["personal_info"]["name"] == "Jane Doe"
    assert doc["personal_info"]["email"] == "jane.doe@example.com"
    assert len(doc["skills"]) >= 4

    ats = evaluate_ats_readiness(doc, target_role="Backend Developer")
    assert 50 <= ats["ats_readiness_score"] <= 100
    assert ats["structure_checklist"]["contact_info"] is True
    assert ats["structure_checklist"]["education"] is True
    assert ats["structure_checklist"]["skills"] is True
    assert ats["structure_checklist"]["projects"] is True
    assert ats["metric_indicators_found"] >= 1
    assert "educational guideline" in ats["disclaimer"].lower()


def test_resume_job_optimization_honesty():
    resume_text = "Experienced in Python and Git with projects in data analysis."
    job_desc = "Looking for an engineer with Python, SQL, Docker, and AWS experience."
    opt = optimize_resume_for_job(resume_text, job_desc, "Software Engineer")
    assert "Python" in opt["matched_skills"]
    assert "SQL" in opt["missing_skills"] or "Docker" in opt["missing_skills"]
    assert "genuinely have experience" in opt["honesty_notice"]


def test_resume_pdf_and_docx_generation():
    sample_doc = {
        "personal_info": {"name": "Test User", "email": "test@user.com", "phone": "1234567890"},
        "summary": "Engineering student.",
        "education": [{"degree": "B.Tech", "institution": "State University", "year": "2026", "score": "8.5"}],
        "skills": ["Python", "SQL", "Git", "REST API"],
        "experience": [{"role": "Intern", "company": "Acme Corp", "duration": "Summer 2025", "bullets": ["Built API endpoints."]}],
        "projects": [{"title": "Cloud Hub", "tech": "Python, Docker", "bullets": ["Improved performance by 25%."], "link": "https://github.com"}],
        "certifications": ["AWS Practitioner"],
        "achievements": ["Hackathon 1st Place"],
    }

    # PDF generation test across 3 templates
    for tmpl in ("classic", "student", "developer"):
        pdf_bytes = generate_resume_pdf(sample_doc, template_id=tmpl)
        assert len(pdf_bytes) > 500
        assert pdf_bytes.startswith(b"%PDF")

    # DOCX generation test
    docx_bytes = generate_resume_docx(sample_doc, template_id="classic")
    assert len(docx_bytes) > 500
    assert docx_bytes.startswith(b"PK")  # ZIP header for DOCX


# ============================================================================
# 4. Database Multi-User Isolation Tests
# ============================================================================

def test_user_data_isolation():
    user_a = "user.a@jobfit.local"
    user_b = "user.b@jobfit.local"

    # Profile isolation
    upsert_user_profile(user_a, {"name": "User Alpha", "cgpa": 9.0})
    upsert_user_profile(user_b, {"name": "User Beta", "cgpa": 7.5})

    prof_a = get_user_profile(user_a)
    prof_b = get_user_profile(user_b)
    assert prof_a["name"] == "User Alpha"
    assert prof_b["name"] == "User Beta"

    # Resume isolation
    res_a_id = save_user_resume(user_a, {"title": "Alpha Resume", "target_role": "Backend Developer", "content": {}})
    save_user_resume(user_b, {"title": "Beta Resume", "target_role": "Data Analyst", "content": {}})

    res_a_list = get_user_resumes(user_a)
    res_b_list = get_user_resumes(user_b)
    assert len(res_a_list) == 1
    assert res_a_list[0]["title"] == "Alpha Resume"
    assert len(res_b_list) == 1
    assert res_b_list[0]["title"] == "Beta Resume"

    # User B cannot delete User A's resume
    assert delete_user_resume(user_b, res_a_id) is False
    assert len(get_user_resumes(user_a)) == 1
    assert delete_user_resume(user_a, res_a_id) is True
    assert len(get_user_resumes(user_a)) == 0

    # Application isolation
    app_a_id = add_user_application(user_a, {"company": "Google", "role": "SWE Intern", "status": "Applied"})
    app_b_id = add_user_application(user_b, {"company": "Microsoft", "role": "Data Intern", "status": "Interview"})

    assert len(get_user_applications(user_a)) == 1
    assert get_user_applications(user_a)[0]["company"] == "Google"
    assert len(get_user_applications(user_b)) == 1
    assert get_user_applications(user_b)[0]["company"] == "Microsoft"

    # User B cannot update User A's application
    assert update_application_status(user_b, app_a_id, "Offer") is False
    assert update_application_status(user_a, app_a_id, "Interview") is True
    assert get_user_applications(user_a)[0]["status"] == "Interview"


# ============================================================================
# 5. FastAPI Endpoint Security & Client Tests
# ============================================================================

def test_unauthenticated_guards():
    client = TestClient(app)

    # Protected endpoints must return 401 when not logged in
    res = client.get("/api/profile")
    assert res.status_code == 401

    res = client.get("/api/applications")
    assert res.status_code == 401

    res = client.get("/api/resume/my-resumes")
    assert res.status_code == 401

    res = client.get("/api/opportunities/saved")
    assert res.status_code == 401


def test_public_and_dev_login_flow():
    os.environ["ENABLE_DEV_LOGIN"] = "true"
    client = TestClient(app)

    # Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # Dev sign-in
    res = client.post("/auth/dev-login")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Now authenticated requests succeed
    res = client.get("/api/profile")
    assert res.status_code == 200
    assert res.json()["success"] is True

    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    assert "next_best_actions" in res.json()["data"]
