# JobFit — Placement Readiness Analyzer

JobFit is a resume-ready, full-stack Python application that estimates placement readiness and highlights skills to prioritize. The single FastAPI service serves both the responsive browser interface and the REST API.

> **Important:** Predictions are educational estimates generated from a synthetic training dataset. The app must not be used to make hiring, admission, or other high-impact decisions.

## Features

- Responsive, accessible UI that works across phones, tablets, and desktop browsers
- FastAPI REST API with validated inputs and clear error responses
- Automatic machine-learning model creation on a first deployment
- Deterministic skill scoring, matching, and gap recommendations
- SQLite persistence for the five most recent assessments
- Health endpoint for hosting platforms: `GET /api/health`
- Docker configuration and a Render Blueprint for production deployment
- No frontend framework, third-party JavaScript, or external font/CDN dependency

## Project layout

```text
backend/
  main.py          # FastAPI routes and request validation
  ml_model.py      # Placement predictor and skill analyzer
  train_model.py   # Synthetic-data ML training script
  database.py      # SQLite storage
frontend/
  index.html       # Accessible responsive page
  style.css        # Mobile-first visual design
  app.js           # Browser API integration
Dockerfile          # Deployment image
render.yaml         # One-click Render service blueprint
```

## Run locally (development only)

Prerequisite: Python 3.10 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`. The model is generated automatically at first startup. API documentation is available at `http://127.0.0.1:8000/docs`.

## Deploy it publicly (recommended)

A browser application always needs a server somewhere; this repository is set up so the server is a cloud host, not your computer.

### Render using the included blueprint

1. Create a GitHub repository and push this project.
2. In Render, choose **New → Blueprint** and select the repository.
3. Render reads `render.yaml`, builds the Docker image, attaches persistent storage, and deploys it.
4. Use the generated HTTPS `onrender.com` address on your résumé or LinkedIn project section.

The persistent disk matters: without it, free/ephemeral hosts can erase the SQLite history after a restart.

### Any Docker-capable host

```bash
docker build -t jobfit .
docker run -p 8000:8000 -e PORT=8000 -v jobfit-data:/data jobfit
```

For production, route your domain to port 8000 through the platform's HTTPS proxy. To serve a separately hosted frontend, set `ALLOWED_ORIGINS` to its comma-separated HTTPS origins (for example `https://your-site.example`).

## API example

```bash
curl -X POST https://YOUR-DOMAIN/api/predict \
  -H "Content-Type: application/json" \
  -d '{"cgpa":8.4,"internships":2,"projects":4,"skills":["Python","SQL","Git","Docker"]}'
```

## Suggested LinkedIn project description

> Built JobFit, a full-stack placement-readiness platform using FastAPI, scikit-learn, SQLite, and responsive vanilla JavaScript. Implemented validated REST APIs, an ML prediction pipeline, deterministic skill-gap recommendations, persistent assessment history, and Docker-based cloud deployment.
