"""FastAPI server for JobFit with live job data and verified company criteria."""
from __future__ import annotations
import os, secrets
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from backend.career_engine import ROLE_CATALOG, analyze_profile, analyze_resume, normalize_skills, role_options
from backend.database import get_analysis_history, get_requirements, init_db, save_analysis, upsert_requirement
from backend.live_data import live_jobs, live_market, live_salary
FRONTEND_DIR=Path(__file__).resolve().parent.parent/"frontend"
@asynccontextmanager
async def lifespan(_:FastAPI): init_db(); yield
app=FastAPI(title="JobFit Live Career Intelligence API",version="3.0.0",lifespan=lifespan)
origins=[item.strip() for item in os.getenv("ALLOWED_ORIGINS","").split(",") if item.strip()]
if origins: app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=["GET","POST"],allow_headers=["Content-Type","X-Admin-Key"])
def clean_list(values:list[str])->list[str]:
 result=[]; seen=set()
 for value in values:
  item=value.strip(); key=item.lower()
  if item and len(item)<=60 and key not in seen: result.append(item); seen.add(key)
 return result
class StudentProfile(BaseModel):
 name:str=Field(min_length=2,max_length=80); degree:str=Field(min_length=2,max_length=60); branch:str=Field(min_length=2,max_length=20); graduation_year:int=Field(ge=2020,le=2035); cgpa:float=Field(ge=0,le=10); backlogs:int=Field(ge=0,le=20); technical_skills:list[str]=Field(min_length=1,max_length=40); soft_skills:list[str]=Field(default_factory=list,max_length=20); certifications:list[str]=Field(default_factory=list,max_length=20); projects:int=Field(ge=0,le=30); internships:int=Field(ge=0,le=15); aptitude_score:float=Field(ge=0,le=100); interview_score:float=Field(ge=0,le=100); target_role:str
 @field_validator("name","degree")
 @classmethod
 def space(cls,v): return " ".join(v.split())
 @field_validator("branch")
 @classmethod
 def branch(cls,v): return v.strip().upper()
 @field_validator("target_role")
 @classmethod
 def role(cls,v):
  if v not in ROLE_CATALOG: raise ValueError("Select a valid target role.")
  return v
 @field_validator("technical_skills","soft_skills","certifications")
 @classmethod
 def lists(cls,v,info):
  output=clean_list(v)
  if info.field_name=="technical_skills" and not output: raise ValueError("Add at least one technical skill.")
  return output
class ResumeTextRequest(BaseModel):
 text:str=Field(min_length=30,max_length=100000); target_role:str
 @field_validator("target_role")
 @classmethod
 def role(cls,v):
  if v not in ROLE_CATALOG: raise ValueError("Select a valid target role.")
  return v
class CompanyRequirement(BaseModel):
 company:str=Field(min_length=2,max_length=100); target_role:str; min_cgpa:float=Field(ge=0,le=10); max_backlogs:int=Field(ge=0,le=20); branches:list[str]=Field(default_factory=list); skills:list[str]=Field(default_factory=list); graduation_year:int|None=Field(default=None,ge=2020,le=2035); source_url:str=Field(min_length=10,max_length=500)
 @field_validator("target_role")
 @classmethod
 def role(cls,v):
  if v not in ROLE_CATALOG: raise ValueError("Select a valid target role.")
  return v
 @field_validator("branches","skills")
 @classmethod
 def lists(cls,v): return clean_list(v)
@app.get("/api/health")
async def health(): return {"status":"ok","service":"jobfit-live-career-intelligence","version":"3.0.0"}
@app.get("/api/roles")
async def roles(): return {"data":role_options()}
@app.post("/api/career/analyze")
async def analyze(profile:StudentProfile):
 data=profile.model_dump(); analysis=analyze_profile(data,get_requirements(profile.target_role)); analysis["salary_estimate"]=await live_salary(analysis["role"]["title"]); live=await live_jobs(role=profile.target_role,skills=normalize_skills(profile.technical_skills)); analysis["recommended_jobs"]=live["jobs"][:6]; analysis["job_source"]={key:live.get(key) for key in ["source","source_url","live","updated_at","error"]}; analysis["id"]=save_analysis(data,analysis)
 return {"success":True,"profile":data,"analysis":analysis,"disclaimer":"Readiness is an educational profile score, not a placement probability or hiring decision. Jobs are retrieved from the listed live provider; employer rules only appear when a verified source has been registered."}
@app.get("/api/career/history")
async def career_history(limit:int=Query(8,ge=1,le=20)): return {"success":True,"data":get_analysis_history(limit)}
@app.get("/api/jobs")
async def jobs(role:str|None=None,location:str|None=None,query:str|None=None,skills:str|None=None):
 if role and role not in ROLE_CATALOG: raise HTTPException(422,"Unknown role filter.")
 return {"success":True,"data":await live_jobs(role,location,query,normalize_skills(skills.split(",")) if skills else None)}
@app.get("/api/market")
async def market(): return {"success":True,"data":await live_market()}
@app.get("/api/company-requirements")
async def company_requirements(role:str):
 if role not in ROLE_CATALOG: raise HTTPException(422,"Unknown role.")
 return {"success":True,"data":get_requirements(role)}
@app.post("/api/company-requirements")
async def register_requirement(item:CompanyRequirement,x_admin_key:str|None=Header(default=None)):
 expected=os.getenv("ADMIN_API_KEY")
 if not expected or not x_admin_key or not secrets.compare_digest(x_admin_key,expected): raise HTTPException(403,"Admin authorization is required to register verified company criteria.")
 return {"success":True,"id":upsert_requirement(item.model_dump())}
@app.post("/api/resume/analyze-text")
async def resume_text(request:ResumeTextRequest): return {"success":True,"data":analyze_resume(request.text,request.target_role)}
@app.post("/api/resume/analyze")
async def resume_file(target_role:str=Form(...),file:UploadFile=File(...)):
 if target_role not in ROLE_CATALOG: raise HTTPException(422,"Select a valid target role.")
 if not file.filename or Path(file.filename).suffix.lower() not in {".pdf",".txt"}: raise HTTPException(422,"Upload a PDF or TXT résumé.")
 content=await file.read()
 if len(content)>4*1024*1024: raise HTTPException(413,"Résumé must be smaller than 4 MB.")
 try:
  text="\n".join(page.extract_text() or "" for page in __import__("pypdf").PdfReader(BytesIO(content)).pages) if file.filename.lower().endswith(".pdf") else content.decode("utf-8",errors="ignore")
 except Exception as exc: raise HTTPException(422,"The résumé could not be read. Upload a text-based PDF or TXT file.") from exc
 if len(text.strip())<30: raise HTTPException(422,"The résumé does not contain enough extractable text.")
 return {"success":True,"filename":file.filename,"data":analyze_resume(text,target_role)}
@app.get("/")
async def index(): return FileResponse(FRONTEND_DIR/"index.html")
app.mount("/",StaticFiles(directory=FRONTEND_DIR),name="frontend")
