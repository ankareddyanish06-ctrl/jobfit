"""Placement prediction and deterministic skill-gap analysis service."""

import pickle
from pathlib import Path


class PlacementPredictor:
    """Wrap the trained model and explainable skill analysis."""

    high_demand_skills = {
        "python", "javascript", "typescript", "react", "node.js", "sql", "nosql",
        "machine learning", "data analysis", "aws", "azure", "gcp", "docker",
        "kubernetes", "java", "c++", "go", "flask", "fastapi", "django", "html",
        "css", "git", "linux", "power bi", "tableau",
    }
    skill_aliases = {"node": "node.js", "nodejs": "node.js", "ml": "machine learning"}

    def __init__(self) -> None:
        self.model = None
        self.model_path = Path(__file__).resolve().parent / "model.pkl"
        self._load_or_create_model()

    def _load_or_create_model(self) -> None:
        try:
            with self.model_path.open("rb") as model_file:
                self.model = pickle.load(model_file)
        except (FileNotFoundError, EOFError, pickle.UnpicklingError):
            from backend.train_model import train_and_save_model
            train_and_save_model(self.model_path)
            with self.model_path.open("rb") as model_file:
                self.model = pickle.load(model_file)

    def calculate_skill_score(self, skills_list: list[str]) -> tuple[float, list[str], list[str]]:
        normalized = {
            self.skill_aliases.get(skill.strip().lower(), skill.strip().lower())
            for skill in skills_list
            if skill.strip()
        }
        matched = sorted(normalized & self.high_demand_skills)
        score = round(min((len(matched) / 8) * 100, 100), 2)
        recommendations = sorted(self.high_demand_skills - normalized)[:5]
        return score, recommendations, matched

    def predict_placement(
        self, cgpa: float, internships: int, projects: int, skill_score: float
    ) -> float:
        if self.model is None:
            self._load_or_create_model()
        prediction = self.model.predict([[cgpa, internships, projects, skill_score]])[0]
        return float(min(max(prediction, 0.0), 100.0))
