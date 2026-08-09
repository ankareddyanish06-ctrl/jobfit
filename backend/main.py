"""FastAPI application for JobFit, a placement-readiness learning tool."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from backend.database import get_history, init_db, save_prediction
from backend.ml_model import PlacementPredictor

predictor = PlacementPredictor()
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="JobFit API",
    version="1.0.0",
    description="Placement-readiness prediction and skill-gap analysis API.",
    lifespan=lifespan,
)

allowed_origins = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "").split(",") if item.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )


class PredictionRequest(BaseModel):
    cgpa: float = Field(ge=0, le=10, description="Cumulative GPA out of 10")
    internships: int = Field(ge=0, le=20)
    projects: int = Field(ge=0, le=50)
    skills: list[str] = Field(min_length=1, max_length=30)

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, skills: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen = set()
        for skill in skills:
            name = skill.strip()
            key = name.lower()
            if name and len(name) <= 50 and key not in seen:
                cleaned.append(name)
                seen.add(key)
        if not cleaned:
            raise ValueError("Please provide at least one valid skill.")
        return cleaned


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "jobfit-api"}


@app.post("/api/predict")
async def predict_placement(request: PredictionRequest):
    try:
        skill_score, recommendations, matched_skills = predictor.calculate_skill_score(request.skills)
        prediction = predictor.predict_placement(
            request.cgpa, request.internships, request.projects, skill_score
        )
        record_id = save_prediction(
            request.cgpa, request.internships, request.projects, request.skills,
            skill_score, prediction,
        )
        return {
            "success": True,
            "id": record_id,
            "prediction_percentage": round(prediction, 1),
            "skill_score": skill_score,
            "matched_skills": matched_skills,
            "recommended_skills": recommendations,
            "disclaimer": "This is an educational readiness estimate trained on synthetic data, not a hiring decision.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to create the analysis.") from exc


@app.get("/api/history")
async def fetch_history(limit: int = Query(default=5, ge=1, le=20)):
    try:
        return {"success": True, "data": get_history(limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to load prediction history.") from exc


@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
