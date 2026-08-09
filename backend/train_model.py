"""Train the demonstration model used by the application."""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split


def create_mock_data(num_samples: int = 2_000) -> pd.DataFrame:
    generator = np.random.default_rng(42)
    cgpa = np.clip(generator.normal(7.5, 1.5, num_samples), 0, 10)
    internships = np.clip(generator.poisson(1.0, num_samples), 0, 5)
    projects = np.clip(generator.poisson(2.5, num_samples), 0, 10)
    skill_score = np.clip(generator.normal(60, 20, num_samples), 0, 100)
    probability = np.clip(
        10 + cgpa * 4 + internships * 5 + projects * 2 + skill_score * 0.2
        + generator.normal(0, 5, num_samples),
        0, 100,
    )
    return pd.DataFrame({
        "cgpa": cgpa, "internships": internships, "projects": projects,
        "skill_score": skill_score, "placement_prob": probability,
    })


def train_and_save_model(model_path: Path | None = None) -> float:
    data = create_mock_data()
    features = data[["cgpa", "internships", "projects", "skill_score"]]
    target = data["placement_prob"]
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )
    model = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42)
    model.fit(x_train, y_train)
    target_path = model_path or Path(__file__).resolve().parent / "model.pkl"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("wb") as model_file:
        pickle.dump(model, model_file)
    return float(model.score(x_test, y_test))


if __name__ == "__main__":
    score = train_and_save_model()
    print(f"Model trained successfully (R2: {score:.3f}).")
