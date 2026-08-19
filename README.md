# JobFit — Live Career Intelligence Platform

JobFit is a full-stack Python career-planning application. It evaluates a student profile against a selected role, identifies skill gaps, creates a learning roadmap, analyzes résumés, and retrieves current job-market signals.

## What is live and what requires configuration

| Feature | Status | Source / setup |
|---|---|---|
| Job search and job matching | Live now | The Muse Jobs API, refreshed at most once every 10 minutes |
| Market skills and locations | Live now | Computed from currently retrieved The Muse listings |
| Salary ranges | Live after setup | Add Adzuna API credentials as environment variables |
| Company eligibility | Verified-data workflow | An admin registers only official employer requirements and source links |
| Profile readiness | Explainable guidance | Derived from the user's profile and role requirements; **not** a placement probability |
| Résumé analysis | Live per upload | PDF/TXT parsed in memory; uploaded file is not stored |

JobFit never presents generated or unverified information as a company rule, job listing, salary fact, or hiring decision.

## Features

- Student profile: education, branch, graduation year, CGPA, backlogs, technical/soft skills, certificates, projects, internships, aptitude, and interview self-assessment
- Role paths: Data Analyst, Software Developer, ServiceNow Developer, Web Developer, and Cloud Engineer
- Explainable readiness breakdown, skill match/gaps, and prioritized next action
- Personalized seven-week learning roadmap and role-specific interview practice
- PDF/TXT résumé strength and target-role skill analysis
- Current job search, direct listing links, and profile-to-listing skill match
- Current market skill/location snapshot
- Verified employer eligibility registry with official source links and admin-only write access
- SQLite persistence for recent assessments
- Responsive mobile UI, Docker container, and Render Blueprint

## Technology

- Python 3.10+, FastAPI, Pydantic
- SQLite (use managed PostgreSQL for a public multi-user deployment)
- pypdf for text-based PDF résumé parsing
- Vanilla HTML, CSS, and JavaScript
- The Muse API for live job data
- Optional Adzuna API for live salary ranges

## Run locally in VS Code

```powershell
cd "D:\python project"
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`. API documentation is at `http://127.0.0.1:8000/docs`.

## Add live-provider credentials

1. Copy [.env.example](.env.example) to `.env`.
2. Register your app with [The Muse Developers](https://www.themuse.com/developers/api/v2) and optionally place its key in `MUSE_API_KEY`. The public endpoint works for development; a key raises rate limits.
3. Create an [Adzuna developer account](https://developer.adzuna.com/overview) and add `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` to enable current salary ranges.
4. Set `ADMIN_API_KEY` to a long random value. Do not commit `.env`.

Uvicorn does not load `.env` by itself. In PowerShell for local development, set environment variables before starting it:

```powershell
$env:MUSE_API_KEY = "your-key"
$env:ADZUNA_APP_ID = "your-id"
$env:ADZUNA_APP_KEY = "your-key"
$env:ADMIN_API_KEY = "a-long-random-secret"
uvicorn backend.main:app --reload
```

In Render, add the same values under **Environment** in the service dashboard. Keep all provider keys and `ADMIN_API_KEY` secret.

## Register verified employer eligibility

Only add an employer rule if you have checked its official careers page, campus-placement notice, or another authoritative source. Send it through the authenticated API, for example:

```powershell
$headers = @{ "X-Admin-Key" = $env:ADMIN_API_KEY; "Content-Type" = "application/json" }
$body = @{
  company = "Example Technologies"
  target_role = "software-developer"
  min_cgpa = 7.0
  max_backlogs = 0
  branches = @("CSE", "IT")
  skills = @("python", "sql", "git")
  graduation_year = 2026
  source_url = "https://careers.example.com/campus"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/company-requirements" -Headers $headers -Body $body
```

## Main endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/career/analyze` | Create an explainable role-readiness analysis |
| `GET` | `/api/jobs` | Get current listings from the live provider |
| `GET` | `/api/market` | Aggregate current listing signals |
| `POST` | `/api/resume/analyze` | Analyze a PDF/TXT résumé in memory |
| `POST` | `/api/company-requirements` | Register verified company criteria (admin key required) |
| `GET` | `/api/company-requirements?role=...` | Read verified criteria for a role |
| `GET` | `/api/health` | Deployment health check |

## Deploy with GitHub and Render

1. Create a new **empty** GitHub repository, for example `jobfit-live-career-platform`.
2. In the VS Code terminal inside this project, run:

```powershell
git init
git add .
git commit -m "Build live JobFit career intelligence platform"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/jobfit-live-career-platform.git
git push -u origin main
```

3. In Render select **New → Blueprint**, connect the GitHub repository, and deploy. Render reads `render.yaml` and `Dockerfile`.
4. In the Render service's **Environment** page, add `MUSE_API_KEY` (optional), `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, and `ADMIN_API_KEY`.
5. Every later update uses:

```powershell
git add .
git commit -m "Describe your change"
git push
```

Render redeploys automatically after a push.

## Production note

Before collecting real student data, add authentication, password hashing, privacy/consent terms, audit logs, rate limiting, and PostgreSQL. Do not train or publish an employment prediction model without a lawful, consented, representative dataset and bias/impact evaluation.
