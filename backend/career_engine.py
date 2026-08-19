"""Explainable student analysis built from profile evidence and live job requirements."""
from __future__ import annotations
from collections import Counter
from backend.live_data import extract_skills, normalize_skills

KNOWN_ROLE_SKILLS = {
    "data analyst": ["python", "sql", "excel", "power bi", "tableau", "data analysis", "statistics"],
    "software developer": ["python", "java", "javascript", "sql", "git", "data structures", "rest api", "docker"],
    "web developer": ["html", "css", "javascript", "react", "node.js", "rest api", "git"],
    "cloud engineer": ["linux", "aws", "azure", "docker", "kubernetes", "python", "networking", "git"],
    "devops engineer": ["linux", "aws", "docker", "kubernetes", "ci/cd", "git", "python"],
    "cybersecurity analyst": ["cybersecurity", "linux", "networking", "python", "git"],
    "data engineer": ["python", "sql", "postgresql", "aws", "docker", "data analysis"],
    "qa engineer": ["testing", "python", "javascript", "rest api", "git"],
    "servicenow developer": ["javascript", "servicenow", "rest api", "sql", "html", "css", "git"],
}


def title_skill(skill: str) -> str:
    special = {"sql": "SQL", "aws": "AWS", "gcp": "GCP", "rest api": "REST API", "html": "HTML", "css": "CSS", "javascript": "JavaScript", "node.js": "Node.js", "power bi": "Power BI", "ci/cd": "CI/CD", "servicenow": "ServiceNow", "qa": "QA"}
    return special.get(skill, skill.title())


def suggested_roles() -> list[str]:
    return ["Software Developer", "Frontend Developer", "Backend Developer", "Full Stack Developer", "Data Analyst", "Data Engineer", "Machine Learning Engineer", "Cloud Engineer", "DevOps Engineer", "Cybersecurity Analyst", "QA Engineer", "Mobile Developer", "UI/UX Designer", "Database Administrator", "Network Engineer", "ServiceNow Developer", "Salesforce Developer", "SAP Consultant", "Business Analyst", "Product Manager"]


def required_skills(target_role: str, jobs: list[dict]) -> tuple[list[str], str]:
    canonical = target_role.strip().lower()
    for role, skills in KNOWN_ROLE_SKILLS.items():
        if role in canonical or canonical in role:
            return skills, "role framework"
    counts = Counter(skill for job in jobs for skill in job.get("skills", []))
    if counts:
        return [skill for skill, _ in counts.most_common(10)], "current live job listings"
    return ["python", "sql", "git", "rest api", "data structures"], "general IT baseline"


def eligibility(profile: dict, skills: set[str], requirements: list[dict]) -> list[dict]:
    results = []
    for company in requirements:
        issues = []
        if profile["cgpa"] < company["min_cgpa"]: issues.append(f"CGPA requires {company['min_cgpa']:.1f} or above")
        if profile["backlogs"] > company["max_backlogs"]: issues.append(f"Allows a maximum of {company['max_backlogs']} backlog(s)")
        if company["branches"] and profile["branch"] not in company["branches"]: issues.append("Branch is outside the verified list")
        if company["graduation_year"] and profile["graduation_year"] != company["graduation_year"]: issues.append(f"Listed batch is {company['graduation_year']}")
        missing = sorted(set(company["skills"]) - skills)
        status = "Eligible" if not issues and not missing else "Almost Eligible" if not issues else "Not Eligible"
        results.append({"company": company["company"], "status": status, "reasons": issues, "warnings": [f"Build: {', '.join(title_skill(skill) for skill in missing)}"] if missing else [], "required_skills": [title_skill(skill) for skill in company["skills"]], "source_url": company["source_url"], "verified_at": company["verified_at"]})
    return results


def analyze_profile(profile: dict, requirements: list[dict], jobs: list[dict]) -> dict:
    skills = normalize_skills(profile["technical_skills"])
    required, source = required_skills(profile["target_role"], jobs)
    required_set = set(required)
    matched, missing = sorted(skills & required_set), sorted(required_set - skills)
    academic, technical = round(profile["cgpa"] * 10), round(len(matched) / max(1, len(required_set)) * 100)
    experience, certifications = min(100, profile["projects"] * 14 + profile["internships"] * 24), min(100, len(profile["certifications"]) * 25)
    readiness = round(academic * .22 + technical * .38 + experience * .18 + certifications * .07 + profile["aptitude_score"] * .08 + profile["interview_score"] * .07)
    priorities = missing[:5]
    reasons = [f"Skills were compared against a {source}."]
    if matched: reasons.append(f"You match {len(matched)} currently relevant technical skill(s).")
    if profile["projects"] < 2: reasons.append("Add one more end-to-end project to strengthen portfolio evidence.")
    if priorities: reasons.append(f"Highest priority: {title_skill(priorities[0])}.")
    roadmap = [
        {"period": "Weeks 1–2", "topic": "Highest-priority skills", "action": f"Learn and practice {', '.join(title_skill(item) for item in priorities[:2]) or 'your role fundamentals'}."},
        {"period": "Weeks 3–4", "topic": "Portfolio project", "action": f"Build and publish a {profile['target_role']} project using the skills you learned."},
        {"period": "Weeks 5–6", "topic": "Production workflow", "action": "Add Git history, tests, clear documentation, and a deployed project link."},
        {"period": "Week 7", "topic": "Application preparation", "action": "Tailor your résumé to current listings and practice technical plus behavioural interviews."},
    ]
    interview = [f"Explain a {profile['target_role']} project you built from problem to deployment.", f"Which trade-off would you make when designing a {profile['target_role']} solution?", "Describe a bug or difficult problem and the steps you used to resolve it."]
    return {"role": {"title": profile["target_role"]}, "readiness_score": readiness, "readiness_label": "Strong" if readiness >= 75 else "Developing" if readiness >= 55 else "Foundation needed", "score_breakdown": {"academics": academic, "technical_skills": technical, "experience": experience, "certifications": certifications, "aptitude": profile["aptitude_score"], "interview": profile["interview_score"]}, "skill_gap": {"matched": [title_skill(item) for item in matched], "missing": [title_skill(item) for item in missing], "priority": [title_skill(item) for item in priorities], "source": source}, "eligibility": eligibility(profile, skills, requirements), "roadmap": roadmap, "next_action": f"Learn {title_skill(priorities[0]) if priorities else 'portfolio depth'} next because it is the most important remaining signal for {profile['target_role']} roles.", "reasons": reasons, "interview_prep": interview}


def analyze_resume(text: str, target_role: str) -> dict:
    detected = set(extract_skills(text))
    required, source = required_skills(target_role, [])
    matched, missing = sorted(detected & set(required)), sorted(set(required) - detected)[:5]
    lowered = text.lower(); sections = {name: name in lowered for name in ["education", "project", "skill", "experience", "certification"]}
    score = min(100, round(len(matched) / max(1, len(required)) * 65 + sum(sections.values()) * 7))
    suggestions = []
    if not sections["project"]: suggestions.append("Add a Projects section with your contribution, tools, and measurable outcome.")
    if not sections["skill"]: suggestions.append("Add a technical-skills section tailored to the chosen role.")
    if missing: suggestions.append(f"Add evidence for: {', '.join(title_skill(item) for item in missing)}.")
    return {"resume_strength": score, "detected_skills": [title_skill(item) for item in matched], "sections_found": sections, "suggestions": suggestions or ["Core sections are present; strengthen achievements with measurable outcomes."], "missing_role_skills": [title_skill(item) for item in missing], "comparison_source": source}
