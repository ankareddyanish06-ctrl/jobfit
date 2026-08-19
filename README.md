# JobFit — Live IT Career Intelligence Platform

JobFit is a full-stack FastAPI application for students and professionals exploring IT careers. It uses authenticated sessions, live job providers, open-ended role searching, profile evidence analysis, résumé analysis, and a verified employer-criteria registry.

## Features now implemented

- **Google sign-in**: secure OAuth/OIDC login with a server-side session
- **Separate experiences**: Overview, Profile Analysis, Live Opportunities, Résumé Lab, and Developer sections
- **Black 3D visual system**: animated orbits, gradients, floating forms, and mobile-responsive design built with CSS
- **Adzuna-first live job search**: searches any IT job title across fresher, mid-level, and senior opportunities
- **The Muse fallback**: keeps live job search available during development if Adzuna credentials are not set
- **Open-ended IT roles**: search and analyze titles such as Platform Engineer, AI Engineer, SAP Consultant, Security Analyst, Senior Architect, and more
- **Evidence-based profile analysis**: skill matching, gaps, roadmap, interview prompts, and no fake placement probability
- **PDF/TXT résumé analysis**: files are processed in memory and are not stored
- **Verified company eligibility**: company criteria appear only after an authenticated administrator adds an official source link
- **Developer section**: edit the `Your Name` and GitHub link in `frontend/index.html` before publishing

> JobFit is a career-planning tool. It does not make hiring, admission, or salary decisions.

## Project files

| File | What it controls |
|---|---|
| `backend/main.py` | FastAPI routes, Google OAuth, protected APIs |
| `backend/live_data.py` | Adzuna-first / The Muse fallback live providers |
| `backend/career_engine.py` | Open-ended IT-role and skill-gap analysis |
| `backend/database.py` | Assessment history and verified employer criteria |
| `frontend/login.html` + `login.js` | Google sign-in page |
| `frontend/index.html` | Separate application views and developer profile |
| `frontend/style.css` | Black 3D-inspired animated design |
| `frontend/app.js` | Client behavior, live searching, analysis and upload |
| `.env.example` | All required environment variable names |

## Run in VS Code

```powershell
cd "D:\python project"
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload --env-file .env
```

Open `http://127.0.0.1:8000`.

For a local visual check before configuring Google, add this temporary value to `.env`:

```text
ENABLE_DEV_LOGIN=true
```

Use **Use local development session** on the sign-in page. Set it back to `false` or remove it before deployment.

## Activate Adzuna live search

1. Register at [Adzuna Developer](https://developer.adzuna.com/overview).
2. Create an application to receive an **App ID** and **App Key**.
3. Copy `.env.example` to `.env` and add:

```text
ADZUNA_APP_ID=your-adzuna-app-id
ADZUNA_APP_KEY=your-adzuna-app-key
```

4. Restart Uvicorn.

Job search will then show **Adzuna** as its provider and can return up to 50 results per page. Without these values, JobFit intentionally falls back to The Muse instead of inventing opportunities. Adzuna’s API requires an app ID and app key for requests. [Adzuna API overview](https://developer.adzuna.com/overview)

## Activate Google authentication

1. In [Google Cloud Console](https://console.cloud.google.com/), create or select a project.
2. Configure the OAuth consent screen.
3. Create an **OAuth client ID** with application type **Web application**.
4. Add these Authorized redirect URIs exactly:

```text
http://127.0.0.1:8000/auth/google/callback
https://YOUR-RENDER-URL.onrender.com/auth/google/callback
```

5. Add the generated credentials to `.env`:

```text
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SESSION_SECRET=use-a-long-random-secret-here
COOKIE_SECURE=false
```

For Render, set `COOKIE_SECURE=true` in its Environment settings. Google requires the callback URL to exactly match one of the redirect URIs configured for the OAuth client; localhost is allowed for development, while deployed apps should use HTTPS. [Google OpenID Connect setup](https://developers.google.com/identity/openid-connect/openid-connect), [redirect-URI rules](https://developers.google.com/identity/protocols/oauth2/web-server)

Never upload `.env`, Google client secrets, Adzuna keys, or `SESSION_SECRET` to GitHub.

## Add verified company eligibility criteria

Set a separate `ADMIN_API_KEY` in `.env`, then use the API documentation at `http://127.0.0.1:8000/docs`. Only enter criteria after verifying the official employer careers page, campus notice, or other authoritative source. The API requires a `source_url` so users can inspect the rule themselves.

## Deploy to Render

1. Push the project to GitHub using the commands below.
2. In Render, select **New → Blueprint** and choose the repository.
3. Render reads `render.yaml` and `Dockerfile`.
4. In the Render service’s **Environment** panel, add:

```text
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
SESSION_SECRET
COOKIE_SECURE=true
ADZUNA_APP_ID
ADZUNA_APP_KEY
ADMIN_API_KEY
```

5. In Google Cloud Console, add the final `https://YOUR-RENDER-URL.onrender.com/auth/google/callback` URI.

## Update GitHub from VS Code

First confirm no secret file is staged:

```powershell
git status
```

Then publish the completed update:

```powershell
cd "D:\python project"
git add .
git commit -m "Add OAuth, Adzuna live search, and 3D multi-view UI"
git push
```

If this project is not yet connected to GitHub:

```powershell
git remote add origin https://github.com/YOUR-USERNAME/jobfit-live-career-platform.git
git branch -M main
git push -u origin main
```

After every later change:

```powershell
git add .
git commit -m "Describe your update"
git push
```

Render redeploys the connected repository automatically.

## Production work still recommended

Before collecting real student data, add a PostgreSQL database, user-to-record ownership, consent/privacy policy, rate limiting, audit logging, password-free session controls, and provider-terms compliance. Do not train an employment prediction model unless you have a lawful, consented, representative dataset and evaluated fairness/impact.
