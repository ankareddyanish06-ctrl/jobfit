const api = "/api";
let roles = [];
let activeRole = "";
const $ = (selector) => document.querySelector(selector);
const splitValues = (value) => value.split(",").map((item) => item.trim()).filter(Boolean);
const safe = (value) => { const node = document.createElement("span"); node.textContent = value; return node.innerHTML; };
const money = (amount) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount);

function optionMarkup() { return roles.map((role) => `<option value="${role.id}">${safe(role.title)}</option>`).join(""); }
function message(element, text = "") { element.textContent = text; element.hidden = !text; }
function listItems(element, values, className = "") { element.replaceChildren(); values.forEach((value) => { const li = document.createElement("li"); if (className) li.className = className; li.textContent = value; element.append(li); }); }
function chips(element, values) { element.replaceChildren(); if (!values.length) values = ["No role skills found yet"] ; values.forEach((value) => { const tag = document.createElement("span"); tag.textContent = value; element.append(tag); }); }

async function request(path, options) {
  const response = await fetch(`${api}${path}`, options);
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join(" ") : data.detail;
    throw new Error(detail || "Something went wrong. Please try again.");
  }
  return data;
}

async function loadRoles() {
  const data = await request("/roles");
  roles = data.data;
  $("#target-role").innerHTML = optionMarkup();
  $("#job-role").innerHTML = '<option value="">All roles</option>' + optionMarkup();
  activeRole = roles[0]?.id || "";
  $("#target-role").value = activeRole;
}

function profilePayload() {
  return {
    name: $("#name").value, degree: $("#degree").value, branch: $("#branch").value,
    graduation_year: Number($("#graduation-year").value), cgpa: Number($("#cgpa").value),
    backlogs: Number($("#backlogs").value), technical_skills: splitValues($("#technical-skills").value),
    soft_skills: splitValues($("#soft-skills").value), certifications: splitValues($("#certifications").value),
    projects: Number($("#projects").value), internships: Number($("#internships").value),
    aptitude_score: Number($("#aptitude").value), interview_score: Number($("#interview").value), target_role: $("#target-role").value,
  };
}

function renderAnalysis(result) {
  const { profile, analysis } = result;
  activeRole = profile.target_role;
  $("#dashboard-name").textContent = `${profile.name}'s ${analysis.role.title} plan`;
  $("#readiness-score").textContent = `${analysis.readiness_score}%`;
  $("#readiness-label").textContent = analysis.readiness_label;
  $("#technical-score").textContent = `${analysis.score_breakdown.technical_skills}%`;
  $("#aptitude-score").textContent = `${analysis.score_breakdown.aptitude}%`;
  $("#interview-score").textContent = `${analysis.score_breakdown.interview}%`;
  $("#next-action").textContent = analysis.next_action;
  listItems($("#reason-list"), analysis.reasons);
  const salary = analysis.salary_estimate;
  $("#salary-range").textContent = salary.available ? `${money(salary.minimum)} – ${money(salary.maximum)}` : "Live salary unavailable";
  $("#salary-note").textContent = salary.available ? `Current range from ${salary.source}` : salary.reason;
  $("#roadmap-role").textContent = `${analysis.role.title} roadmap`;
  const skillTable = $("#skill-table"); skillTable.replaceChildren();
  const matched = new Set(analysis.skill_gap.matched);
  [...analysis.skill_gap.matched, ...analysis.skill_gap.missing].forEach((skill) => {
    const row = document.createElement("div"); row.className = "skill-row";
    row.innerHTML = `<span>${safe(skill)}</span><b class="status ${matched.has(skill) ? "match" : "gap"}">${matched.has(skill) ? "Matched" : "Priority gap"}</b>`;
    skillTable.append(row);
  });
  const roadmap = $("#roadmap-list"); roadmap.replaceChildren(); analysis.roadmap.forEach((item) => { const li = document.createElement("li"); li.innerHTML = `<b>${safe(item.period)} · ${safe(item.topic)}</b>${safe(item.action)}`; roadmap.append(li); });
  listItems($("#interview-list"), analysis.interview_prep);
  const eligibility = $("#eligibility-list"); eligibility.replaceChildren();
  if (!analysis.eligibility.length) eligibility.innerHTML = "<p class=\"muted\">No verified employer criteria are registered for this role yet. Add criteria only from an official company hiring source.</p>";
  analysis.eligibility.forEach((item) => {
    const card = document.createElement("article"); card.className = "eligibility";
    const statusClass = item.status === "Eligible" ? "eligible" : item.status === "Almost Eligible" ? "almost" : "not";
    const notes = [...item.reasons, ...item.warnings];
    const source = item.source_url ? `<a class="source-link" href="${safe(item.source_url)}" target="_blank" rel="noreferrer">Verified source</a>` : "";
    card.innerHTML = `<div class="eligibility-top"><h4>${safe(item.company)}</h4><span class="badge ${statusClass}">${safe(item.status)}</span></div><p>Required: ${item.required_skills.map(safe).join(", ")}</p>${notes.length ? `<p>${notes.map(safe).join(" · ")}</p>` : "<p>You meet the listed criteria.</p>"}${source}`;
    eligibility.append(card);
  });
  renderRecommendedJobs(analysis.recommended_jobs);
  $("#dashboard").hidden = false;
  $("#dashboard").scrollIntoView({ behavior: "smooth", block: "start" });
  loadHistory();
}

function renderRecommendedJobs(jobs) {
  const list = $("#job-list"); list.replaceChildren();
  jobs.forEach((job) => list.append(jobCard(job)));
}
function jobCard(job) {
  const card = document.createElement("article"); card.className = "job";
  const tags = (job.skills || []).map(safe).join(", ");
  const published = job.published_at ? new Date(job.published_at).toLocaleDateString() : "Live listing";
  const match = job.match_percentage === undefined ? "" : `<p class="match">Profile match: ${job.match_percentage}%</p>`;
  const missing = job.missing_skills?.length ? `<p>Build next: ${job.missing_skills.map(safe).join(", ")}</p>` : "";
  const apply = job.url ? `<a class="source-link" href="${safe(job.url)}" target="_blank" rel="noreferrer">View live listing →</a>` : "";
  card.innerHTML = `<div class="job-top"><span class="badge almost">${safe(job.type)}</span><span class="subtle">${safe(published)}</span></div><h3>${safe(job.title)}</h3><div class="meta"><span>${safe(job.company)}</span><span>${safe(job.location)}</span></div><p>${tags || "Skills not specified in listing"}</p>${match}${missing}${apply}`;
  return card;
}

async function loadJobs(event) {
  if (event) event.preventDefault();
  const params = new URLSearchParams();
  [["role", $("#job-role").value], ["query", $("#job-query").value], ["location", $("#job-location").value]].forEach(([key, value]) => { if (value.trim()) params.set(key, value.trim()); });
  const response = await request(`/jobs?${params}`); const source = response.data; const list = $("#job-list"); list.replaceChildren();
  if (!source.live) { list.innerHTML = `<p class="muted">${safe(source.error || "Live jobs are currently unavailable.")}</p>`; return; }
  if (!source.jobs.length) { list.innerHTML = '<p class="muted">No live jobs match those filters. Try another role or location.</p>'; return; }
  source.jobs.forEach((job) => list.append(jobCard(job)));
}
async function analyzeResume(event) {
  event.preventDefault(); const error = $("#resume-error"); message(error);
  const file = $("#resume-file").files[0]; if (!file) return message(error, "Choose a PDF or TXT résumé first.");
  const body = new FormData(); body.append("file", file); body.append("target_role", activeRole || $("#target-role").value);
  try {
    const result = await request("/resume/analyze", { method: "POST", body }); const data = result.data;
    $("#resume-score").textContent = `${data.resume_strength}%`; chips($("#resume-skills"), data.detected_skills); listItems($("#resume-suggestions"), data.suggestions);
    $("#resume-results").hidden = false;
  } catch (err) { message(error, err.message); }
}

async function loadMarket() {
  const data = (await request("/market")).data; const content = $("#market-content"); content.replaceChildren();
  if (!data.live) { content.innerHTML = '<p class="muted">Live market data is temporarily unavailable.</p>'; return; }
  const stats = [["Live jobs sampled", data.jobs_sampled], ["Data source", data.source], ["Last refreshed", new Date(data.updated_at).toLocaleTimeString()], ["Locations", data.locations.join(", ") || "Not listed"]];
  stats.forEach(([label, value]) => { const card = document.createElement("article"); card.className = "market-stat"; card.innerHTML = `<span>${safe(label)}</span><strong>${safe(value)}</strong>`; content.append(card); });
  const skills = document.createElement("article"); skills.className = "market-stat"; skills.style.gridColumn = "1 / -1"; skills.innerHTML = `<span>Skills detected in currently retrieved listings</span><div class="chips">${data.top_skills.map((item) => `<span>${safe(item.skill)} · ${item.openings} listing${item.openings > 1 ? "s" : ""}</span>`).join("")}</div>`; content.append(skills);
}
async function loadHistory() {
  const data = await request("/career/history?limit=8"); const body = $("#history-body"); body.replaceChildren();
  if (!data.data.length) { body.innerHTML = '<tr><td colspan="4" class="muted">No full assessments saved yet.</td></tr>'; return; }
  data.data.forEach((item) => { const row = document.createElement("tr"); const role = roles.find((roleItem) => roleItem.id === item.target_role)?.title || item.target_role; row.innerHTML = `<td>${safe(item.student_name)}</td><td>${safe(role)}</td><td>${Math.round(item.readiness_score)}%</td><td>${new Date(item.timestamp).toLocaleDateString()}</td>`; body.append(row); });
}

$("#profile-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const error = $("#profile-error"); message(error); if (!event.currentTarget.reportValidity()) return;
  const button = $("#analyze-button"); button.disabled = true; button.textContent = "Analyzing your profile…";
  try { renderAnalysis(await request("/career/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(profilePayload()) })); }
  catch (err) { message(error, err.message); }
  finally { button.disabled = false; button.innerHTML = 'Generate career analysis <span aria-hidden="true">→</span>'; }
});
$("#job-filter").addEventListener("submit", (event) => loadJobs(event).catch(console.error));
$("#resume-form").addEventListener("submit", analyzeResume);
$("#refresh-market").addEventListener("click", () => loadMarket().catch(console.error));
$("#refresh-history").addEventListener("click", () => loadHistory().catch(console.error));
$("#start-over").addEventListener("click", () => $("#assessment").scrollIntoView({ behavior: "smooth" }));

(async () => { try { await loadRoles(); await Promise.all([loadJobs(), loadMarket(), loadHistory()]); } catch (error) { message($("#profile-error"), "Could not load the platform data. Refresh the page to retry."); } })();
