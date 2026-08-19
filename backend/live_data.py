"""Live job-provider integrations with Adzuna as the primary source."""
from __future__ import annotations

import asyncio
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_SECONDS = 300
SKILLS = {"python", "java", "javascript", "typescript", "react", "angular", "vue", "node.js", "sql", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes", "aws", "azure", "gcp", "linux", "git", "rest api", "graphql", "microservices", "django", "flask", "fastapi", "spring", "dotnet", "html", "css", "cybersecurity", "networking", "devops", "machine learning", "data analysis", "power bi", "tableau", "excel", "salesforce", "servicenow", "sap", "data structures", "testing", "ci/cd"}
ALIASES = {"node": "node.js", "nodejs": "node.js", "rest": "rest api", "powerbi": "power bi", "ml": "machine learning", "cicd": "ci/cd", "c#": "dotnet"}


def _fetch_json(url: str) -> dict:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "JobFit/3.0"})
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


async def _cached(key: str, url: str) -> dict:
    loop = asyncio.get_running_loop()
    now = loop.time()
    cached = _CACHE.get(key)
    if cached and now - cached[0] < _CACHE_SECONDS:
        return cached[1]
    result = await asyncio.to_thread(_fetch_json, url)
    _CACHE[key] = (now, result)
    return result


def normalize_skills(skills: list[str]) -> set[str]:
    return {ALIASES.get(item.strip().lower(), item.strip().lower()) for item in skills if item.strip()}


def extract_skills(text: str) -> list[str]:
    normalized = text.lower().replace("nodejs", "node.js").replace("powerbi", "power bi")
    return sorted(skill for skill in SKILLS if skill in normalized)


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def seniority(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    if any(word in text for word in ("intern", "graduate", "fresher", "entry level", "junior", "trainee")):
        return "Fresher / Entry"
    if any(word in text for word in ("senior", "lead", "principal", "architect", "manager", "director")):
        return "Senior+"
    return "Mid-level"


def provider_status() -> dict:
    return {"adzuna_configured": bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY")), "muse_configured": bool(os.getenv("MUSE_API_KEY"))}


async def _adzuna_jobs(query: str, location: str | None, country: str, page: int) -> dict:
    app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        raise RuntimeError("Adzuna credentials are not configured.")
    params = {"app_id": app_id, "app_key": app_key, "what": query, "results_per_page": 50, "content-type": "application/json"}
    if location:
        params["where"] = location
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}?{urlencode(params)}"
    raw = await _cached(f"adzuna:{country}:{page}:{query}:{location or ''}", url)
    jobs = []
    for item in raw.get("results", []):
        title = item.get("title", "Untitled role")
        description = strip_html(item.get("description", ""))
        found_skills = extract_skills(f"{title} {description}")
        jobs.append({"id": f"adzuna-{item.get('id')}", "title": title, "company": item.get("company", {}).get("display_name", "Not specified"), "location": item.get("location", {}).get("display_name", "Not specified"), "published_at": item.get("created"), "url": item.get("redirect_url"), "skills": found_skills, "seniority": seniority(title, description), "salary_min": item.get("salary_min"), "salary_max": item.get("salary_max"), "description": description[:320]})
    return {"provider": "Adzuna", "provider_url": "https://developer.adzuna.com/overview", "live": True, "updated_at": datetime.now(timezone.utc).isoformat(), "jobs": jobs, "total_results": raw.get("count"), "page": page, "page_size": 50}


async def _muse_jobs(query: str, location: str | None, page: int) -> dict:
    params = {"page": page, "descending": "true"}
    if location:
        params["location"] = location
    if os.getenv("MUSE_API_KEY"):
        params["api_key"] = os.getenv("MUSE_API_KEY")
    url = f"https://www.themuse.com/api/public/jobs?{urlencode(params)}"
    raw = await _cached(f"muse:{page}:{location or ''}", url)
    jobs = []
    for item in raw.get("results", []):
        title = item.get("name", "Untitled role")
        description = strip_html(item.get("contents", ""))
        if query.lower() not in f"{title} {description}".lower():
            continue
        jobs.append({"id": f"muse-{item.get('id')}", "title": title, "company": item.get("company", {}).get("name", "Not specified"), "location": ", ".join(place.get("name", "") for place in item.get("locations", [])) or "Not specified", "published_at": item.get("publication_date"), "url": item.get("refs", {}).get("landing_page"), "skills": extract_skills(f"{title} {description}"), "seniority": seniority(title, description), "salary_min": None, "salary_max": None, "description": description[:320]})
    return {"provider": "The Muse", "provider_url": "https://www.themuse.com/developers/api/v2", "live": True, "updated_at": datetime.now(timezone.utc).isoformat(), "jobs": jobs, "total_results": raw.get("page_count"), "page": page, "page_size": 20}


async def live_jobs(query: str, location: str | None = None, country: str = "in", page: int = 1, level: str | None = None, user_skills: set[str] | None = None) -> dict:
    try:
        data = await _adzuna_jobs(query, location, country, page)
    except Exception:
        try:
            data = await _muse_jobs(query, location, page)
            data["notice"] = "Adzuna is not configured, so results are from The Muse. Add Adzuna credentials for broad live search."
        except Exception:
            return {"provider": "None", "live": False, "jobs": [], "error": "No live job provider is available. Check the network and provider credentials."}
    jobs = data["jobs"]
    if level:
        jobs = [job for job in jobs if job["seniority"] == level]
    for job in jobs:
        detected = set(job["skills"])
        job["match_percentage"] = round(len(detected & (user_skills or set())) / len(detected) * 100) if user_skills and detected else None
        job["missing_skills"] = sorted(detected - (user_skills or set()))[:8]
    data["jobs"] = jobs
    return data


async def market_signals(query: str, country: str = "in") -> dict:
    data = await live_jobs(query, country=country, page=1)
    counts = Counter(skill for job in data.get("jobs", []) for skill in job["skills"])
    return {"provider": data.get("provider"), "provider_url": data.get("provider_url"), "live": data.get("live", False), "updated_at": data.get("updated_at"), "jobs_sampled": len(data.get("jobs", [])), "top_skills": [{"skill": skill, "openings": count} for skill, count in counts.most_common(12)]}
