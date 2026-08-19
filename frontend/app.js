const api = "/api";
let roles = [];
let jobPage = 1;
let latestJobQuery = "Software Developer";
let latestJobLocation = "";
let latestJobCountry = "in";
let latestJobLevel = "";
const $ = (selector) => document.querySelector(selector);
const split = (value) => value.split(",").map((item) => item.trim()).filter(Boolean);
const escape = (value = "") => { const node = document.createElement("span"); node.textContent = String(value); return node.innerHTML; };
const title = (value = "") => value.replace(/\b\w/g, (character) => character.toUpperCase());

async function request(path, options = {}) {
  const response = await fetch(`${api}${path}`, options);
  if (response.status === 401) { window.location.href = "/login"; throw new Error("Your session ended. Please sign in again."); }
  const data = await response.json();
  if (!response.ok) throw new Error(Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join(" ") : (data.detail || "Request failed."));
  return data;
}
function showMessage(element, text = "") { element.hidden = !text; element.textContent = text; }
function changeView() {
  const id = window.location.hash.slice(1) || "home";
  const active = document.getElementById(id) ? id : "home";
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === active));
  document.querySelectorAll("[data-view]").forEach((link) => link.classList.toggle("active", link.dataset.view === active));
  window.scrollTo({ top: 0, behavior: "smooth" });
}
function listItems(element, values) { element.replaceChildren(); values.forEach((value) => { const item = document.createElement("li"); item.textContent = value; element.append(item); }); }
function chips(element, values) { element.replaceChildren(); (values.length ? values : ["No matching skills detected"]).forEach((value) => { const chip = document.createElement("span"); chip.textContent = value; element.append(chip); }); }

function jobCard(job) {
  const card = document.createElement("article"); card.className = "job-card";
  const published = job.published_at ? new Date(job.published_at).toLocaleDateString() : "Current listing";
  const skills = job.skills?.slice(0, 7).map((skill) => `<span>${escape(title(skill))}</span>`).join("") || "";
  const match = job.match_percentage == null ? "" : `<p class="match">Your skill match: ${job.match_percentage}%</p>`;
  const link = job.url ? `<a class="source-link" href="${escape(job.url)}" target="_blank" rel="noreferrer">Open live listing →</a>` : "";
  card.innerHTML = `<div class="job-top"><span>${escape(job.seniority || "Role")}</span><span>${escape(published)}</span></div><h3>${escape(job.title)}</h3><p class="company">${escape(job.company)}</p><p class="location">${escape(job.location)}</p><p class="description">${escape(job.description || "Skills are extracted from the live listing where available.")}</p><div class="chips">${skills}</div>${match}${link}`;
  return card;
}
function renderJobs(jobs, append = false) {
  const list = $("#job-list"); if (!append) list.replaceChildren();
  if (!jobs.length && !append) list.innerHTML = '<p class="source-note">No live listings matched this search. Try a broader job title or another location.</p>';
  jobs.forEach((job) => list.append(jobCard(job)));
}
async function searchJobs(page = 1, append = false) {
  const params = new URLSearchParams({ query: latestJobQuery, country: latestJobCountry, page: String(page) });
  if (latestJobLocation) params.set("location", latestJobLocation);
  if (latestJobLevel) params.set("level", latestJobLevel);
  const result = await request(`/jobs?${params}`); const data = result.data;
  renderJobs(data.jobs, append);
  $("#jobs-meta").textContent = data.live ? `${data.provider} · ${data.jobs.length} current listings${data.total_results ? ` · ${data.total_results} results reported` : ""}${data.notice ? ` · ${data.notice}` : ""}` : (data.error || "Live jobs unavailable.");
  $("#provider-text").textContent = data.live ? `Live opportunities via ${data.provider}` : "Live provider unavailable";
  $("#load-more").hidden = !data.live || !data.jobs.length || data.provider !== "Adzuna";
  jobPage = page;
}

function profilePayload() {
  return { name: $("#name").value, degree: $("#degree").value, branch: $("#branch").value, graduation_year: Number($("#graduation-year").value), cgpa: Number($("#cgpa").value), backlogs: Number($("#backlogs").value), technical_skills: split($("#technical-skills").value), soft_skills: split($("#soft-skills").value), certifications: split($("#certifications").value), projects: Number($("#projects").value), internships: Number($("#internships").value), aptitude_score: Number($("#aptitude").value), interview_score: Number($("#interview").value), target_role: $("#target-role").value };
}
function renderAnalysis(payload) {
  const { profile, analysis } = payload;
  $("#analysis-title").textContent = `${profile.target_role} readiness`;
  $("#readiness-score").textContent = `${analysis.readiness_score}%`;
  $("#academic-score").textContent = `${analysis.score_breakdown.academics}%`;
  $("#technical-score").textContent = `${analysis.score_breakdown.technical_skills}%`;
  $("#experience-score").textContent = `${analysis.score_breakdown.experience}%`;
  $("#interview-score").textContent = `${analysis.score_breakdown.interview}%`;
  $("#source-note").textContent = `Skill evidence source: ${analysis.skill_gap.source}. ${analysis.job_source.live ? `Live jobs retrieved through ${analysis.job_source.provider}.` : (analysis.job_source.error || "No live listings were available during analysis.")}`;
  $("#next-action").textContent = analysis.next_action;
  listItems($("#reason-list"), analysis.reasons);
  const skillList = $("#skill-list"); skillList.replaceChildren();
  const matched = new Set(analysis.skill_gap.matched);
  [...analysis.skill_gap.matched, ...analysis.skill_gap.missing].forEach((skill) => { const chip = document.createElement("span"); chip.className = `skill ${matched.has(skill) ? "match" : "gap"}`; chip.innerHTML = `${escape(skill)} <b>${matched.has(skill) ? "match" : "gap"}</b>`; skillList.append(chip); });
  const roadmap = $("#roadmap-list"); roadmap.replaceChildren(); analysis.roadmap.forEach((item) => { const row = document.createElement("li"); row.innerHTML = `<b>${escape(item.period)} · ${escape(item.topic)}</b>${escape(item.action)}`; roadmap.append(row); });
  listItems($("#interview-list"), analysis.interview_prep);
  const companies = $("#eligibility-list"); companies.replaceChildren();
  if (!analysis.eligibility.length) companies.innerHTML = '<p class="source-note">No verified employer rules are registered for this exact role. This prevents JobFit from making up eligibility requirements.</p>';
  analysis.eligibility.forEach((item) => { const card = document.createElement("article"); card.className = "eligibility-card"; const state = item.status === "Eligible" ? "eligible" : item.status === "Almost Eligible" ? "almost" : "not"; card.innerHTML = `<div class="eligibility-head"><h4>${escape(item.company)}</h4><span class="tag ${state}">${escape(item.status)}</span></div><p>Required: ${item.required_skills.map(escape).join(", ")}</p><p>${[...item.reasons, ...item.warnings].map(escape).join(" · ") || "All verified requirements met."}</p><a class="source-link" href="${escape(item.source_url)}" target="_blank" rel="noreferrer">Official criteria source →</a>`; companies.append(card); });
  $("#analysis-results").hidden = false;
  $("#analysis-results").scrollIntoView({ behavior: "smooth", block: "start" });
  if (analysis.recommended_jobs.length) { renderJobs(analysis.recommended_jobs); $("#jobs-meta").textContent = `Recommended live opportunities for ${profile.target_role}`; }
}

async function initializeUser() {
  const data = await request("/auth/me"); if (!data.user) { window.location.href = "/login"; return; }
  $("#user-name").textContent = data.user.name; $("#user-email").textContent = data.user.email || "Google account";
  if (data.user.picture) { const image = $("#user-picture"); image.src = data.user.picture; image.hidden = false; }
}
async function initializeRoles() {
  roles = (await request("/role-suggestions")).data;
  const list = $("#role-suggestions"); list.innerHTML = roles.map((role) => `<option value="${escape(role)}"></option>`).join("");
  $("#target-role").value = "Software Developer"; $("#resume-role").value = "Software Developer";
}

$("#profile-form").addEventListener("submit", async (event) => { event.preventDefault(); const error = $("#profile-error"); showMessage(error); if (!event.currentTarget.reportValidity()) return; const button = $("#analyze-button"); button.disabled = true; button.textContent = "Analyzing live evidence…"; try { renderAnalysis(await request("/career/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(profilePayload()) })); } catch (err) { showMessage(error, err.message); } finally { button.disabled = false; button.innerHTML = 'Run evidence analysis <span>→</span>'; } });
$("#job-form").addEventListener("submit", (event) => { event.preventDefault(); latestJobQuery = $("#job-query").value.trim(); latestJobLocation = $("#job-location").value.trim(); latestJobCountry = $("#job-country").value; latestJobLevel = $("#job-level").value; if (latestJobQuery) searchJobs(1).catch((err) => { $("#jobs-meta").textContent = err.message; }); });
$("#load-more").addEventListener("click", () => searchJobs(jobPage + 1, true).catch((err) => { $("#jobs-meta").textContent = err.message; }));
$("#resume-form").addEventListener("submit", async (event) => { event.preventDefault(); const error = $("#resume-error"); showMessage(error); const file = $("#resume-file").files[0]; if (!file) return showMessage(error, "Choose a PDF or TXT résumé first."); const form = new FormData(); form.append("file", file); form.append("target_role", $("#resume-role").value); try { const result = await request("/resume/analyze", { method: "POST", body: form }); $("#resume-score").textContent = `${result.data.resume_strength}%`; $("#resume-source").textContent = `Compared against ${result.data.comparison_source}`; chips($("#resume-skills"), result.data.detected_skills); listItems($("#resume-suggestions"), result.data.suggestions); $("#resume-results").hidden = false; } catch (err) { showMessage(error, err.message); } });
$("#logout").addEventListener("click", async () => { await fetch("/auth/logout", { method: "POST" }); window.location.href = "/login"; });
$("#mobile-menu").addEventListener("click", () => document.querySelector(".sidebar").scrollIntoView({ behavior: "smooth" }));
window.addEventListener("hashchange", changeView);
(async () => { try { await initializeUser(); await initializeRoles(); changeView(); await searchJobs(); } catch (err) { $("#provider-text").textContent = err.message; } })();
