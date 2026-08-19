"""Explainable, role-specific readiness analysis. No fictional company or job records."""
from __future__ import annotations

ROLE_CATALOG = {
"data-analyst":{"title":"Data Analyst","skills":["python","sql","excel","power bi","tableau","statistics","data analysis"],"roadmap":[("Weeks 1–2","SQL foundations","Practice joins, aggregations, window functions, and a sales dataset."),("Weeks 3–4","Data visualization","Build an Excel or Power BI dashboard with business insights."),("Weeks 5–6","Python analysis","Use pandas and matplotlib in an exploratory-data-analysis project."),("Week 7","Portfolio and interview","Publish one analysis and rehearse SQL/business-case questions.")],"interview":["Explain the difference between INNER JOIN and LEFT JOIN.","How would you identify outliers in a dataset?","Describe a dashboard insight that influenced a decision."]},
"software-developer":{"title":"Software Developer","skills":["python","java","javascript","sql","git","data structures","rest api","docker"],"roadmap":[("Weeks 1–2","Programming and DSA","Solve arrays, strings, linked-list, and complexity problems daily."),("Weeks 3–4","Backend foundations","Build REST APIs, validate input, and persist data with SQL."),("Weeks 5–6","Engineering workflow","Use Git, tests, Docker, and deployment for a portfolio app."),("Week 7","Interview and résumé","Prepare project stories, DSA patterns, and role-specific résumé bullets.")],"interview":["What is the time complexity of a hash-table lookup?","How would you design a REST API for a task manager?","Explain a project trade-off you made."]},
"servicenow-developer":{"title":"ServiceNow Developer","skills":["javascript","servicenow","rest api","sql","html","css","git"],"roadmap":[("Weeks 1–2","JavaScript","Learn ES6 syntax, functions, objects, arrays, and asynchronous requests."),("Week 3","Web and APIs","Practice forms, JSON, HTTP methods, and REST API integration."),("Weeks 4–5","ServiceNow platform","Complete ServiceNow fundamentals and configure sample workflows."),("Weeks 6–7","Portfolio and preparation","Build a catalog/workflow example and prepare ITSM interview concepts.")],"interview":["What is the difference between a Business Rule and Client Script?","How do you secure a ServiceNow table?","Explain an API integration approach."]},
"web-developer":{"title":"Web Developer","skills":["html","css","javascript","react","node.js","rest api","git","sql"],"roadmap":[("Weeks 1–2","Web foundations","Build accessible, responsive pages with semantic HTML and modern CSS."),("Weeks 3–4","JavaScript","Practice DOM, asynchronous data fetching, forms, and ES6 modules."),("Weeks 5–6","React and APIs","Create a component-based frontend connected to a REST API."),("Week 7","Deploy a portfolio project","Add tests, a README, Git history, and a public URL.")],"interview":["What is the CSS box model?","How does the JavaScript event loop work?","How do you make a page accessible on mobile?"]},
"cloud-engineer":{"title":"Cloud Engineer","skills":["linux","aws","azure","docker","kubernetes","python","networking","git"],"roadmap":[("Weeks 1–2","Linux and networking","Practice shell commands, permissions, DNS, HTTP, and IP basics."),("Weeks 3–4","Cloud fundamentals","Learn IAM, compute, storage, networking, and cost basics on one cloud."),("Weeks 5–6","Containers and automation","Containerize an app and automate a deployment with Git."),("Week 7","Cloud project","Deploy a secure API project and document its architecture.")],"interview":["What is the principle of least privilege in IAM?","Compare containers and virtual machines.","How would you make an application highly available?"]}}
ALIASES={"node":"node.js","nodejs":"node.js","ml":"machine learning","powerbi":"power bi","rest":"rest api","service now":"servicenow","dsa":"data structures"}


def normalize_skills(skills:list[str])->set[str]: return {ALIASES.get(value.strip().lower(),value.strip().lower()) for value in skills if value.strip()}
def title_skill(skill:str)->str: return {"sql":"SQL","aws":"AWS","rest api":"REST API","html":"HTML","css":"CSS","javascript":"JavaScript","node.js":"Node.js","power bi":"Power BI","servicenow":"ServiceNow"}.get(skill,skill.title())
def role_options()->list[dict]: return [{"id":key,"title":value["title"],"skills":[title_skill(item) for item in value["skills"]]} for key,value in ROLE_CATALOG.items()]


def eligibility(profile:dict, skills:set[str], requirements:list[dict])->list[dict]:
    records=[]
    for company in requirements:
        reasons=[]
        if profile["cgpa"]<company["min_cgpa"]: reasons.append(f"CGPA requires {company['min_cgpa']:.1f} or above")
        if profile["backlogs"]>company["max_backlogs"]: reasons.append(f"Allows a maximum of {company['max_backlogs']} backlog(s)")
        if company["branches"] and profile["branch"] not in company["branches"]: reasons.append("Branch is outside the verified eligibility list")
        if company["graduation_year"] and profile["graduation_year"]!=company["graduation_year"]: reasons.append(f"Listed hiring batch is {company['graduation_year']}")
        missing=sorted(set(company["skills"])-skills)
        status="Eligible" if not reasons and not missing else "Almost Eligible" if not reasons else "Not Eligible"
        records.append({"company":company["company"],"status":status,"reasons":reasons,"warnings":[f"Build: {', '.join(title_skill(skill) for skill in missing)}"] if missing else [],"required_skills":company["skills"],"source_url":company["source_url"],"verified_at":company["verified_at"]})
    return records


def analyze_profile(profile:dict, requirements:list[dict])->dict:
    role=ROLE_CATALOG[profile["target_role"]]; skills=normalize_skills(profile["technical_skills"]); required=set(role["skills"]); matched=sorted(skills&required); missing=sorted(required-skills)
    technical=round(len(matched)/len(required)*100); academic=round(profile["cgpa"]*10); experience=min(100,profile["projects"]*14+profile["internships"]*24); certifications=min(100,len(profile["certifications"])*25)
    readiness=round(academic*.22+technical*.38+experience*.18+certifications*.07+profile["aptitude_score"]*.08+profile["interview_score"]*.07); priorities=missing[:4]
    reasons=[]
    if academic>=75: reasons.append("Your academic score strengthens roles with CGPA requirements.")
    if matched: reasons.append(f"You already match {len(matched)} core {role['title']} skill(s).")
    if profile["projects"]>=2: reasons.append("Your project count provides practical portfolio evidence.")
    if priorities: reasons.append(f"The biggest role gap is {title_skill(priorities[0])}.")
    return {"role":{"id":profile["target_role"],"title":role["title"]},"readiness_score":readiness,"readiness_label":"Strong" if readiness>=75 else "Developing" if readiness>=55 else "Foundation needed","score_breakdown":{"academics":academic,"technical_skills":technical,"experience":experience,"certifications":certifications,"aptitude":profile["aptitude_score"],"interview":profile["interview_score"]},"skill_gap":{"matched":[title_skill(item) for item in matched],"missing":[title_skill(item) for item in missing],"priority":[title_skill(item) for item in priorities]},"eligibility":eligibility(profile,skills,requirements),"roadmap":[{"period":period,"topic":topic,"action":action} for period,topic,action in role["roadmap"]],"next_action":f"Learn {title_skill(priorities[0]) if priorities else 'portfolio depth'} next because it is the strongest remaining role signal.","reasons":reasons,"interview_prep":role["interview"]}


def analyze_resume(text:str,target_role:str)->dict:
    clean=text.lower(); detected=sorted(skill for skill in ROLE_CATALOG[target_role]["skills"] if skill in clean); sections={name:name in clean for name in ["education","project","skill","experience","certification"]}; score=min(100,round(len(detected)/len(ROLE_CATALOG[target_role]["skills"])*65+sum(sections.values())*7)); missing=sorted(set(ROLE_CATALOG[target_role]["skills"])-set(detected))[:4]; suggestions=[]
    if not sections["project"]: suggestions.append("Add a Projects section with contribution, stack, and measurable result.")
    if not sections["skill"]: suggestions.append("Add a Technical Skills section tailored to the target role.")
    if missing: suggestions.append(f"Include real project evidence for: {', '.join(title_skill(item) for item in missing)}.")
    return {"resume_strength":score,"detected_skills":[title_skill(item) for item in detected],"sections_found":sections,"suggestions":suggestions or ["Core sections are present; improve with measurable outcomes."],"missing_role_skills":[title_skill(item) for item in missing]}
