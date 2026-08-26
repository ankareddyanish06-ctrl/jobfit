/**
 * JobFit — Live IT Career Intelligence Platform
 * Client Application Logic & Black 3D Visual Controller
 */

const API_BASE = "/api";
let availableRoles = [];
let currentPage = 1;
let currentQuery = "Software Developer";
let currentLocation = "";
let currentCountry = "in";
let currentLevel = "";
let userAnalyzedSkills = new Set();

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

const escapeHtml = (text = "") => {
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
};

const titleCase = (text = "") => {
  return String(text).replace(/\b\w/g, (char) => char.toUpperCase());
};

const splitValues = (str = "") => {
  return str
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
};

// Toast notification helper
function showToast(message, type = "info") {
  const container = $("#toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// API Request Wrapper
async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, options);
  if (response.status === 401) {
    window.location.href = "/login";
    throw new Error("Your session has expired. Redirecting to login...");
  }
  const json = await response.json();
  if (!response.ok) {
    const errorMsg = Array.isArray(json.detail)
      ? json.detail.map((e) => e.msg).join(" ")
      : (json.detail || "Request failed.");
    throw new Error(errorMsg);
  }
  return json;
}

// View Controller & Navigation
function handleViewChange() {
  const hash = window.location.hash.slice(1) || "home";
  const targetId = document.getElementById(hash) ? hash : "home";

  $$(".view").forEach((view) => {
    view.classList.toggle("active", view.id === targetId);
  });

  $$("[data-view]").forEach((link) => {
    link.classList.toggle("active", link.dataset.view === targetId);
  });

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Interactive Starfield Canvas Particle System
(function initStarfield() {
  const canvas = document.getElementById("starfield-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let stars = [];
  const count = 80;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  for (let i = 0; i < count; i++) {
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      size: Math.random() * 1.8 + 0.4,
      alpha: Math.random() * 0.7 + 0.2,
      dx: (Math.random() - 0.5) * 0.3,
      dy: (Math.random() - 0.5) * 0.3,
    });
  }

  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const star of stars) {
      star.x += star.dx;
      star.y += star.dy;
      if (star.x < 0) star.x = canvas.width;
      if (star.x > canvas.width) star.x = 0;
      if (star.y < 0) star.y = canvas.height;
      if (star.y > canvas.height) star.y = 0;

      ctx.beginPath();
      ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(200, 255, 0, ${star.alpha})`;
      ctx.shadowBlur = star.size * 5;
      ctx.shadowColor = "#c8ff00";
      ctx.fill();
    }
    requestAnimationFrame(render);
  }
  render();
})();

// Mouse Parallax 3D Tilt Effect on Cards
(function init3DTilt() {
  document.addEventListener("mousemove", (e) => {
    const tiltElements = $$("[data-tilt]");
    const { clientX, clientY } = e;
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;

    tiltElements.forEach((el) => {
      const rect = el.getBoundingClientRect();
      if (
        rect.top < window.innerHeight &&
        rect.bottom > 0 &&
        rect.left < window.innerWidth &&
        rect.right > 0
      ) {
        const xOffset = (clientX - (rect.left + rect.width / 2)) / 35;
        const yOffset = (clientY - (rect.top + rect.height / 2)) / 35;
        el.style.transform = `perspective(1000px) rotateY(${xOffset}deg) rotateX(${-yOffset}deg)`;
      }
    });
  });
})();

// User Profile & Authentication Init
async function initUser() {
  try {
    const res = await apiRequest("/auth/me");
    if (!res.user) {
      window.location.href = "/login";
      return;
    }
    $("#user-name").textContent = res.user.name || "JobFit User";
    $("#user-email").textContent = res.user.email || "Session Active";
    if (res.user.picture) {
      const pic = $("#user-picture");
      pic.src = res.user.picture;
      pic.hidden = false;
      $("#user-avatar-fallback").hidden = true;
    } else {
      const initial = (res.user.name || "U").charAt(0).toUpperCase();
      $("#user-avatar-fallback").textContent = initial;
    }
  } catch (err) {
    console.error("Auth check failed:", err);
  }
}

// Role Suggestions & Autocomplete
async function initRoles() {
  try {
    const res = await apiRequest("/role-suggestions");
    availableRoles = res.data || [];
    const datalist = $("#role-suggestions");
    if (datalist) {
      datalist.innerHTML = availableRoles
        .map((role) => `<option value="${escapeHtml(role)}"></option>`)
        .join("");
    }
  } catch (err) {
    console.warn("Could not load role suggestions:", err);
  }
}

// Job Card HTML Builder
function buildJobCard(job) {
  const card = document.createElement("article");
  card.className = "job-card";

  const published = job.published_at
    ? new Date(job.published_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "Current listing";

  const skillsHtml =
    job.skills && job.skills.length
      ? job.skills
          .slice(0, 6)
          .map((s) => `<span>${escapeHtml(titleCase(s))}</span>`)
          .join("")
      : "<span>General IT</span>";

  const matchHtml =
    job.match_percentage != null
      ? `<span class="match-pill">Skill Match: ${job.match_percentage}%</span>`
      : "";

  const salaryHtml = job.salary_formatted
    ? `<span class="salary-tag">${escapeHtml(job.salary_formatted)}</span>`
    : "";

  const linkHtml = job.url
    ? `<a class="source-link" href="${escapeHtml(job.url)}" target="_blank" rel="noreferrer">Apply / View Live Listing ↗</a>`
    : "";

  card.innerHTML = `
    <div>
      <div class="job-header-row">
        <span class="job-seniority-badge">${escapeHtml(job.seniority || "All Levels")}</span>
        <span class="job-time">${escapeHtml(published)}</span>
      </div>
      <h3>${escapeHtml(job.title)}</h3>
      <p class="job-company">🏢 ${escapeHtml(job.company)}</p>
      <p class="job-location">📍 ${escapeHtml(job.location)}</p>
      ${salaryHtml}
      <p class="job-desc">${escapeHtml(job.description || "Detailed skill requirements extracted from live listing.")}</p>
      <div class="chips">${skillsHtml}</div>
    </div>
    <div class="job-footer-row">
      ${matchHtml}
      ${linkHtml}
    </div>
  `;
  return card;
}

// Render Job Openings
function renderJobsList(jobs, containerId = "#job-list", append = false) {
  const container = $(containerId);
  if (!container) return;

  if (!append) container.replaceChildren();

  if (!jobs || !jobs.length) {
    if (!append) {
      container.innerHTML = `
        <div class="surface" style="grid-column: 1/-1; text-align: center; padding: 2.5rem;">
          <p class="kicker">NO ACTIVE MATCHES</p>
          <p style="color: var(--text-muted); margin: 0.5rem 0 0;">
            No live job listings matched your current query. Try searching for a broader title (e.g. "Software Developer", "Data Analyst") or switching locations.
          </p>
        </div>
      `;
    }
    return;
  }

  jobs.forEach((job) => container.appendChild(buildJobCard(job)));
}

// Fetch Live Jobs
async function fetchLiveJobs(page = 1, append = false) {
  const params = new URLSearchParams({
    query: currentQuery,
    country: currentCountry,
    page: String(page),
  });

  if (currentLocation) params.set("location", currentLocation);
  if (currentLevel) params.set("level", currentLevel);

  const result = await apiRequest(`/jobs?${params}`);
  const data = result.data;

  renderJobsList(data.jobs, "#job-list", append);

  const metaText = data.live
    ? `${data.provider} · ${data.jobs.length} current listings displayed${data.total_results ? ` (${data.total_results} total reported)` : ""}${data.notice ? ` · ${data.notice}` : ""}`
    : (data.error || "Live jobs unavailable.");

  $("#jobs-meta").textContent = metaText;
  $("#provider-text").textContent = data.live
    ? `Live job stream active via ${data.provider}`
    : "Live provider currently unavailable";
  $("#sidebar-provider-status").textContent = data.live
    ? `Live: ${data.provider}`
    : "Offline Stream";

  const loadMoreBtn = $("#load-more");
  if (loadMoreBtn) {
    loadMoreBtn.hidden = !data.live || !data.jobs.length || data.jobs.length < 10;
  }
  currentPage = page;
}

// Profile Payload Builder
function getProfileData() {
  return {
    name: $("#name").value.trim(),
    degree: $("#degree").value.trim(),
    branch: $("#branch").value.trim(),
    graduation_year: Number($("#graduation-year").value),
    cgpa: Number($("#cgpa").value),
    backlogs: Number($("#backlogs").value),
    technical_skills: splitValues($("#technical-skills").value),
    soft_skills: splitValues($("#soft-skills").value),
    certifications: splitValues($("#certifications").value),
    projects: Number($("#projects").value),
    internships: Number($("#internships").value),
    aptitude_score: Number($("#aptitude").value),
    interview_score: Number($("#interview").value),
    target_role: $("#target-role").value.trim(),
  };
}

// Render Profile Analysis Results
function renderAnalysisResults(data) {
  const { profile, analysis } = data;

  // Track skills for highlighting in live job search
  userAnalyzedSkills = new Set(
    (analysis.skill_gap.matched || []).map((s) => s.toLowerCase())
  );

  $("#analysis-title").textContent = `${profile.target_role} Readiness Diagnostic`;
  $("#readiness-label").textContent = analysis.readiness_label;
  $("#readiness-score").textContent = `${analysis.readiness_score}%`;

  // Animate SVG circular progress ring
  const ring = $("#readiness-ring");
  if (ring) {
    const radius = ring.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (analysis.readiness_score / 100) * circumference;
    ring.style.strokeDasharray = `${circumference} ${circumference}`;
    ring.style.strokeDashoffset = offset;
  }

  // Score breakdown metrics
  const bd = analysis.score_breakdown;
  $("#academic-score").textContent = `${bd.academics}%`;
  $("#academic-bar").style.width = `${bd.academics}%`;

  $("#technical-score").textContent = `${bd.technical_skills}%`;
  $("#technical-bar").style.width = `${bd.technical_skills}%`;

  $("#experience-score").textContent = `${bd.experience}%`;
  $("#experience-bar").style.width = `${bd.experience}%`;

  $("#interview-score").textContent = `${bd.interview}%`;
  $("#interview-bar").style.width = `${bd.interview}%`;

  // Evidence Source Note
  $("#source-note").textContent = `Skill intelligence benchmark: ${analysis.skill_gap.source}. ${
    analysis.job_source && analysis.job_source.live
      ? `Live market opportunities verified via ${analysis.job_source.provider}.`
      : ""
  }`;

  // Next action and rationale
  $("#next-action").textContent = analysis.next_action;
  const reasonList = $("#reason-list");
  reasonList.replaceChildren();
  (analysis.reasons || []).forEach((reason) => {
    const li = document.createElement("li");
    li.textContent = reason;
    reasonList.appendChild(li);
  });

  // Skill Matrix
  const skillContainer = $("#skill-list");
  skillContainer.replaceChildren();
  const matchedSet = new Set((analysis.skill_gap.matched || []).map((s) => s.toLowerCase()));
  const prioritySet = new Set((analysis.skill_gap.priority || []).map((s) => s.toLowerCase()));

  [...(analysis.skill_gap.matched || []), ...(analysis.skill_gap.missing || [])].forEach((skill) => {
    const isMatch = matchedSet.has(skill.toLowerCase());
    const isPriority = prioritySet.has(skill.toLowerCase());
    const chip = document.createElement("span");
    chip.className = `skill-chip ${isMatch ? "match" : isPriority ? "priority" : "gap"}`;
    chip.innerHTML = `${escapeHtml(skill)} <small>${isMatch ? "✓ MATCH" : isPriority ? "★ PRIORITY GAP" : "GAP"}</small>`;
    skillContainer.appendChild(chip);
  });

  // 7-Week Sprint Roadmap
  const roadmapContainer = $("#roadmap-list");
  roadmapContainer.replaceChildren();
  (analysis.roadmap || []).forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `<b>${escapeHtml(item.period)} · ${escapeHtml(item.topic)}</b>${escapeHtml(item.action)}`;
    roadmapContainer.appendChild(li);
  });

  // Copy Roadmap Handler
  const copyBtn = $("#copy-roadmap-btn");
  if (copyBtn) {
    copyBtn.onclick = () => {
      const text = (analysis.roadmap || [])
        .map((r) => `### ${r.period}: ${r.topic}\n${r.action}`)
        .join("\n\n");
      navigator.clipboard.writeText(text);
      showToast("7-Week Roadmap copied to clipboard!", "success");
    };
  }

  // Targeted Interview Prompts
  const interviewContainer = $("#interview-list");
  interviewContainer.replaceChildren();
  (analysis.interview_prep || []).forEach((q) => {
    const li = document.createElement("li");
    li.textContent = q;
    interviewContainer.appendChild(li);
  });

  // Tailored Project Ideas
  const projectIdeasBox = $("#project-ideas-box");
  const projectIdeasList = $("#project-ideasList");
  if (projectIdeasBox && projectIdeasList) {
    if (analysis.project_ideas && analysis.project_ideas.length) {
      projectIdeasList.replaceChildren();
      analysis.project_ideas.forEach((p) => {
        const pCard = document.createElement("div");
        pCard.className = "project-idea-card";
        pCard.innerHTML = `
          <h4>🚀 ${escapeHtml(p.title)}</h4>
          <p>${escapeHtml(p.description)}</p>
        `;
        projectIdeasList.appendChild(pCard);
      });
      projectIdeasBox.hidden = false;
    } else {
      projectIdeasBox.hidden = true;
    }
  }

  // Verified Employer Eligibility
  const eligibilityContainer = $("#eligibility-list");
  eligibilityContainer.replaceChildren();

  if (!analysis.eligibility || !analysis.eligibility.length) {
    eligibilityContainer.innerHTML = `
      <p class="source-note" style="grid-column: 1/-1;">
        No official employer criteria are registered for this role yet. JobFit displays verified company criteria only when official criteria URLs are authenticated.
      </p>
    `;
  } else {
    analysis.eligibility.forEach((item) => {
      const card = document.createElement("article");
      card.className = "eligibility-card";
      const stateClass =
        item.status === "Eligible"
          ? "eligible"
          : item.status === "Almost Eligible"
          ? "almost"
          : "not";

      const reasonsText = [...(item.reasons || []), ...(item.warnings || [])].join(" · ") || "All criteria satisfied.";

      card.innerHTML = `
        <div class="eligibility-head">
          <h4>${escapeHtml(item.company)}</h4>
          <span class="tag ${stateClass}">${escapeHtml(item.status)}</span>
        </div>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0.4rem 0;">
          <strong>Target Skills:</strong> ${escapeHtml((item.required_skills || []).join(", "))}
        </p>
        <p style="font-size: 0.8rem; color: var(--text-dim); margin: 0.3rem 0;">
          ${escapeHtml(reasonsText)}
        </p>
        <a class="source-link" href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">
          Official Criteria Source ↗
        </a>
      `;
      eligibilityContainer.appendChild(card);
    });
  }

  // Recommended Live Roles
  const recJobs = analysis.recommended_jobs || [];
  $("#rec-jobs-title").textContent = `Real-time Openings Matching ${profile.target_role}`;
  renderJobsList(recJobs, "#recommended-job-list", false);

  const resultsSection = $("#analysis-results");
  resultsSection.hidden = false;
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  showToast("Profile evidence analysis complete!", "success");
}

// Sample Profile Autofill Helper
function autofillSampleProfile() {
  $("#name").value = "Anish Ankareddy";
  $("#degree").value = "B.Tech";
  $("#branch").value = "CSE";
  $("#graduation-year").value = 2026;
  $("#cgpa").value = 8.65;
  $("#backlogs").value = 0;
  $("#target-role").value = "Full Stack Developer";
  $("#technical-skills").value = "Python, JavaScript, TypeScript, React, Node.js, SQL, PostgreSQL, Docker, Git, REST API";
  $("#soft-skills").value = "Problem Solving, Agile Collaboration, System Design, Communication";
  $("#certifications").value = "AWS Certified Cloud Practitioner";
  $("#projects").value = 3;
  $("#internships").value = 1;
  $("#aptitude").value = 80;
  $("#interview").value = 75;
  showToast("Sample candidate profile loaded.", "info");
}

// Résumé ATS Analysis Renderer
function renderResumeResults(data, role) {
  $("#resume-score").textContent = `${data.resume_strength}%`;

  const ring = $("#resume-strength-ring");
  if (ring) {
    const radius = ring.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (data.resume_strength / 100) * circumference;
    ring.style.strokeDasharray = `${circumference} ${circumference}`;
    ring.style.strokeDashoffset = offset;
  }

  $("#resume-source").textContent = `Evaluated against ${data.comparison_source} for ${role}`;

  // Detected skills
  const skillsContainer = $("#resume-skills");
  skillsContainer.replaceChildren();
  if (data.detected_skills && data.detected_skills.length) {
    data.detected_skills.forEach((s) => {
      const chip = document.createElement("span");
      chip.textContent = s;
      skillsContainer.appendChild(chip);
    });
  } else {
    skillsContainer.innerHTML = "<small style='color:var(--text-dim);'>No recognizable technical skills found</small>";
  }

  // Missing critical keywords
  const missingContainer = $("#resume-missing-skills");
  missingContainer.replaceChildren();
  if (data.missing_role_skills && data.missing_role_skills.length) {
    data.missing_role_skills.forEach((s) => {
      const chip = document.createElement("span");
      chip.textContent = `+ ${s}`;
      missingContainer.appendChild(chip);
    });
  } else {
    missingContainer.innerHTML = "<small style='color:var(--text-dim);'>All primary role keywords detected!</small>";
  }

  // Section Health Checklist
  const checklistContainer = $("#resume-sections-checklist");
  checklistContainer.replaceChildren();
  const sectionLabels = {
    contact: "Contact Information",
    education: "Education & Degree",
    experience: "Experience / Internships",
    project: "Technical Projects",
    skill: "Technical Skills Matrix",
    certification: "Certifications & Credentials",
  };

  Object.entries(data.sections_found || {}).forEach(([sec, isPresent]) => {
    const li = document.createElement("li");
    li.className = isPresent ? "pass" : "fail";
    li.innerHTML = `<span>${isPresent ? "✓" : "✗"}</span> <span>${sectionLabels[sec] || sec}</span>`;
    checklistContainer.appendChild(li);
  });

  // Actionable Suggestions
  const suggestionsList = $("#resume-suggestions");
  suggestionsList.replaceChildren();
  (data.suggestions || []).forEach((sug) => {
    const li = document.createElement("li");
    li.textContent = sug;
    suggestionsList.appendChild(li);
  });

  $("#resume-results").hidden = false;
  $("#resume-results").scrollIntoView({ behavior: "smooth", block: "start" });
  showToast("Résumé ATS diagnostic complete.", "success");
}

/* ==========================================================================
   Event Listeners & Form Submissions
   ========================================================================== */

// Profile Form Submit
$("#profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = $("#profile-error");
  errorEl.hidden = true;

  const btn = $("#analyze-button");
  btn.disabled = true;
  btn.innerHTML = `<span>Evaluating evidence against live signals…</span>`;

  try {
    const payload = getProfileData();
    const result = await apiRequest("/career/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderAnalysisResults(result);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Run Evidence Analysis</span> <span class="arrow">→</span>`;
  }
});

// Autofill Sample Profile Button
$("#autofill-profile").addEventListener("click", autofillSampleProfile);

// Quick Role Chips Click
$("#quick-role-chips").addEventListener("click", (e) => {
  if (e.target && e.target.dataset.role) {
    const role = e.target.dataset.role;
    $("#target-role").value = role;
    $("#job-query").value = role;
    $("#resume-role").value = role;
    currentQuery = role;
    window.location.hash = "#analysis";
    showToast(`Target role set to: ${role}`, "info");
  }
});

// Live Job Search Form
$("#job-form").addEventListener("submit", (e) => {
  e.preventDefault();
  currentQuery = $("#job-query").value.trim() || "Software Developer";
  currentLocation = $("#job-location").value.trim();
  currentCountry = $("#job-country").value;
  currentLevel = $("#job-level").value;

  fetchLiveJobs(1, false).catch((err) => {
    $("#jobs-meta").textContent = err.message;
    showToast(err.message, "error");
  });
});

// Load More Jobs Button
$("#load-more").addEventListener("click", () => {
  fetchLiveJobs(currentPage + 1, true).catch((err) => {
    $("#jobs-meta").textContent = err.message;
    showToast(err.message, "error");
  });
});

// Résumé Dropzone & File Handling
const dropzone = $("#resume-dropzone");
const resumeFileInput = $("#resume-file");
const fileBadge = $("#selected-file-badge");

if (dropzone && resumeFileInput) {
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      resumeFileInput.files = e.dataTransfer.files;
      updateFileBadge(e.dataTransfer.files[0]);
    }
  });

  resumeFileInput.addEventListener("change", () => {
    if (resumeFileInput.files && resumeFileInput.files[0]) {
      updateFileBadge(resumeFileInput.files[0]);
    }
  });
}

function updateFileBadge(file) {
  if (fileBadge && file) {
    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
    fileBadge.textContent = `📎 ${file.name} (${sizeMb} MB)`;
    fileBadge.hidden = false;
  }
}

// Résumé Form Submit
$("#resume-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = $("#resume-error");
  errorEl.hidden = true;

  const file = resumeFileInput.files[0];
  if (!file) {
    errorEl.textContent = "Please upload or drop a PDF or TXT résumé file.";
    errorEl.hidden = false;
    return;
  }

  const role = $("#resume-role").value.trim() || "Software Developer";
  const btn = $("#resume-analyze-btn");
  btn.disabled = true;
  btn.innerHTML = `<span>Processing memory stream…</span>`;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("target_role", role);

  try {
    const res = await apiRequest("/resume/analyze", {
      method: "POST",
      body: formData,
    });
    renderResumeResults(res.data, role);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Analyze Résumé</span> <span class="arrow">→</span>`;
  }
});

// Logout Handler
$("#logout").addEventListener("click", async () => {
  try {
    await fetch("/auth/logout", { method: "POST" });
    window.location.href = "/login";
  } catch (err) {
    window.location.href = "/login";
  }
});

// Mobile Navigation Toggle
$("#mobile-menu").addEventListener("click", () => {
  const sidebar = $(".sidebar");
  sidebar.scrollIntoView({ behavior: "smooth" });
});

// Hash routing
window.addEventListener("hashchange", handleViewChange);

// App Lifecycle Boot
(async () => {
  try {
    await initUser();
    await initRoles();
    handleViewChange();
    await fetchLiveJobs(1, false);
  } catch (err) {
    console.error("Boot error:", err);
  }
})();
