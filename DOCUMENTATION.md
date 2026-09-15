# JobFit — Live IT Career Intelligence Platform
## Complete Technical Documentation & System Reference Manual

**Author / Developer:** Anish Ankareddy  
**Project Repository:** `https://github.com/ankareddyanish06-ctrl/jobfit.git`  
**Application Type:** Full-Stack Career Intelligence & Live Market Diagnostics  
**Version:** 2.0.0 (Production Release)  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture & Data Flow](#2-system-architecture--data-flow)
3. [Technology Stack](#3-technology-stack)
4. [Visual System & Aesthetics (Black 3D Cyber Engine)](#4-visual-system--aesthetics-black-3d-cyber-engine)
5. [Core Modules & Feature Breakdown](#5-core-modules--feature-breakdown)
   - [5.1. Authentication & Session Security](#51-authentication--session-security)
   - [5.2. Evidence-Based Career Intelligence Engine](#52-evidence-based-career-intelligence-engine)
   - [5.3. Multi-Provider Live Job Search](#53-multi-provider-live-job-search)
   - [5.4. In-Memory Résumé ATS Diagnostic Lab](#54-in-memory-résumé-ats-diagnostic-lab)
   - [5.5. Verified Employer Eligibility Registry](#55-verified-employer-eligibility-registry)
6. [API Specification & Data Contracts](#6-api-specification--data-contracts)
7. [Database Schema & Persistence Layer](#7-database-schema--persistence-layer)
8. [Configuration & Environment Variables](#8-configuration--environment-variables)
9. [Local Development & Testing Guide](#9-local-development--testing-guide)
10. [Production Cloud Deployment Guide (Render, Docker, VPS)](#10-production-cloud-deployment-guide-render-docker-vps)
11. [Security, Privacy, and Ethical AI Principles](#11-security-privacy-and-ethical-ai-principles)

---

## 1. Executive Summary

**JobFit** is an enterprise-grade, evidence-driven career intelligence platform engineered for students, engineering graduates, and IT professionals. Unlike legacy placement prediction tools that rely on fabricated probability percentages, JobFit provides:

- **Mathematical Readiness Scoring**: Based on transparent weighted metrics across academics, technical competency, practical experience, aptitude, and interview performance.
- **Live Real-Time Market Intelligence**: Powered by an Adzuna-first architecture with automatic fallback to The Muse and curated telemetry.
- **Open-Ended Role Analysis**: Analyzes traditional IT roles (Full Stack, Data Scientist, DevOps) alongside modern titles (AI Engineer, Cloud Architect, Cybersecurity Analyst, Site Reliability Engineer).
- **Zero-Storage Privacy Résumé Analysis**: Inspects PDF and TXT résumés in volatile memory with zero disk persistence.
- **Verified Company Criteria**: Strict registry of verified employer eligibility with authenticated links to official company careers portals.
- **Black 3D Cyber Visual System**: Dynamic starfield canvas particle simulations, 3D CSS orbital telemetry models, glassmorphic HUD surfaces, and responsive layouts.

---

## 2. System Architecture & Data Flow

```
+-------------------------------------------------------------------------------+
|                                CLIENT BROWSER                                 |
|   +-------------------+  +--------------------+  +------------------------+   |
|   |  3D Particle HUD  |  | 3D Holographic     |  | Glassmorphic           |   |
|   |  Canvas (Starfield|  | Orbit Model (CSS3) |  | Interactive Dashboard  |   |
|   +-------------------+  +--------------------+  +------------------------+   |
|   +-------------------+  +--------------------+  +------------------------+   |
|   | Overview & Trends |  | Profile Analysis   |  | Live Jobs & ATS Lab    |   |
|   +-------------------+  +--------------------+  +------------------------+   |
+---------------------------------------^---------------------------------------+
                                        | (HTTPS / Encrypted Session Cookie)
+---------------------------------------v---------------------------------------+
|                            FASTAPI BACKEND GATEWAY                            |
|  [Starlette Session Middleware] <---> [CORS & Auth Guards]                    |
|  [Static Files Handler: /login.html, /index.html, /style.css, /app.js]        |
+------------------+--------------------+-------------------+-------------------+
                   |                    |                   |
                   v                    v                   v
+------------------+---+  +-------------+-----+  +----------+-------------------+
| AUTHENTICATION LAYER |  | INTELLIGENCE      |  | LIVE PROVIDER INTEGRATOR     |
| - Google OAuth 2.0   |  | ENGINE            |  | - Adzuna API (Primary)       |
| - OIDC OpenID Connect|  | - 30+ Role Schema |  | - The Muse API (Fallback)    |
| - Dev Session Bypass |  | - Skill Gap Matrix|  | - Skill Match & Salary Parser|
+----------------------+  | - 7-Week Sprint   |  +------------------------------+
                          | - ATS In-Memory   |
                          +-------------+-----+
                                        |
+---------------------------------------v---------------------------------------+
|                            SQLITE PERSISTENCE LAYER                           |
|   - database.db (Assessment History, Verified Company Eligibility Registry)   |
+-------------------------------------------------------------------------------+
```

---

## 3. Technology Stack

### Backend Core
- **Framework**: FastAPI `0.111.0+` (High-performance Python 3.12+ async ASGI framework)
- **Server**: Uvicorn `0.30.0+` with standard event loop workers (`uvloop`, `httptools`)
- **Session & Auth**: `authlib 1.3.0+`, `itsdangerous 2.2.0+`, Starlette `SessionMiddleware`
- **Validation**: Pydantic `2.7.0+` V2 with strict type models
- **PDF Extraction**: `pypdf 4.2.0+` for in-memory stream decoding
- **HTTP Client**: `httpx 0.28.0+` for async REST API requests

### Frontend Architecture
- **Language**: Vanilla ECMAScript 2026+ (No bulky framework dependencies; zero build step required)
- **Styling**: Pure CSS3 with modern custom properties, CSS Grid, Flexbox, 3D Transforms (`perspective`, `rotateX`, `rotateZ`, `preserve-3d`)
- **Typography**: Google Fonts CDN (`Outfit`, `Plus Jakarta Sans`, `JetBrains Mono`)
- **Visuals**: HTML5 `<canvas>` 2D particle simulation, SVG radial gauges, CSS frosted glassmorphism

### Database & Storage
- **Engine**: SQLite 3 with WAL (Write-Ahead Logging) mode and connection timeouts
- **Seeding**: Automated startup migration with verified criteria for Fortune 500 & Top IT Employers

---

## 4. Visual System & Aesthetics (Black 3D Cyber Engine)

The user interface implements a **Black 3D Cyber Theme** designed to provide a rich visual experience:

| Component | Technical Implementation | Purpose |
| :--- | :--- | :--- |
| **Deep Space Particle Canvas** | JavaScript requestAnimationFrame physics loop drawing floating vector particles with neon lime glow (`#c8ff00`). | Immersive, fluid ambient background without degrading CPU performance. |
| **3D Holographic Orbit** | CSS3 3D transformed coordinate space (`perspective: 800px; rotateX(62deg); rotateZ(-22deg)`) with counter-rotating orbital rings and glowing satellites. | Visualizes foundational, advanced, and emerging IT competencies orbiting core readiness. |
| **Glassmorphic HUD Surfaces** | `background: rgba(13, 17, 25, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08);` | High-contrast readability with depth perception and neon accents. |
| **Radial SVG Progress Gauges** | Dynamic SVG `stroke-dasharray` and `stroke-dashoffset` calculated via $C = 2\pi r$. | Visualizes readiness scores and ATS strength percentages. |
| **Parallax 3D Tilt** | Viewport-aware mousemove event listener applying real-time 3D rotation (`rotateX`, `rotateY`) on cards. | Interactive tactile feedback on desktop displays. |

---

## 5. Core Modules & Feature Breakdown

### 5.1. Authentication & Session Security

JobFit employs a hybrid authentication model:

1. **Google Identity Services (OIDC / OAuth 2.0)**:
   - Endpoint: `/auth/login` redirects user to Google's OpenID Connect server.
   - Endpoint: `/auth/callback` handles the authorization code exchange, extracts name, email, and profile avatar, and stores an encrypted session cookie (`session`).
   - Strict state verification prevents CSRF attacks during auth flow.
2. **Local Development Session (`ENABLE_DEV_LOGIN=true`)**:
   - Allows instant one-click login in local test environments without requiring active Google Cloud Console credentials.
   - Automatically disabled in production when `ENABLE_DEV_LOGIN=false`.
3. **Session Guards**:
   - All `/api/*` endpoints (except `/api/health` and `/api/auth/config`) validate user existence in the encrypted session before processing requests, returning HTTP 401 with redirect signals if unauthorized.

---

### 5.2. Evidence-Based Career Intelligence Engine (`backend/career_engine.py`)

#### 30+ IT Role Taxonomy & Open-Ended Matching
The engine includes comprehensive skill profiles for over 30 roles across domains:
- **Web & Full-Stack**: Full Stack Developer, Frontend Developer, Backend Developer.
- **AI & Data Intelligence**: AI Engineer, Machine Learning Engineer, Data Scientist, Data Engineer, NLP Specialist.
- **Cloud, Platform & Infrastructure**: DevOps Engineer, Cloud Architect, Site Reliability Engineer (SRE), Platform Engineer.
- **Security & Systems**: Cybersecurity Analyst, Penetration Tester, Embedded Systems Engineer, Blockchain Developer.
- **Enterprise & Management**: Product Manager, Technical Architect, Business Analyst, QA Automation Engineer.
- **Custom / Open-Ended Titles**: Fuzzy keyword extraction analyzes non-standard job titles and derives requirements.

#### Mathematical Readiness Formula
The readiness score $R \in [0, 100]$ is computed via weighted scoring:

$$R = 0.20 \cdot S_{\text{academics}} + 0.35 \cdot S_{\text{technical}} + 0.25 \cdot S_{\text{experience}} + 0.20 \cdot S_{\text{interview}}$$

Where:
- $S_{\text{academics}}$: Evaluates CGPA ($\ge 8.5 \rightarrow 100\%$, $\ge 7.5 \rightarrow 85\%$, $\ge 6.5 \rightarrow 70\%$), backlogs (penalized per active backlog), and degree relevance.
- $S_{\text{technical}}$: Measured as $\frac{|\text{User Skills} \cap \text{Role Skills}|}{|\text{Role Skills}|}$ with bonus multipliers for industry-recognized certifications.
- $S_{\text{experience}}$: Scaled based on practical project counts (capped at 4) and completed internships (capped at 2).
- $S_{\text{interview}}$: Normalized average of aptitude assessments and technical interview scores.

#### Output Artifacts
- **7-Week Sprint Roadmap**: Milestone schedule covering Foundational Skills, Core Architecture, Portfolio Project Build, System Design, Testing & Security, and Live Interview Sprints.
- **Skill Gap Matrix**: Highlights matched skills (`✓ MATCH`), critical missing skills (`★ PRIORITY GAP`), and emerging technologies.
- **Tailored Project Proposals**: Concrete full-stack/AI project proposals to bridge resume gaps.
- **Interview Question Bank**: Role-specific technical, architectural, and behavioral prompts.

---

### 5.3. Multi-Provider Live Job Search (`backend/live_data.py`)

```
               [ User Job Search Request ]
                           |
                           v
              [ Is Adzuna Configured? ]
                    /             \
             (YES) /               \ (NO)
                  v                 v
          [ Query Adzuna API ]   [ Query The Muse API ]
                  |                      |
            (Has Results?)         (Has Results?)
             /          \           /          \
       (YES)/      (NO)  \    (YES)/      (NO)  \
           v              v       v              v
     [ Return Jobs ]  [ Curated Live Intelligence Stream ]
```

- **Adzuna API Integration**: Fetches up to 50 listings per request with structured salary metadata, locations, and direct application links.
- **The Muse API Fallback**: Provides live opportunities when Adzuna credentials are not set.
- **Skill Extraction & Match Meter**: Inspects job descriptions using regex word boundaries against 120+ technical keywords and computes match percentages.
- **Seniority Normalization**: Standardizes job levels into `Fresher / Entry`, `Mid-Level`, or `Senior`.

---

### 5.4. In-Memory Résumé ATS Diagnostic Lab

- **Privacy Architecture**: Uploaded PDF and TXT files are processed entirely in volatile RAM (`io.BytesIO`). Files are immediately garbage-collected and never written to disk.
- **ATS 6-Point Health Checklist**:
  1. Contact Information (Email, Phone, Location, LinkedIn/GitHub)
  2. Education & Degree Details
  3. Work Experience & Internships
  4. Technical Projects & Repositories
  5. Technical Skills Matrix
  6. Certifications & Credentials
- **Keyword Gap Detection**: Cross-references detected skills in the résumé against the target role taxonomy and highlights missing keywords.

---

### 5.5. Verified Employer Eligibility Registry (`backend/database.py`)

JobFit maintains an authenticated company eligibility registry with pre-seeded data for major employers:
- **Google, Microsoft, Amazon, TCS, Infosys, Accenture, Deloitte, Cisco, IBM, AWS, Palo Alto Networks**.
- **Source Verification**: All criteria entries include a verified `source_url` pointing to official careers portals.
- **Admin Management**: Protected via `X-Admin-Key` header matching `ADMIN_API_KEY`.

---

## 6. API Specification & Data Contracts

### 6.1. Authentication Endpoints

#### `GET /api/auth/config`
Returns OAuth status and provider capabilities.
```json
{
  "google_enabled": true,
  "development_login_enabled": false,
  "providers": {
    "adzuna_configured": true,
    "muse_configured": false,
    "live_provider": "Adzuna"
  }
}
```

#### `GET /api/auth/me`
Returns current authenticated user details.
```json
{
  "user": {
    "name": "Anish Ankareddy",
    "email": "anish@example.com",
    "picture": "https://lh3.googleusercontent.com/..."
  }
}
```

#### `POST /auth/dev-login`
Sets a development session (only when `ENABLE_DEV_LOGIN=true`).

#### `POST /auth/logout`
Clears session cookie and logs out.

---

### 6.2. Career Intelligence Endpoints

#### `GET /api/role-suggestions`
Returns standard role taxonomy suggestions for search autocomplete.

#### `POST /api/career/analyze`
**Request Body:**
```json
{
  "name": "Candidate Name",
  "degree": "B.Tech",
  "branch": "CSE",
  "graduation_year": 2026,
  "cgpa": 8.65,
  "backlogs": 0,
  "technical_skills": ["Python", "JavaScript", "React", "Docker", "AWS", "SQL"],
  "soft_skills": ["Problem Solving", "Collaboration"],
  "certifications": ["AWS Certified Cloud Practitioner"],
  "projects": 3,
  "internships": 1,
  "aptitude_score": 80,
  "interview_score": 75,
  "target_role": "Full Stack Developer"
}
```

**Response (Summary):**
```json
{
  "id": 1,
  "created_at": "2026-08-26T18:00:00Z",
  "profile": { ... },
  "analysis": {
    "readiness_score": 78,
    "readiness_label": "High Readiness (Profile Aligned)",
    "score_breakdown": {
      "academics": 90,
      "technical_skills": 75,
      "experience": 80,
      "interview": 77
    },
    "skill_gap": {
      "matched": ["Python", "JavaScript", "React", "Docker", "AWS", "SQL"],
      "missing": ["TypeScript", "Node.js", "Redis"],
      "priority": ["Node.js", "TypeScript"]
    },
    "roadmap": [
      {
        "period": "Week 1-2",
        "topic": "Core Backend & Asynchronous Architecture",
        "action": "Master Node.js event loop and TypeScript interfaces."
      }
    ],
    "interview_prep": [ ... ],
    "project_ideas": [ ... ],
    "eligibility": [ ... ],
    "recommended_jobs": [ ... ]
  }
}
```

#### `GET /api/career/history`
Returns past analysis history for the current session.

---

### 6.3. Live Opportunities Endpoints

#### `GET /api/jobs?query=Full+Stack+Developer&location=Bengaluru&country=in&page=1&level=Fresher`
Returns real-time job listings matching search criteria.

#### `GET /api/market-signals?query=AI+Engineer&country=in`
Returns aggregated live industry skill demand frequencies.

---

### 6.4. Résumé Lab Endpoints

#### `POST /api/resume/analyze`
Accepts `multipart/form-data` with:
- `file`: PDF or TXT file bytes.
- `target_role`: Target job title string.

#### `POST /api/resume/analyze-text`
Accepts JSON payload with raw resume text for headless/API testing.

---

### 6.5. Employer Criteria Endpoints

#### `GET /api/company-requirements?role=Software+Developer`
Returns verified employer requirements matching the specified role.

#### `POST /api/company-requirements`
*(Requires `X-Admin-Key: <ADMIN_API_KEY>` header)*
Inserts or updates verified company criteria.

---

## 7. Database Schema & Persistence Layer

The SQLite database (`database.db`) uses two primary tables:

### Table: `assessment_history`
```sql
CREATE TABLE IF NOT EXISTS assessment_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    target_role TEXT NOT NULL,
    readiness_score INTEGER NOT NULL,
    readiness_label TEXT NOT NULL,
    profile_payload TEXT NOT NULL,
    analysis_payload TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_assessment_email ON assessment_history(user_email);
```

### Table: `company_requirements`
```sql
CREATE TABLE IF NOT EXISTS company_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    min_cgpa REAL NOT NULL,
    max_backlogs INTEGER NOT NULL,
    required_skills TEXT NOT NULL,
    source_url TEXT NOT NULL,
    verified_by TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company, role)
);
CREATE INDEX IF NOT EXISTS idx_req_role ON company_requirements(role);
```

---

## 8. Configuration & Environment Variables

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SESSION_SECRET_KEY` | String | Random token | Key for encrypted session cookies. |
| `COOKIE_SECURE` | Boolean | `false` | Set to `true` in production to enforce HTTPS cookies. |
| `ENABLE_DEV_LOGIN` | Boolean | `false` | Set to `true` for local 1-click test session bypass. |
| `GOOGLE_CLIENT_ID` | String | `""` | Google Cloud Console OAuth 2.0 Web Client ID. |
| `GOOGLE_CLIENT_SECRET` | String | `""` | Google Cloud Console OAuth 2.0 Web Client Secret. |
| `ADZUNA_APP_ID` | String | `""` | Adzuna Developer Application ID. |
| `ADZUNA_APP_KEY` | String | `""` | Adzuna Developer Application API Key. |
| `MUSE_API_KEY` | String | `""` | Optional API key for The Muse fallback. |
| `DATABASE_PATH` | String | `./database.db` | Absolute or relative path to SQLite database. |
| `ADMIN_API_KEY` | String | `jobfit-admin-secret` | Key for authenticating criteria updates. |

---

## 9. Local Development & Testing Guide

### 1. Prerequisites
- Python 3.12 or 3.13 installed
- Git installed
- Google Chrome or modern browser

### 2. Quick Setup Commands (PowerShell)
```powershell
# Navigate to project directory
cd "D:\python project"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create .env configuration
Copy-Item .env.example .env

# Launch application server
python -m uvicorn backend.main:app --port 8000 --reload
```

### 3. Verification & Automated Test Suite
To verify all API endpoints and models:
```powershell
python -c "
from fastapi.testclient import TestClient
from backend.main import app

with TestClient(app) as client:
    r = client.get('/api/health')
    assert r.status_code == 200
    print('Health Check: PASSED')
    
    r = client.post('/auth/dev-login')
    assert r.status_code == 200
    print('Development Session Auth: PASSED')
    
    r = client.get('/api/role-suggestions')
    assert len(r.json()['data']) > 0
    print('Role Taxonomy: PASSED')
"
```

---

## 10. Production Cloud Deployment Guide

### Deployment Option A: Render (via Blueprint)

1. Push your repository to GitHub (`main` branch).
2. Log into [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** → **Blueprint** → Select your repository `jobfit`.
4. Render detects `render.yaml` and `Dockerfile` automatically.
5. In the **Environment** settings, configure production keys:
   - `SESSION_SECRET_KEY` = *(random 32-character string)*
   - `COOKIE_SECURE` = `true`
   - `ENABLE_DEV_LOGIN` = `false`
   - `GOOGLE_CLIENT_ID` = `your-id.apps.googleusercontent.com`
   - `GOOGLE_CLIENT_SECRET` = `your-secret`
   - `ADZUNA_APP_ID` = `your-adzuna-id`
   - `ADZUNA_APP_KEY` = `your-adzuna-key`
6. In **Google Cloud Console**, register your live redirect URI:
   `https://<your-render-app>.onrender.com/auth/callback`

### Deployment Option B: Docker Container

```bash
# Build production Docker image
docker build -t jobfit:latest .

# Run container with mounted persistent volume for SQLite
docker run -d \
  -p 8000:8000 \
  -v jobfit_data:/data \
  -e SESSION_SECRET_KEY="your-production-secret" \
  -e COOKIE_SECURE="true" \
  -e DATABASE_PATH="/data/database.db" \
  --name jobfit-app \
  jobfit:latest
```

---

## 11. Security, Privacy, and Ethical AI Principles

1. **Zero Resume Persistence**: Résumé files uploaded to the Résumé Lab are processed in memory and never written to disk or third-party storage.
2. **Transparent Mathematical Scoring**: Readiness scores are calculated from explicit, documented criteria rather than opaque black-box machine learning estimates.
3. **No Unsubstantiated Decisions**: JobFit explicitly identifies itself as a career preparation tool and provides disclaimers stating that it does not make admission or employment decisions.
4. **Verified Employer Criteria**: Criteria for companies appear only when backed by an authenticated source URL to prevent misinformation.

---

*JobFit — Engineering Career Intelligence for the Next Generation.*
