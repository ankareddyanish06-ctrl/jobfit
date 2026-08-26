"""Explainable student career analysis built from profile evidence and live job requirements."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any
from backend.live_data import extract_skills, normalize_skills

KNOWN_ROLE_SKILLS: dict[str, list[str]] = {
    "software developer": ["python", "java", "javascript", "sql", "git", "data structures", "rest api", "docker"],
    "software engineer": ["python", "java", "c++", "data structures", "system design", "git", "rest api", "sql", "docker"],
    "frontend developer": ["html", "css", "javascript", "typescript", "react", "next.js", "tailwind", "git", "rest api"],
    "backend developer": ["python", "java", "node.js", "sql", "postgresql", "rest api", "docker", "redis", "git", "microservices"],
    "full stack developer": ["javascript", "typescript", "react", "node.js", "python", "sql", "mongodb", "docker", "git", "rest api"],
    "data analyst": ["python", "sql", "excel", "power bi", "tableau", "data analysis", "statistics", "pandas"],
    "data scientist": ["python", "sql", "machine learning", "statistics", "pandas", "numpy", "scikit-learn", "data analysis"],
    "data engineer": ["python", "sql", "postgresql", "aws", "docker", "spark", "kafka", "snowflake", "data analysis"],
    "machine learning engineer": ["python", "machine learning", "deep learning", "pytorch", "tensorflow", "docker", "rest api", "sql", "git"],
    "ai engineer": ["python", "machine learning", "deep learning", "nlp", "llm", "langchain", "docker", "rest api", "git", "pytorch"],
    "cloud engineer": ["linux", "aws", "azure", "docker", "kubernetes", "python", "networking", "terraform", "git"],
    "cloud architect": ["aws", "azure", "gcp", "kubernetes", "docker", "system design", "networking", "cybersecurity", "terraform"],
    "devops engineer": ["linux", "aws", "docker", "kubernetes", "ci/cd", "git", "python", "terraform", "ansible"],
    "site reliability engineer": ["linux", "kubernetes", "docker", "python", "go", "ci/cd", "monitoring", "networking", "cloud"],
    "platform engineer": ["kubernetes", "docker", "terraform", "go", "python", "aws", "ci/cd", "linux", "git"],
    "cybersecurity analyst": ["cybersecurity", "networking", "linux", "python", "firewall", "siem", "ethical hacking", "git"],
    "security engineer": ["cybersecurity", "linux", "python", "cryptography", "cloud security", "networking", "docker", "git"],
    "qa engineer": ["testing", "selenium", "python", "javascript", "rest api", "git", "jira", "ci/cd"],
    "automation test engineer": ["selenium", "python", "java", "testing", "rest api", "ci/cd", "git", "docker"],
    "mobile developer": ["flutter", "dart", "react native", "javascript", "kotlin", "swift", "rest api", "git"],
    "android developer": ["kotlin", "java", "android sdk", "rest api", "git", "sqlite", "jetpack compose"],
    "ios developer": ["swift", "swiftui", "ios sdk", "rest api", "git", "xcode", "core data"],
    "ui/ux designer": ["figma", "wireframing", "prototyping", "user research", "html", "css", "design systems"],
    "ui/ux developer": ["html", "css", "javascript", "react", "figma", "tailwind", "responsive design", "git"],
    "database administrator": ["sql", "postgresql", "mysql", "oracle", "mongodb", "backup & recovery", "performance tuning", "linux"],
    "network engineer": ["networking", "cisco", "tcp/ip", "firewall", "routing & switching", "linux", "python", "wireshark"],
    "servicenow developer": ["javascript", "servicenow", "rest api", "sql", "html", "css", "git", "itsm"],
    "salesforce developer": ["apex", "visualforce", "salesforce", "javascript", "soql", "rest api", "git"],
    "sap consultant": ["sap", "abap", "erp", "sql", "business process", "sap hana", "excel"],
    "business analyst": ["sql", "excel", "power bi", "tableau", "agile", "jira", "requirements gathering", "data analysis"],
    "product manager": ["agile", "jira", "product roadmap", "data analysis", "user research", "sql", "market research"],
    "blockchain developer": ["solidity", "ethereum", "smart contracts", "javascript", "web3", "rust", "cryptography", "git"],
    "embedded systems engineer": ["c", "c++", "microcontrollers", "rtos", "linux", "pcb design", "embedded c", "git"]
}

SPECIAL_TITLES: dict[str, str] = {
    "sql": "SQL",
    "aws": "AWS",
    "gcp": "GCP",
    "rest api": "REST API",
    "html": "HTML",
    "css": "CSS",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "node.js": "Node.js",
    "power bi": "Power BI",
    "ci/cd": "CI/CD",
    "servicenow": "ServiceNow",
    "qa": "QA",
    "ui/ux": "UI/UX",
    "nlp": "NLP",
    "llm": "LLM",
    "sre": "SRE",
    "itsm": "ITSM",
    "abap": "ABAP",
    "erp": "ERP",
    "tcp/ip": "TCP/IP",
    "soql": "SOQL",
    "rtos": "RTOS",
    "c++": "C++",
    "c#": "C#",
    "dotnet": ".NET",
    "vue": "Vue.js",
    "react": "React",
    "next.js": "Next.js",
    "mongodb": "MongoDB",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "redis": "Redis",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "jira": "Jira",
    "figma": "Figma",
    "selenium": "Selenium",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow"
}


def title_skill(skill: str) -> str:
    key = skill.strip().lower()
    return SPECIAL_TITLES.get(key, skill.strip().title())


def suggested_roles() -> list[str]:
    return [
        "Software Developer",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "AI / Machine Learning Engineer",
        "Data Scientist",
        "Data Analyst",
        "Data Engineer",
        "Cloud Engineer",
        "DevOps Engineer",
        "Platform Engineer",
        "Site Reliability Engineer (SRE)",
        "Cybersecurity Analyst",
        "Security Engineer",
        "QA / Automation Engineer",
        "Mobile Developer (Flutter / React Native)",
        "Android Developer",
        "iOS Developer",
        "UI/UX Developer",
        "Database Administrator",
        "Network Engineer",
        "ServiceNow Developer",
        "Salesforce Developer",
        "SAP Consultant",
        "Business Analyst",
        "Product Manager",
        "Blockchain Developer",
        "Embedded Systems Engineer"
    ]


def _infer_skills_from_title(title: str) -> list[str]:
    canonical = title.lower()
    inferred: set[str] = set()

    if any(k in canonical for k in ("cloud", "aws", "azure", "gcp")):
        inferred.update(["cloud", "aws", "linux", "docker", "kubernetes", "python", "networking"])
    if any(k in canonical for k in ("ai", "machine learning", "deep learning", "llm", "nlp", "vision")):
        inferred.update(["python", "machine learning", "deep learning", "pytorch", "rest api", "git", "sql"])
    if any(k in canonical for k in ("data", "analytics", "bi", "scientist")):
        inferred.update(["python", "sql", "data analysis", "statistics", "power bi", "pandas"])
    if any(k in canonical for k in ("devops", "sre", "reliability", "platform", "infrastructure")):
        inferred.update(["linux", "docker", "kubernetes", "ci/cd", "git", "python", "aws", "terraform"])
    if any(k in canonical for k in ("security", "cyber", "infosec", "soc")):
        inferred.update(["cybersecurity", "networking", "linux", "python", "firewall", "git"])
    if any(k in canonical for k in ("frontend", "ui", "ux", "web", "client")):
        inferred.update(["html", "css", "javascript", "react", "typescript", "git", "rest api"])
    if any(k in canonical for k in ("backend", "api", "server", "distributed")):
        inferred.update(["python", "java", "sql", "rest api", "docker", "postgresql", "git", "redis"])
    if any(k in canonical for k in ("full stack", "fullstack")):
        inferred.update(["javascript", "react", "node.js", "python", "sql", "docker", "git", "rest api"])
    if any(k in canonical for k in ("qa", "test", "automation", "quality", "sdet")):
        inferred.update(["testing", "python", "selenium", "rest api", "git", "ci/cd"])
    if any(k in canonical for k in ("mobile", "app", "android", "ios", "flutter")):
        inferred.update(["flutter", "react native", "javascript", "kotlin", "rest api", "git"])

    if inferred:
        return sorted(inferred)
    return ["python", "sql", "git", "rest api", "data structures", "docker", "linux"]


def required_skills(target_role: str, jobs: list[dict]) -> tuple[list[str], str]:
    canonical = target_role.strip().lower()

    # Exact or substring match in curated taxonomy
    for role, skills in KNOWN_ROLE_SKILLS.items():
        if role in canonical or canonical in role:
            return skills, f"Role Framework ({title_skill(role)})"

    # Match from live jobs if provided
    counts = Counter(skill for job in jobs for skill in job.get("skills", []))
    if counts and len(counts) >= 3:
        top_from_jobs = [skill for skill, _ in counts.most_common(10)]
        return top_from_jobs, "Real-time Live Job Evidence"

    # Fuzzy/semantic keyword extraction
    inferred = _infer_skills_from_title(target_role)
    return inferred, "Role Keyword Intelligence & IT Baseline"


def eligibility(profile: dict[str, Any], skills: set[str], requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for company in requirements:
        issues = []
        if profile["cgpa"] < company["min_cgpa"]:
            issues.append(f"Requires CGPA ≥ {company['min_cgpa']:.1f} (you have {profile['cgpa']:.2f})")
        if profile["backlogs"] > company["max_backlogs"]:
            issues.append(f"Permits max {company['max_backlogs']} backlog(s) (you have {profile['backlogs']})")
        if company["branches"] and profile["branch"] not in [b.upper() for b in company["branches"]]:
            issues.append(f"Eligible branches: {', '.join(company['branches'])}")
        if company["graduation_year"] and profile["graduation_year"] != company["graduation_year"]:
            issues.append(f"Targeting batch {company['graduation_year']}")

        comp_skills = normalize_skills(company["skills"])
        missing = sorted(comp_skills - skills)
        matched_count = len(comp_skills & skills)

        status = "Eligible" if not issues and not missing else "Almost Eligible" if not issues else "Not Eligible"
        results.append({
            "company": company["company"],
            "status": status,
            "reasons": issues,
            "warnings": [f"Recommended to build: {', '.join(title_skill(skill) for skill in missing)}"] if missing else [],
            "required_skills": [title_skill(skill) for skill in company["skills"]],
            "skills_matched": matched_count,
            "skills_total": len(comp_skills),
            "source_url": company["source_url"],
            "verified_at": company["verified_at"],
        })
    return results


def _generate_project_ideas(target_role: str, missing_skills: list[str]) -> list[dict[str, str]]:
    focus = [title_skill(s) for s in missing_skills[:2]]
    focus_str = " and ".join(focus) if focus else "production technologies"
    return [
        {
            "title": f"Full-Stack {target_role} Showcase Platform",
            "description": f"Design an end-to-end service implementing {focus_str} with clean architecture, containerization, CI/CD pipeline, and public cloud deployment."
        },
        {
            "title": f"Live Analytics & Automation Pipeline",
            "description": f"Build a data ingestion or automation workflow that integrates REST APIs, structured storage (SQL/NoSQL), and interactive visualization."
        }
    ]


def analyze_profile(profile: dict[str, Any], requirements: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> dict[str, Any]:
    skills = normalize_skills(profile["technical_skills"])
    required, source = required_skills(profile["target_role"], jobs)
    required_set = set(normalize_skills(required))
    matched = sorted(skills & required_set)
    missing = sorted(required_set - skills)

    # Compute transparent factor scores (0-100 scale)
    academic_score = round(min(100.0, max(0.0, (profile["cgpa"] / 10.0) * 100.0 - (profile["backlogs"] * 8.0))))
    technical_score = round((len(matched) / max(1, len(required_set))) * 100.0)
    experience_score = min(100, profile["projects"] * 18 + profile["internships"] * 25)
    certifications_score = min(100, len(profile["certifications"]) * 25)
    aptitude_score = round(float(profile["aptitude_score"]))
    interview_score = round(float(profile["interview_score"]))

    # Weighted composite readiness calculation
    readiness = round(
        academic_score * 0.20
        + technical_score * 0.38
        + experience_score * 0.18
        + certifications_score * 0.08
        + aptitude_score * 0.08
        + interview_score * 0.08
    )
    readiness = max(5, min(100, readiness))

    priorities = missing[:4]
    secondary = missing[4:8]

    reasons: list[str] = [
        f"Target skills benchmarked against {source}.",
        f"You match {len(matched)} of {len(required_set)} core technical competencies for this role."
    ]
    if profile["projects"] < 2:
        reasons.append("Building at least 2 complete, deployed portfolio projects will strongly elevate your hiring signal.")
    if profile["internships"] > 0:
        reasons.append(f"Practical industry experience ({profile['internships']} internship) adds tangible credibility to your profile.")
    if priorities:
        reasons.append(f"Immediate high-priority gap: focus on mastering {title_skill(priorities[0])}.")

    roadmap = [
        {
            "period": "Weeks 1–2",
            "topic": "Core Gap Remediation",
            "action": f"Deep-dive into {', '.join(title_skill(item) for item in priorities[:2]) or 'core role fundamentals'}; build foundational code samples and hands-on exercises."
        },
        {
            "period": "Weeks 3–4",
            "topic": "Applied Portfolio Project",
            "action": f"Architect and code an end-to-end {profile['target_role']} project integrating {title_skill(priorities[0]) if priorities else 'your strongest tools'} and Git version control."
        },
        {
            "period": "Weeks 5–6",
            "topic": "Engineering Polish & Deployment",
            "action": "Add unit tests, Docker containerization, comprehensive README architecture diagrams, and deploy live on cloud."
        },
        {
            "period": "Week 7",
            "topic": "Market Readiness & Interview Prep",
            "action": "Refactor your résumé with STAR-format project impact bullet points and practice technical system design and behavioral rounds."
        }
    ]

    interview = [
        f"Walk through the end-to-end architecture of your most challenging {profile['target_role']} project.",
        f"How would you approach scaling or optimizing a bottleneck when working with {title_skill(matched[0]) if matched else 'distributed systems'}?",
        f"Explain how you would implement or troubleshoot {title_skill(priorities[0]) if priorities else 'a critical production bug'} in a live environment.",
        "Describe a difficult technical problem you faced, the alternative solutions you evaluated, and why you chose your final approach."
    ]

    project_ideas = _generate_project_ideas(profile["target_role"], priorities)

    readiness_label = (
        "Application Ready (High Signal)" if readiness >= 80
        else "Strong Competence (Near Target)" if readiness >= 65
        else "Developing Skill Profile" if readiness >= 45
        else "Foundational Stage"
    )

    return {
        "role": {"title": profile["target_role"]},
        "readiness_score": readiness,
        "readiness_label": readiness_label,
        "score_breakdown": {
            "academics": academic_score,
            "technical_skills": technical_score,
            "experience": experience_score,
            "certifications": certifications_score,
            "aptitude": aptitude_score,
            "interview": interview_score,
        },
        "skill_gap": {
            "matched": [title_skill(item) for item in matched],
            "missing": [title_skill(item) for item in missing],
            "priority": [title_skill(item) for item in priorities],
            "secondary": [title_skill(item) for item in secondary],
            "source": source,
        },
        "eligibility": eligibility(profile, skills, requirements),
        "roadmap": roadmap,
        "project_ideas": project_ideas,
        "next_action": f"Master {title_skill(priorities[0]) if priorities else 'portfolio architecture'} next to close the primary competency gap for {profile['target_role']} opportunities.",
        "reasons": reasons,
        "interview_prep": interview,
    }


def analyze_resume(text: str, target_role: str) -> dict[str, Any]:
    detected = set(extract_skills(text))
    required, source = required_skills(target_role, [])
    required_set = set(normalize_skills(required))
    matched = sorted(detected & required_set)
    missing = sorted(required_set - detected)[:6]

    lowered = text.lower()
    sections = {
        "education": any(w in lowered for w in ("education", "academics", "b.tech", "degree", "bachelor", "master", "gpa", "cgpa", "university", "college")),
        "project": any(w in lowered for w in ("project", "portfolio", "application", "built", "developed", "system", "designed")),
        "skill": any(w in lowered for w in ("skill", "technologies", "proficiencies", "technical expertise", "tools", "languages")),
        "experience": any(w in lowered for w in ("experience", "internship", "employment", "work history", "job", "role")),
        "certification": any(w in lowered for w in ("certification", "certificate", "credential", "certified", "award", "achievement")),
        "contact": any(w in lowered for w in ("email", "github", "linkedin", "phone", "@", "portfolio", "http")),
    }

    # Actionable ATS scoring
    section_score = sum(sections.values()) / len(sections) * 35.0
    skill_match_ratio = len(matched) / max(1, len(required_set))
    skill_score = min(50.0, skill_match_ratio * 50.0)
    length_bonus = 15.0 if 200 <= len(text.split()) <= 1500 else 8.0

    resume_strength = max(10, min(100, round(section_score + skill_score + length_bonus)))

    suggestions: list[str] = []
    if not sections["project"]:
        suggestions.append("Add a dedicated 'Projects' section featuring 2-3 significant applications with quantifiable metrics.")
    if not sections["experience"]:
        suggestions.append("Add an 'Experience' or 'Internships & Research' section to showcase real-world teamwork and problem solving.")
    if not sections["skill"]:
        suggestions.append("Include a categorized 'Technical Skills' block (Languages, Frameworks, Cloud/Databases, Tools).")
    if not sections["certification"]:
        suggestions.append("Highlight verifiable industry certifications (e.g. AWS, Oracle, Google Cloud, Azure) to boost ATS ranking.")
    if missing:
        suggestions.append(f"Target role keywords to incorporate naturally: {', '.join(title_skill(item) for item in missing[:4])}.")
    if not any(k in lowered for k in ("%", "increased", "reduced", "improved", "optimized", "scale", "latency", "ms", "users")):
        suggestions.append("Use STAR-method impact statements with measurable outcomes (e.g., 'Improved response time by 30%').")

    if not suggestions:
        suggestions.append("Excellent structure! Ensure all live demo links and GitHub repositories are publicly accessible.")

    return {
        "resume_strength": resume_strength,
        "detected_skills": [title_skill(item) for item in sorted(detected)],
        "matched_skills": [title_skill(item) for item in matched],
        "missing_role_skills": [title_skill(item) for item in missing],
        "sections_found": sections,
        "suggestions": suggestions,
        "comparison_source": source,
        "word_count": len(text.split()),
    }

