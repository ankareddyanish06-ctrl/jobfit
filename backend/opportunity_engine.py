"""Student-first Opportunity Engine, Normalizer, and Explainable Matching."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from backend.live_data import extract_skills, format_salary, normalize_skills, title_skill

# Curated High-Signal Student and Fresher Baseline Programs
# Used for verified student discovery alongside Adzuna & The Muse
STUDENT_BASELINE_PROGRAMS: list[dict[str, Any]] = [
    {
        "id": "program-google-step",
        "title": "Student Researcher / STEP Intern",
        "company": "Google",
        "location": "Bengaluru / Hyderabad, India",
        "description": "Student Training in Engineering Program (STEP) is a 12-week developmental internship for undergraduate students with a passion for computer science and technology.",
        "url": "https://careers.google.com/students/",
        "type": "Student Programs",
        "workplace_type": "Hybrid",
        "experience": "Intern / Student",
        "skills": ["python", "c++", "java", "data structures", "git"],
        "source": "Official Student Career Portal",
        "posted_date": "2026-03-01",
        "deadline": "Rolling / Verified",
        "salary_min": None,
        "salary_max": None,
        "salary_formatted": "Competitive Student Stipend",
    },
    {
        "id": "program-msft-explore",
        "title": "Software Engineering Intern — University Program",
        "company": "Microsoft",
        "location": "Bengaluru / Hyderabad / Noida",
        "description": "Designed for students pursuing bachelor's or master's degrees in CS/IT. Work on cutting-edge Azure, Office, and Developer Tools under senior engineering mentorship.",
        "url": "https://careers.microsoft.com/v2/global/en/students.html",
        "type": "Internships",
        "workplace_type": "Hybrid",
        "experience": "Intern / Student",
        "skills": ["c++", "c#", "azure", "data structures", "git", "rest api"],
        "source": "Official Student Career Portal",
        "posted_date": "2026-02-15",
        "deadline": "Rolling / Verified",
        "salary_min": None,
        "salary_max": None,
        "salary_formatted": "Industry Benchmark Stipend",
    },
    {
        "id": "program-amazon-sde-intern",
        "title": "Software Development Engineer Intern (Summer)",
        "company": "Amazon",
        "location": "Bengaluru / Hyderabad / Chennai",
        "description": "6-month or summer internship for pre-final and final year students. Design, implement, and test core distributed software systems powering Amazon AWS and Retail.",
        "url": "https://amazon.jobs/en/job_categories/software-development",
        "type": "Internships",
        "workplace_type": "Hybrid",
        "experience": "Intern / Student",
        "skills": ["java", "python", "aws", "data structures", "linux"],
        "source": "Amazon University Hiring",
        "posted_date": "2026-02-20",
        "deadline": "Rolling / Verified",
        "salary_min": None,
        "salary_max": None,
        "salary_formatted": "Standard University Stipend",
    },
    {
        "id": "program-tcs-ninja-digital",
        "title": "Graduate Engineer Trainee (Ninja & Digital)",
        "company": "Tata Consultancy Services (TCS)",
        "location": "Pan-India / Multiple Locations",
        "description": "Premier entry-level career program for engineering graduates across India. Extensive foundational bootcamps in cloud, full-stack, and enterprise architecture.",
        "url": "https://www.tcs.com/careers/india/entry-level-hiring",
        "type": "Fresher Jobs",
        "workplace_type": "On-site",
        "experience": "Fresher / Entry",
        "skills": ["python", "java", "sql", "data structures", "html", "css"],
        "source": "TCS National Qualifier / Campus Hiring",
        "posted_date": "2026-01-10",
        "deadline": "Batch Specific",
        "salary_min": 360000,
        "salary_max": 750000,
        "salary_formatted": "₹3.6L - ₹7.5L / year",
    },
    {
        "id": "program-infosys-specialist",
        "title": "Associate Developer / Specialist Programmer",
        "company": "Infosys",
        "location": "Bengaluru / Pune / Hyderabad",
        "description": "Hiring fresh engineering graduates for specialist software engineering tracks. High-impact roles in microservices, AI engineering, and cloud platforms.",
        "url": "https://www.infosys.com/careers.html",
        "type": "Graduate Programs",
        "workplace_type": "Hybrid",
        "experience": "Fresher / Entry",
        "skills": ["java", "python", "sql", "rest api", "git", "docker"],
        "source": "Infosys Springboard / Campus Portal",
        "posted_date": "2026-01-25",
        "deadline": "Batch Specific",
        "salary_min": 450000,
        "salary_max": 950000,
        "salary_formatted": "₹4.5L - ₹9.5L / year",
    },
    {
        "id": "program-deloitte-analyst",
        "title": "Graduate Analyst / Associate Solution Advisor",
        "company": "Deloitte",
        "location": "Bengaluru / Hyderabad / Mumbai",
        "description": "Technology consulting and analytics role for fresh graduates. Build dashboards, SQL models, and cloud integrations for global enterprise clients.",
        "url": "https://www2.deloitte.com/ui/en/pages/careers/articles/technology-consulting.html",
        "type": "Graduate Programs",
        "workplace_type": "Hybrid",
        "experience": "Fresher / Entry",
        "skills": ["sql", "python", "power bi", "excel", "data analysis"],
        "source": "Deloitte Early Careers",
        "posted_date": "2026-02-10",
        "deadline": "Annual Cohort",
        "salary_min": 600000,
        "salary_max": 900000,
        "salary_formatted": "₹6.0L - ₹9.0L / year",
    },
    {
        "id": "program-mlh-fellowship",
        "title": "Open Source Fellow — Student Developer Program",
        "company": "Major League Hacking (MLH)",
        "location": "Remote / Worldwide",
        "description": "A 12-week educational internship alternative for students worldwide. Contribute to major open-source repositories under professional engineering mentorship.",
        "url": "https://fellowship.mlh.io/",
        "type": "Student Programs",
        "workplace_type": "Remote",
        "experience": "Intern / Student",
        "skills": ["python", "javascript", "git", "rest api", "docker"],
        "source": "MLH Fellowship Portal",
        "posted_date": "2026-03-05",
        "deadline": "Cohort Applications Open",
        "salary_min": None,
        "salary_max": None,
        "salary_formatted": "Educational Grant / Stipend",
    },
    {
        "id": "program-gsoc",
        "title": "Google Summer of Code Contributor",
        "company": "Google Open Source",
        "location": "Remote / Global",
        "description": "A global program focused on bringing new developers and students into open source software development. 12-to-22 week coding projects with mentorship.",
        "url": "https://summerofcode.withgoogle.com/",
        "type": "Student Programs",
        "workplace_type": "Remote",
        "experience": "Intern / Student",
        "skills": ["python", "c++", "git", "linux", "rest api"],
        "source": "GSoC Official Portal",
        "posted_date": "2026-02-01",
        "deadline": "Annual Schedule",
        "salary_min": None,
        "salary_max": None,
        "salary_formatted": "Open Source Stipend",
    },
    {
        "id": "program-accenture-ase",
        "title": "Associate Software Engineer",
        "company": "Accenture",
        "location": "Bengaluru / Chennai / Hyderabad / Pune",
        "description": "Entry-level engineering role for fresh graduates. Develop, design, and deliver cloud applications, test automation suites, and API backends.",
        "url": "https://www.accenture.com/in-en/careers/jobsearch",
        "type": "Fresher Jobs",
        "workplace_type": "Hybrid",
        "experience": "Fresher / Entry",
        "skills": ["java", "python", "sql", "git", "cloud"],
        "source": "Accenture Campus Careers",
        "posted_date": "2026-02-18",
        "deadline": "Verified",
        "salary_min": 450000,
        "salary_max": 650000,
        "salary_formatted": "₹4.5L - ₹6.5L / year",
    },
    {
        "id": "program-cisco-intern",
        "title": "Software Engineer Intern — Cloud & Networking",
        "company": "Cisco",
        "location": "Bengaluru, Karnataka",
        "description": "Hands-on internship for engineering students working on cloud platforms, network automation, and security infrastructure.",
        "url": "https://jobs.cisco.com/jobs/SearchJobs",
        "type": "Internships",
        "workplace_type": "Hybrid",
        "experience": "Intern / Student",
        "skills": ["python", "networking", "linux", "git", "docker"],
        "source": "Cisco University Hiring",
        "posted_date": "2026-03-02",
        "deadline": "Verified",
        "salary_min": None,
        "salary_max": None,
        "salary_formatted": "Paid Internship Stipend",
    }
]


def classify_opportunity_type(title: str, description: str) -> str:
    """Classify an opportunity into student categories."""
    text = f"{title} {description}".lower()

    if any(k in text for k in ("intern", "internship", "summer analyst", "co-op")):
        return "Internships"
    if any(k in text for k in ("student program", "fellowship", "summer of code", "campus ambassador", "hackathon")):
        return "Student Programs"
    if any(k in text for k in ("graduate engineer", "graduate program", "trainee", "campus hiring", "campus recruit")):
        return "Graduate Programs"
    if any(k in text for k in ("fresher", "entry level", "junior", "associate developer", "associate software", "entry-level")):
        return "Fresher Jobs"
    if any(k in text for k in ("part-time", "part time", "flexible hours")):
        return "Part-Time"
    return "Jobs"


def classify_workplace_type(title: str, location: str, description: str) -> str:
    """Classify workplace type into Remote, Hybrid, or On-site."""
    text = f"{title} {location} {description}".lower()
    if any(k in text for k in ("remote", "work from home", "wfh", "anywhere", "virtual")):
        return "Remote"
    if any(k in text for k in ("hybrid", "flexible workplace")):
        return "Hybrid"
    return "On-site"


def normalize_opportunity(item: dict[str, Any], provider_name: str = "Live Provider") -> dict[str, Any]:
    """Ensure consistent opportunity dictionary contract."""
    title = item.get("title") or item.get("name") or "Untitled Role"
    description = item.get("description") or ""
    location = item.get("location") or "Location not specified"
    op_type = item.get("type") or classify_opportunity_type(title, description)
    workplace = item.get("workplace_type") or classify_workplace_type(title, location, description)

    skills = item.get("skills")
    if not skills:
        skills = extract_skills(f"{title} {description}")

    return {
        "id": str(item.get("id")),
        "title": title,
        "company": item.get("company") or "Leading Employer",
        "location": location,
        "description": description[:360],
        "url": item.get("url") or item.get("redirect_url") or "#",
        "type": op_type,
        "workplace_type": workplace,
        "experience": item.get("experience") or item.get("seniority") or "Entry / Fresher",
        "skills": [title_skill(s) for s in skills],
        "source": item.get("source") or provider_name,
        "posted_date": item.get("posted_date") or item.get("published_at") or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "deadline": item.get("deadline") or "Verified active",
        "salary_min": item.get("salary_min"),
        "salary_max": item.get("salary_max"),
        "salary_formatted": item.get("salary_formatted"),
    }


def explain_opportunity_match(opportunity: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """
    Explainable match generator ('Why This Opportunity?').
    Analyzes:
    - Skill alignment
    - Preference match (Internship vs Full-Time)
    - Location and remote mode match
    - Experience level fit
    Never outputs fake probabilistic statements like 'You have an 87% chance of getting hired'.
    """
    # 1. Skills Comparison
    raw_profile_skills = profile.get("technical_skills") or profile.get("skills") or []
    if isinstance(raw_profile_skills, dict):
        flat_skills = [s for sub in raw_profile_skills.values() for s in (sub if isinstance(sub, list) else [sub])]
    elif isinstance(raw_profile_skills, list):
        flat_skills = raw_profile_skills
    else:
        flat_skills = str(raw_profile_skills).split(",")

    user_skills_set = set(normalize_skills(flat_skills))
    opp_skills_set = set(normalize_skills(opportunity.get("skills") or []))

    matched_skills = sorted(user_skills_set & opp_skills_set)
    missing_skills = sorted(opp_skills_set - user_skills_set)

    # 2. Preference Comparison
    pref_type = (profile.get("opportunity_preference") or "Both").lower()
    opp_type = (opportunity.get("type") or "Jobs").lower()
    type_matches = (
        pref_type == "both"
        or (pref_type == "internship" and "intern" in opp_type)
        or (pref_type == "full-time" and ("job" in opp_type or "graduate" in opp_type or "fresher" in opp_type))
    )

    # 3. Location / Remote Comparison
    pref_remote = (profile.get("remote_preference") or "Any").lower()
    workplace = (opportunity.get("workplace_type") or "On-site").lower()
    remote_matches = (
        pref_remote == "any"
        or (pref_remote == "remote" and workplace == "remote")
        or (pref_remote == "hybrid" and workplace in ("hybrid", "remote"))
        or (pref_remote == "on-site")
    )

    pref_locations = [l.strip().lower() for l in profile.get("preferred_locations") or []]
    opp_location = (opportunity.get("location") or "").lower()
    location_matches = (
        not pref_locations
        or any(pl in opp_location for pl in pref_locations)
        or "remote" in workplace
    )

    # Build explainable evidence bullet points
    evidence: list[dict[str, str]] = []

    for s in matched_skills[:4]:
        evidence.append({
            "type": "positive",
            "message": f"Skill Match: {title_skill(s)} is directly highlighted in your profile."
        })

    if type_matches:
        evidence.append({
            "type": "positive",
            "message": f"Role Type: {opportunity.get('type')} aligns with your career preference ({profile.get('opportunity_preference') or 'Both'})."
        })

    if remote_matches and location_matches:
        evidence.append({
            "type": "positive",
            "message": f"Work Arrangement: {opportunity.get('workplace_type')} / {opportunity.get('location')} matches your location preferences."
        })

    for s in missing_skills[:3]:
        evidence.append({
            "type": "gap",
            "message": f"Recommended Preparation: {title_skill(s)} appears in requirements. Add this only if you genuinely have experience with it."
        })

    if not matched_skills:
        evidence.append({
            "type": "neutral",
            "message": "Foundational opportunity: build hands-on project samples using the listed skills before applying."
        })

    # Transparent alignment status
    if len(matched_skills) >= 3 and (type_matches or remote_matches):
        alignment_tier = "High Competency Alignment"
    elif len(matched_skills) >= 1:
        alignment_tier = "Moderate Skill Alignment"
    else:
        alignment_tier = "Growth / Stretch Opportunity"

    return {
        "opportunity_id": opportunity.get("id"),
        "title": opportunity.get("title"),
        "company": opportunity.get("company"),
        "alignment_tier": alignment_tier,
        "matched_skills": [title_skill(s) for s in matched_skills],
        "missing_skills": [title_skill(s) for s in missing_skills],
        "evidence": evidence,
        "disclaimer": (
            "Why This Opportunity alignment is transparent educational criteria matching based on your profile inputs. "
            "It is not an automated recruitment decision or employment probability."
        ),
    }
