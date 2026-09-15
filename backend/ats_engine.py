"""ATS Readiness Check and Job-Specific Resume Optimization Engine."""
from __future__ import annotations

import re
from typing import Any

from backend.career_engine import KNOWN_ROLE_SKILLS, required_skills
from backend.live_data import extract_skills, normalize_skills, title_skill
from backend.resume_engine import normalize_resume_input

ACTION_VERBS = {
    "accelerated", "achieved", "analyzed", "architected", "automated", "built", "collaborated",
    "configured", "constructed", "created", "debugged", "delivered", "deployed", "designed",
    "developed", "devised", "documented", "engineered", "enhanced", "established", "executed",
    "formulated", "implemented", "improved", "increased", "initiated", "integrated", "launched",
    "led", "maintained", "managed", "maximized", "mentored", "minimized", "modeled", "monitored",
    "optimized", "orchestrated", "organized", "pioneered", "programmed", "published", "reduced",
    "refactored", "resolved", "restructured", "scaled", "simplified", "solved", "spearheaded",
    "standardized", "streamlined", "strengthened", "supervised", "tested", "trained", "troubleshot",
    "upgraded", "validated"
}

METRIC_PATTERNS = [
    re.compile(r"\b\d+%\b"),                     # e.g., 30%
    re.compile(r"\b\d+\s*ms\b", re.I),           # e.g., 120ms
    re.compile(r"\b\d+k\+?\b", re.I),            # e.g., 10k users
    re.compile(r"\b\d+\s*(?:users|clients|requests|queries|students)\b", re.I),
    re.compile(r"\$\d+(?:,\d{3})*(?:\.\d+)?"),   # e.g., $5,000
    re.compile(r"\b(?:reduced|increased|improved|scaled)\s+by\s+\d+", re.I),
]


def _flatten_resume_text(resume_doc: dict[str, Any]) -> str:
    """Convert a resume document or text into a searchable raw string."""
    if "raw_text" in resume_doc and resume_doc["raw_text"]:
        return resume_doc["raw_text"]

    parts = []
    info = resume_doc.get("personal_info", {})
    parts.extend([info.get("name", ""), info.get("email", ""), info.get("phone", ""), info.get("location", "")])
    parts.append(resume_doc.get("summary", ""))

    for edu in resume_doc.get("education", []):
        if isinstance(edu, dict):
            parts.extend([edu.get("degree", ""), edu.get("institution", ""), edu.get("year", ""), edu.get("score", "")])
        else:
            parts.append(str(edu))

    skills = resume_doc.get("skills", [])
    if isinstance(skills, dict):
        for sk_list in skills.values():
            parts.extend(sk_list if isinstance(sk_list, list) else [str(sk_list)])
    elif isinstance(skills, list):
        parts.extend(str(s) for s in skills)

    for exp in resume_doc.get("experience", []):
        if isinstance(exp, dict):
            parts.extend([exp.get("role", ""), exp.get("company", "")])
            parts.extend(exp.get("bullets", []))
        else:
            parts.append(str(exp))

    for p in resume_doc.get("projects", []):
        if isinstance(p, dict):
            parts.extend([p.get("title", ""), p.get("tech", "")])
            parts.extend(p.get("bullets", []))
        else:
            parts.append(str(p))

    parts.extend(str(c) for c in resume_doc.get("certifications", []))
    parts.extend(str(a) for a in resume_doc.get("achievements", []))
    return " ".join(parts)


def evaluate_ats_readiness(resume_input: dict[str, Any] | str, target_role: str = "Software Developer") -> dict[str, Any]:
    """
    Comprehensive ATS readiness analysis based on:
    - Structural completeness (Contact, Education, Skills, Projects, Experience, Certifications)
    - Content strength (Action verbs, Quantifiable impact, Keyword relevance)
    - Formatting & length metrics
    """
    doc = normalize_resume_input(resume_input)
    text = _flatten_resume_text(doc)
    lowered = text.lower()
    words = text.split()
    word_count = len(words)

    # 1. Structural Checklist
    has_contact = bool(doc.get("personal_info", {}).get("email") or any(k in lowered for k in ("email", "github", "phone", "@")))
    has_education = bool(doc.get("education") or any(k in lowered for k in ("education", "b.tech", "degree", "bachelor", "master", "gpa", "cgpa", "university", "college")))
    has_skills = bool(doc.get("skills") or any(k in lowered for k in ("skills", "technical skills", "technologies", "proficiencies", "programming")))
    has_projects = bool(doc.get("projects") or any(k in lowered for k in ("project", "portfolio", "built", "implemented", "designed", "application")))
    has_experience = bool(doc.get("experience") or any(k in lowered for k in ("experience", "internship", "work history", "employment", "role")))
    has_certifications = bool(doc.get("certifications") or any(k in lowered for k in ("certified", "certification", "credential", "certificate", "license")))

    structure_checklist = {
        "contact_info": has_contact,
        "education": has_education,
        "skills": has_skills,
        "projects": has_projects,
        "experience": has_experience,
        "certifications": has_certifications,
    }

    # Structure Score (0 to 35 points)
    # Give full credit to students who have rich projects even if traditional full-time experience is 0
    core_sections = [has_contact, has_education, has_skills, has_projects]
    secondary_sections = [has_experience, has_certifications]
    structure_score = (sum(core_sections) / len(core_sections)) * 25.0 + (sum(secondary_sections) / len(secondary_sections)) * 10.0

    # 2. Content & Impact
    action_verb_hits = set()
    for word in words:
        cleaned_word = word.strip(".,;:()[]{}\"'").lower()
        if cleaned_word in ACTION_VERBS:
            action_verb_hits.add(cleaned_word)

    metric_matches = sum(len(pat.findall(text)) for pat in METRIC_PATTERNS)

    # Action verb score (0 to 15 points)
    action_score = min(15.0, len(action_verb_hits) * 2.5)

    # Metric score (0 to 15 points)
    metric_score = min(15.0, metric_matches * 3.0)

    # 3. Role Keywords Match (0 to 25 points)
    detected_skills = extract_skills(text)
    required, source = required_skills(target_role, [])
    req_set = set(normalize_skills(required))
    detected_norm = set(normalize_skills(detected_skills))
    matched_skills = sorted(detected_norm & req_set)
    missing_skills = sorted(req_set - detected_norm)[:6]

    keyword_ratio = len(matched_skills) / max(1, len(req_set))
    keyword_score = min(25.0, keyword_ratio * 25.0)

    # 4. Length & Formatting (0 to 10 points)
    length_score = 10.0 if (250 <= word_count <= 1200) else 5.0 if (150 <= word_count <= 1600) else 2.0

    # Total ATS Readiness Score (0 to 100)
    total_score = round(structure_score + action_score + metric_score + keyword_score + length_score)
    total_score = max(10, min(100, total_score))

    # Strengths and actionable improvement items
    strengths = []
    improvements = []

    if has_contact:
        strengths.append("Verified clear contact information and identity header.")
    else:
        improvements.append("Add accessible contact information (Email, Phone, Location, GitHub/LinkedIn).")

    if has_skills and len(detected_skills) >= 5:
        strengths.append(f"Strong technical skill footprint detected ({len(detected_skills)} skills identified).")
    else:
        improvements.append("Categorize and expand your technical skills (Languages, Frameworks, Cloud, Databases).")

    if has_projects:
        strengths.append("Dedicated project showcase demonstrates practical applied capability.")
    else:
        improvements.append("Add 2–3 in-depth technical projects highlighting end-to-end architecture and deployed links.")

    if len(action_verb_hits) >= 4:
        strengths.append(f"Active voice with strong engineering verbs ({', '.join(sorted(action_verb_hits)[:4])}).")
    else:
        improvements.append("Lead bullet points with decisive action verbs (e.g. Architected, Implemented, Deployed, Automated).")

    if metric_matches >= 2:
        strengths.append("Includes quantifiable impact indicators (numbers, percentages, scale).")
    else:
        improvements.append("Apply STAR format: quantify results wherever possible (e.g. 'reduced latency by 25%', 'handled 500+ users').")

    if missing_skills:
        improvements.append(
            f"Target role competencies to emphasize if you have experience with them: {', '.join(title_skill(s) for s in missing_skills[:4])}."
        )

    if word_count < 250:
        improvements.append("Resume length is very brief. Expand project architectures and problem-solving details.")
    elif word_count > 1200:
        improvements.append("Resume is somewhat dense. Aim for concise, high-signal bullet points to improve scan efficiency.")

    return {
        "ats_readiness_score": total_score,
        "target_role": target_role,
        "score_breakdown": {
            "structure": round(structure_score),
            "action_verbs": round(action_score),
            "quantifiable_metrics": round(metric_score),
            "keyword_alignment": round(keyword_score),
            "formatting_length": round(length_score),
        },
        "structure_checklist": structure_checklist,
        "detected_skills": [title_skill(s) for s in sorted(detected_skills)],
        "matched_skills": [title_skill(s) for s in matched_skills],
        "missing_skills": [title_skill(s) for s in missing_skills],
        "action_verbs_found": sorted(action_verb_hits),
        "metric_indicators_found": metric_matches,
        "word_count": word_count,
        "strengths": strengths,
        "improvements": improvements,
        "disclaimer": (
            "ATS Readiness Score is an educational guideline based on industry formatting and keyword clarity. "
            "It does not guarantee recruiter selection, interview calls, or automated parsing success across distinct employer tools."
        ),
    }


def optimize_resume_for_job(
    resume_input: dict[str, Any] | str,
    job_description: str,
    job_title: str = "Target Opportunity"
) -> dict[str, Any]:
    """
    Compare resume competencies against a specific target job posting.
    Identifies matched skills, missing requirements, and recommended improvements.
    Enforces honest guidance: 'Add this skill only if you genuinely have experience with it.'
    """
    doc = normalize_resume_input(resume_input)
    resume_text = _flatten_resume_text(doc)

    # Extract skills from job description and title
    combined_job_text = f"{job_title} {job_description}"
    job_skills = set(extract_skills(combined_job_text))

    # Fallback to role framework if JD text is terse
    if len(job_skills) < 3:
        role_reqs, _ = required_skills(job_title, [])
        job_skills.update(normalize_skills(role_reqs))

    resume_skills = set(normalize_skills(extract_skills(resume_text)))
    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    match_percentage = round((len(matched) / max(1, len(job_skills))) * 100)

    recommendations = []
    if missing:
        top_missing = [title_skill(s) for s in missing[:4]]
        recommendations.append(
            f"The job posting explicitly mentions {', '.join(top_missing)}. "
            "Add these skills only if you genuinely have experience with them, such as from academic projects, labs, or coursework."
        )

    if matched:
        top_matched = [title_skill(s) for s in matched[:3]]
        recommendations.append(
            f"Highlight your experience with {', '.join(top_matched)} in the top third of your resume and in your bullet points."
        )

    recommendations.append(
        "Tailor your project descriptions to mirror the problems mentioned in the role description (e.g. scalability, APIs, data pipelines)."
    )
    recommendations.append(
        "Never invent experience or technologies. If you have not used a tool, consider building a weekend showcase project to learn it authentically."
    )

    return {
        "job_title": job_title,
        "job_skills": [title_skill(s) for s in sorted(job_skills)],
        "resume_skills": [title_skill(s) for s in sorted(resume_skills)],
        "matched_skills": [title_skill(s) for s in matched],
        "missing_skills": [title_skill(s) for s in missing],
        "alignment_percentage": match_percentage,
        "recommendations": recommendations,
        "honesty_notice": "Add this skill only if you genuinely have experience with it. JobFit prioritizes truthful, high-integrity representation.",
    }
