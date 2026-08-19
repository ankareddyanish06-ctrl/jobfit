"""Live job, labour-market, and salary data adapters with short-lived caching."""
from __future__ import annotations
import asyncio, json, os, re
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_SECONDS = 600
SKILLS = {"python", "sql", "excel", "power bi", "tableau", "statistics", "data analysis", "java", "javascript", "react", "node.js", "git", "rest api", "docker", "linux", "aws", "azure", "kubernetes", "servicenow", "html", "css", "networking", "data structures"}
ROLE_CATEGORIES = {"data-analyst": "Data and Analytics", "software-developer": "Software Engineering", "servicenow-developer": "IT", "web-developer": "Software Engineering", "cloud-engineer": "IT"}


def _fetch_json(url: str) -> dict:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "JobFit/2.0"})
    with urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


async def _cached(key: str, url: str) -> dict:
    now = asyncio.get_running_loop().time()
    cached = _CACHE.get(key)
    if cached and now - cached[0] < _CACHE_SECONDS:
        return cached[1]
    data = await asyncio.to_thread(_fetch_json, url)
    _CACHE[key] = (now, data)
    return data


def _skills_from_text(text: str) -> list[str]:
    normalized = text.lower().replace("nodejs", "node.js")
    return sorted(skill for skill in SKILLS if skill in normalized)


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


async def live_jobs(role: str | None = None, location: str | None = None, query: str | None = None, skills: set[str] | None = None) -> dict:
    params = {"page": 1, "descending": "true"}
    if role and ROLE_CATEGORIES.get(role): params["category"] = ROLE_CATEGORIES[role]
    if location: params["location"] = location
    api_key = os.getenv("MUSE_API_KEY")
    if api_key: params["api_key"] = api_key
    url = f"https://www.themuse.com/api/public/jobs?{urlencode(params)}"
    try:
        raw = await _cached(url, url)
    except Exception as exc:
        return {"source": "The Muse", "live": False, "error": "The live job provider is temporarily unavailable.", "jobs": [], "updated_at": None}
    jobs = []
    for item in raw.get("results", raw.get("items", [])):
        title = item.get("name", "Untitled role")
        company = item.get("company", {}).get("name", "Unknown company")
        description = _strip_html(item.get("contents", ""))
        searchable = f"{title} {company} {description}".lower()
        if query and query.lower() not in searchable: continue
        found_skills = _skills_from_text(searchable)
        match = round(len(set(found_skills) & (skills or set())) / max(1, len(found_skills)) * 100) if skills else None
        jobs.append({"id": f"muse-{item.get('id')}", "title": title, "company": company, "location": ", ".join(place.get("name", "") for place in item.get("locations", [])) or "Not specified", "published_at": item.get("publication_date"), "url": item.get("refs", {}).get("landing_page"), "skills": found_skills, "match_percentage": match, "missing_skills": sorted(set(found_skills) - (skills or set())), "type": ", ".join(level.get("name", "") for level in item.get("levels", [])) or "Not specified"})
    return {"source": "The Muse", "source_url": "https://www.themuse.com/developers/api/v2", "live": True, "updated_at": datetime.now(timezone.utc).isoformat(), "jobs": jobs, "total_pages": raw.get("page_count")}


async def live_market() -> dict:
    batches = await asyncio.gather(*(live_jobs(role=role) for role in ROLE_CATEGORIES), return_exceptions=True)
    jobs = [job for batch in batches if isinstance(batch, dict) for job in batch.get("jobs", [])]
    counts: dict[str, int] = {}
    for job in jobs:
        for skill in job["skills"]: counts[skill] = counts.get(skill, 0) + 1
    return {"source": "The Muse", "source_url": "https://www.themuse.com/developers/api/v2", "live": bool(jobs), "updated_at": datetime.now(timezone.utc).isoformat(), "jobs_sampled": len(jobs), "top_skills": [{"skill": skill, "openings": count} for skill, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:8]], "locations": sorted({job["location"] for job in jobs})[:8]}


async def live_salary(role_title: str) -> dict:
    app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return {"available": False, "reason": "Add ADZUNA_APP_ID and ADZUNA_APP_KEY to enable live salary ranges.", "source": "Adzuna"}
    params = urlencode({"app_id": app_id, "app_key": app_key, "what": role_title, "results_per_page": 20})
    try:
        data = await _cached(f"salary:{role_title}", f"https://api.adzuna.com/v1/api/jobs/in/search/1?{params}")
        salaries = [(item.get("salary_min"), item.get("salary_max")) for item in data.get("results", []) if item.get("salary_min") and item.get("salary_max")]
        if not salaries: raise ValueError("No current salary data")
        return {"available": True, "minimum": round(sum(pair[0] for pair in salaries) / len(salaries)), "maximum": round(sum(pair[1] for pair in salaries) / len(salaries)), "source": "Adzuna", "source_url": "https://developer.adzuna.com/overview"}
    except Exception:
        return {"available": False, "reason": "The salary provider returned no current range for this role.", "source": "Adzuna"}
