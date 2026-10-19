/**
 * JobFit — Student Career Intelligence & Opportunity Hub
 * Complete Client-Side Application Controller
 */

const API_BASE = "/api";
let currentUser = null;
let currentProfile = null;
let availableRoles = [];

// Opportunity State
let oppCurrentPage = 1;
let oppCurrentQuery = "Software Developer";
let oppCurrentCategory = "All";
let oppCurrentLocation = "";
let oppCurrentCountry = "in";
let oppCurrentLevel = "";
let savedOpportunityIds = new Set();

// Active Resume in Memory
let activeResumeDocument = null;
let currentAtsResult = null;

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
  return String(str)
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
  const validViews = ["home", "profile", "opportunities", "resume", "roadmap", "applications", "developer"];
  const targetId = validViews.includes(hash) ? hash : "home";

  $$(".view").forEach((view) => {
    view.classList.toggle("active", view.id === targetId);
  });

  $$("[data-view]").forEach((link) => {
    link.classList.toggle("active", link.dataset.view === targetId);
  });

  window.scrollTo({ top: 0, behavior: "smooth" });

  // Refresh view specific data when navigated
  if (targetId === "home") {
    loadDashboardSummary();
  } else if (targetId === "profile") {
    loadStudentProfile();
  } else if (targetId === "applications") {
    loadApplications();
  } else if (targetId === "resume") {
    loadMyResumes();
  }
}

// Starfield Canvas Particle System
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

// Mouse Parallax 3D Tilt Effect
(function init3DTilt() {
  document.addEventListener("mousemove", (e) => {
    const tiltElements = $$("[data-tilt]");
    const { clientX, clientY } = e;

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

// User Authentication Boot
async function initUser() {
  try {
    const res = await apiRequest("/auth/me");
    if (!res.user) {
      window.location.href = "/login";
      return;
    }
    currentUser = res.user;
    $("#user-name").textContent = currentUser.name || "JobFit Student";
    $("#user-email").textContent = currentUser.email || "Session Active";
    if (currentUser.picture) {
      const pic = $("#user-picture");
      pic.src = currentUser.picture;
      pic.hidden = false;
      $("#user-avatar-fallback").hidden = true;
    } else {
      const initial = (currentUser.name || "S").charAt(0).toUpperCase();
      $("#user-avatar-fallback").textContent = initial;
    }
  } catch (err) {
    console.error("Auth check failed:", err);
  }
}

// Role Suggestions Init
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

// ============================================================================
// 01 / Overview Dashboard Controller
// ============================================================================

async function loadDashboardSummary() {
  try {
    const res = await apiRequest("/dashboard/summary");
    const d = res.data;

    $("#dash-ats-score").textContent = `${d.ats_readiness_score}%`;
    $("#dash-ats-bar").style.width = `${d.ats_readiness_score}%`;

    $("#dash-role-name").textContent = d.target_role || "Software Developer";
    $("#roadmap-role-title").textContent = d.target_role || "Software Developer";

    $("#dash-apps-count").textContent = String(d.applications_count);
    $("#dash-apps-bar").style.width = `${Math.min(100, d.applications_count * 20)}%`;

    $("#dash-saved-count").textContent = String(d.saved_opportunities_count);
    $("#dash-saved-bar").style.width = `${Math.min(100, d.saved_opportunities_count * 25)}%`;

    const actionsList = $("#dash-next-actions-list");
    if (actionsList && d.next_best_actions) {
      actionsList.replaceChildren();
      d.next_best_actions.forEach((act) => {
        const li = document.createElement("li");
        li.textContent = act;
        actionsList.appendChild(li);
      });
    }
  } catch (err) {
    console.warn("Error loading dashboard summary:", err);
  }
}

// ============================================================================
// 02 / Student Profile Controller
// ============================================================================

async function loadStudentProfile() {
  try {
    const res = await apiRequest("/profile");
    const p = res.data;
    currentProfile = p;

    if ($("#prof-name")) $("#prof-name").value = p.name || currentUser?.name || "";
    if ($("#prof-email")) $("#prof-email").value = p.email || currentUser?.email || "";
    if ($("#prof-phone")) $("#prof-phone").value = p.phone || "";
    if ($("#prof-location")) $("#prof-location").value = p.location || "";
    if ($("#prof-github")) $("#prof-github").value = p.github || "";
    if ($("#prof-linkedin")) $("#prof-linkedin").value = p.linkedin || "";
    if ($("#prof-portfolio")) $("#prof-portfolio").value = p.portfolio || "";

    if ($("#prof-degree")) $("#prof-degree").value = p.degree || "B.Tech";
    if ($("#prof-branch")) $("#prof-branch").value = p.branch || "CSE";
    if ($("#prof-college")) $("#prof-college").value = p.college || "";
    if ($("#prof-grad-year")) $("#prof-grad-year").value = p.graduation_year || 2026;
    if ($("#prof-cgpa")) $("#prof-cgpa").value = p.cgpa || 8.0;
    if ($("#prof-backlogs")) $("#prof-backlogs").value = p.backlogs || 0;
    if ($("#prof-academic-year")) $("#prof-academic-year").value = p.academic_year || "Final Year";

    if ($("#prof-languages")) $("#prof-languages").value = (p.programming_languages || p.skills || []).join(", ");
    if ($("#prof-frameworks")) $("#prof-frameworks").value = (p.frameworks || []).join(", ");
    if ($("#prof-cloud-db")) $("#prof-cloud-db").value = [...(p.databases || []), ...(p.cloud_skills || []), ...(p.tools || [])].join(", ");

    if ($("#prof-target-role")) $("#prof-target-role").value = p.target_roles?.[0] || p.target_role || "Software Developer";
    if ($("#prof-opp-pref")) $("#prof-opp-pref").value = p.opportunity_preference || "Both";
    if ($("#prof-remote-pref")) $("#prof-remote-pref").value = p.remote_preference || "Any";
    if ($("#prof-locations")) $("#prof-locations").value = (p.preferred_locations || []).join(", ");

    // Sync builder name & contact
    if ($("#b-name")) $("#b-name").value = p.name || "";
    if ($("#b-email")) $("#b-email").value = p.email || "";
    if ($("#b-phone")) $("#b-phone").value = p.phone || "";
    if ($("#b-location")) $("#b-location").value = p.location || "";
    if ($("#b-github")) $("#b-github").value = p.github || "";
    if ($("#b-linkedin")) $("#b-linkedin").value = p.linkedin || "";
    if ($("#b-portfolio")) $("#b-portfolio").value = p.portfolio || "";
  } catch (err) {
    console.warn("Could not fetch profile:", err);
  }
}

function collectProfileFormData() {
  return {
    name: $("#prof-name").value.trim(),
    email: $("#prof-email").value.trim(),
    phone: $("#prof-phone").value.trim(),
    location: $("#prof-location").value.trim(),
    github: $("#prof-github").value.trim(),
    linkedin: $("#prof-linkedin").value.trim(),
    portfolio: $("#prof-portfolio").value.trim(),
    degree: $("#prof-degree").value.trim(),
    branch: $("#prof-branch").value.trim(),
    college: $("#prof-college").value.trim(),
    academic_year: $("#prof-academic-year").value,
    graduation_year: Number($("#prof-grad-year").value),
    cgpa: Number($("#prof-cgpa").value),
    backlogs: Number($("#prof-backlogs").value),
    programming_languages: splitValues($("#prof-languages").value),
    frameworks: splitValues($("#prof-frameworks").value),
    skills: splitValues($("#prof-languages").value),
    databases: splitValues($("#prof-cloud-db").value).filter((s) => ["sql", "postgres", "mongodb", "redis"].some((k) => s.toLowerCase().includes(k))),
    cloud_skills: splitValues($("#prof-cloud-db").value).filter((s) => ["aws", "azure", "gcp", "docker", "cloud"].some((k) => s.toLowerCase().includes(k))),
    tools: splitValues($("#prof-cloud-db").value),
    target_roles: [$("#prof-target-role").value.trim()],
    target_role: $("#prof-target-role").value.trim(),
    opportunity_preference: $("#prof-opp-pref").value,
    remote_preference: $("#prof-remote-pref").value,
    preferred_locations: splitValues($("#prof-locations").value),
  };
}

$("#student-profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#save-profile-btn");
  btn.disabled = true;
  btn.textContent = "Saving profile…";

  try {
    const payload = collectProfileFormData();
    const res = await apiRequest("/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    currentProfile = res.data;
    showToast("Student profile saved successfully!", "success");
    loadDashboardSummary();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Save Student Profile</span> <span class="arrow">✓</span>`;
  }
});

$("#autofill-student-profile").addEventListener("click", () => {
  $("#prof-name").value = "Anish Ankareddy";
  $("#prof-phone").value = "+91 98765 43210";
  $("#prof-location").value = "Bengaluru, Karnataka";
  $("#prof-github").value = "https://github.com/ankareddyanish06-ctrl";
  $("#prof-linkedin").value = "https://linkedin.com/in/anishreddy";
  $("#prof-portfolio").value = "https://jobfit.dev";
  $("#prof-degree").value = "B.Tech in Computer Science";
  $("#prof-branch").value = "CSE";
  $("#prof-college").value = "National Institute of Technology";
  $("#prof-grad-year").value = 2026;
  $("#prof-cgpa").value = 8.75;
  $("#prof-backlogs").value = 0;
  $("#prof-languages").value = "Python, JavaScript, TypeScript, C++, SQL";
  $("#prof-frameworks").value = "React, Node.js, FastAPI, Express.js";
  $("#prof-cloud-db").value = "PostgreSQL, MongoDB, AWS, Docker, Git, REST API";
  $("#prof-target-role").value = "Full Stack Developer";
  $("#prof-opp-pref").value = "Both";
  $("#prof-remote-pref").value = "Any";
  $("#prof-locations").value = "Bengaluru, Hyderabad, Remote";
  showToast("Sample student profile populated.", "info");
});

// ============================================================================
// 03 / Opportunities Hub Controller
// ============================================================================

async function fetchOpportunities(page = 1, append = false) {
  const container = $("#opp-list");
  if (!append && container) {
    container.innerHTML = `
      <div class="surface" style="grid-column: 1/-1; text-align: center; padding: 3rem;">
        <p class="kicker">SEARCHING OPPORTUNITIES</p>
        <p style="color: var(--text-muted);">Fetching real-time opportunities and verified student programs…</p>
      </div>
    `;
  }

  const params = new URLSearchParams({
    query: oppCurrentQuery,
    country: oppCurrentCountry,
    page: String(page),
  });

  if (oppCurrentCategory && oppCurrentCategory !== "All") params.set("category", oppCurrentCategory);
  if (oppCurrentLocation) params.set("location", oppCurrentLocation);
  if (oppCurrentLevel) params.set("level", oppCurrentLevel);

  try {
    const res = await apiRequest(`/opportunities?${params}`);
    const data = res.data;

    // Fetch saved opportunities to sync save button state
    await syncSavedOpportunities();

    renderOpportunitiesList(data.jobs, append);

    $("#opp-meta").textContent = data.live
      ? `${data.provider} · ${data.jobs.length} roles found${data.total_results ? ` (${data.total_results} total available)` : ""}${data.notice ? ` · ${data.notice}` : ""}`
      : (data.error || "Opportunities retrieved.");

    $("#provider-text").textContent = data.live
      ? `Live stream active via ${data.provider}`
      : "Curated student stream active";

    const loadMoreBtn = $("#opp-load-more");
    if (loadMoreBtn) {
      loadMoreBtn.hidden = !data.jobs || data.jobs.length < 10;
    }
    oppCurrentPage = page;
  } catch (err) {
    if (container) {
      container.innerHTML = `
        <div class="surface message" style="grid-column: 1/-1;">
          Failed to load opportunities: ${escapeHtml(err.message)}
        </div>
      `;
    }
  }
}

async function syncSavedOpportunities() {
  try {
    const res = await apiRequest("/opportunities/saved");
    savedOpportunityIds = new Set(res.data.map((o) => String(o.id)));
  } catch {
    savedOpportunityIds = new Set();
  }
}

function buildOpportunityCard(opp) {
  const card = document.createElement("article");
  card.className = "job-card";
  card.dataset.oppId = opp.id;

  const isSaved = savedOpportunityIds.has(String(opp.id));

  const published = opp.posted_date || "Active";
  const skillsHtml =
    opp.skills && opp.skills.length
      ? opp.skills
          .slice(0, 6)
          .map((s) => `<span>${escapeHtml(s)}</span>`)
          .join("")
      : "<span>General IT</span>";

  const salaryHtml = opp.salary_formatted
    ? `<span class="salary-tag">${escapeHtml(opp.salary_formatted)}</span>`
    : "";

  const matchPill = opp.match_percentage != null
    ? `<span class="match-pill">Skill Match: ${opp.match_percentage}%</span>`
    : "";

  card.innerHTML = `
    <div>
      <div class="job-header-row">
        <div>
          <span class="job-type-badge">${escapeHtml(opp.type || "Job")}</span>
          <span class="job-workplace-badge">${escapeHtml(opp.workplace_type || "On-site")}</span>
        </div>
        <span class="job-time">${escapeHtml(published)}</span>
      </div>
      <h3 style="margin-top: 0.6rem;">${escapeHtml(opp.title)}</h3>
      <p class="job-company">🏢 ${escapeHtml(opp.company)}</p>
      <p class="job-location">📍 ${escapeHtml(opp.location)}</p>
      ${salaryHtml}
      <p class="job-desc">${escapeHtml(opp.description || "Official candidate requirements extracted from listing.")}</p>
      <div class="chips">${skillsHtml}</div>
    </div>
    <div class="job-footer-row">
      <div>${matchPill}</div>
      <div class="job-card-actions">
        <button type="button" class="job-card-btn why-btn" data-action="why-match">
          Why This Match? ⚡
        </button>
        <button type="button" class="job-card-btn ${isSaved ? "saved-active" : ""}" data-action="toggle-save">
          ${isSaved ? "★ Saved" : "☆ Save"}
        </button>
        <button type="button" class="job-card-btn" data-action="optimize-resume">
          Optimize Resume 📝
        </button>
        <a class="source-link" href="${escapeHtml(opp.url)}" target="_blank" rel="noreferrer">
          Apply Official ↗
        </a>
      </div>
    </div>
  `;

  // Attach button events
  card.querySelector('[data-action="why-match"]').onclick = () => openWhyMatchModal(opp);
  card.querySelector('[data-action="toggle-save"]').onclick = (e) => toggleSaveOpportunity(opp, e.currentTarget);
  card.querySelector('[data-action="optimize-resume"]').onclick = () => prefillJobOptimizer(opp);

  return card;
}

function renderOpportunitiesList(jobs, append = false) {
  const container = $("#opp-list");
  if (!container) return;

  if (!append) container.replaceChildren();

  if (!jobs || !jobs.length) {
    if (!append) {
      container.innerHTML = `
        <div class="surface" style="grid-column: 1/-1; text-align: center; padding: 3rem;">
          <p class="kicker">NO OPPORTUNITIES FOUND</p>
          <p style="color: var(--text-muted); margin-top: 0.5rem;">
            No live opportunities matched your current search and filters. Try selecting 'All Roles' or broadening your keyword query.
          </p>
        </div>
      `;
    }
    return;
  }

  jobs.forEach((job) => container.appendChild(buildOpportunityCard(job)));
}

// Category tabs click
$("#opportunity-category-tabs").addEventListener("click", (e) => {
  if (e.target && e.target.dataset.category) {
    $$("#opportunity-category-tabs .cat-pill").forEach((p) => p.classList.remove("active"));
    e.target.classList.add("active");
    oppCurrentCategory = e.target.dataset.category;
    fetchOpportunities(1, false);
  }
});

// Search form submit
$("#opp-search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  oppCurrentQuery = $("#opp-query").value.trim() || "Software Developer";
  oppCurrentLocation = $("#opp-location").value.trim();
  oppCurrentCountry = $("#opp-country").value;
  oppCurrentLevel = $("#opp-level").value;
  fetchOpportunities(1, false);
});

// Load more click
$("#opp-load-more").addEventListener("click", () => {
  fetchOpportunities(oppCurrentPage + 1, true);
});

// Bookmark / Save Opportunity Handler
async function toggleSaveOpportunity(opp, btn) {
  const oppId = String(opp.id);
  const isSaved = savedOpportunityIds.has(oppId);

  try {
    if (isSaved) {
      await apiRequest(`/opportunities/save/${oppId}`, { method: "DELETE" });
      savedOpportunityIds.delete(oppId);
      btn.textContent = "☆ Save";
      btn.classList.remove("saved-active");
      showToast("Removed from saved opportunities.", "info");
    } else {
      await apiRequest("/opportunities/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ opportunity: opp }),
      });
      savedOpportunityIds.add(oppId);
      btn.textContent = "★ Saved";
      btn.classList.add("saved-active");
      showToast("Opportunity bookmarked to your workspace!", "success");

      // Also create a 'Saved' tracking entry in applications
      await apiRequest("/applications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company: opp.company,
          role: opp.title,
          opportunity_id: oppId,
          status: "Saved",
          url: opp.url,
          notes: `Bookmarked from Opportunities Hub (${opp.type || "Role"}).`,
        }),
      }).catch(() => {});
    }
    loadDashboardSummary();
  } catch (err) {
    showToast(`Could not update saved status: ${err.message}`, "error");
  }
}

// "Why This Match?" Explainability Modal
function evidenceBullet(type, message) {
  const bullet = document.createElement("div");
  bullet.className = `evidence-bullet ${type}`;
  bullet.textContent = message;
  return bullet;
}

function renderWhyMatchEvidence(evidenceBox, evidence) {
  evidenceBox.replaceChildren();
  evidence.forEach((item) => evidenceBox.appendChild(evidenceBullet(item.type || "neutral", item.message)));
}

async function openWhyMatchModal(opp) {
  const modal = $("#why-match-modal");
  const title = opp?.title || "Opportunity Alignment";
  const company = opp?.company || "Verified opportunity";
  const location = opp?.location || "Location not specified";
  const skills = Array.isArray(opp?.skills) ? opp.skills.filter(Boolean) : [];
  const profileSkills = Array.isArray(currentProfile?.skills)
    ? currentProfile.skills
    : (Array.isArray(currentProfile?.technical_skills) ? currentProfile.technical_skills : []);
  const profileSkillSet = new Set(profileSkills.map((skill) => String(skill).trim().toLowerCase()));
  const matched = skills.filter((skill) => profileSkillSet.has(String(skill).trim().toLowerCase()));
  const unmatched = skills.filter((skill) => !profileSkillSet.has(String(skill).trim().toLowerCase()));

  $("#modal-opp-title").textContent = title;
  $("#modal-opp-company").textContent = `${company} · ${location}`;
  $("#modal-opp-tier").textContent = "Checking alignment…";

  const evidenceBox = $("#modal-evidence-list");
  const initialEvidence = [];
  if (matched.length) {
    initialEvidence.push({ type: "positive", message: `Profile evidence: ${matched.slice(0, 4).join(", ")} appears in both your profile and this opportunity.` });
  }
  if (unmatched.length) {
    initialEvidence.push({ type: "gap", message: `Preparation areas: ${unmatched.slice(0, 3).join(", ")}. Add them only after gaining genuine experience.` });
  }
  if (!initialEvidence.length) {
    initialEvidence.push({ type: "neutral", message: "This listing does not expose enough structured skill data for an instant comparison. JobFit is requesting a detailed explanation now." });
  }
  renderWhyMatchEvidence(evidenceBox, initialEvidence);
  modal.hidden = false;

  try {
    const res = await apiRequest("/opportunities/why-match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ opportunity: opp || {}, profile: currentProfile || {} }),
    });
    const d = res?.data || {};
    $("#modal-opp-tier").textContent = d.alignment_tier || "Opportunity alignment";
    const detailedEvidence = Array.isArray(d.evidence) ? d.evidence.filter((item) => item?.message) : [];
    if (detailedEvidence.length) {
      renderWhyMatchEvidence(evidenceBox, detailedEvidence);
    } else {
      evidenceBox.appendChild(evidenceBullet("neutral", "The detailed service returned no additional criteria. Review the official listing before applying."));
    }
  } catch (err) {
    $("#modal-opp-tier").textContent = "Opportunity details available";
    evidenceBox.appendChild(evidenceBullet("neutral", `Detailed alignment could not be loaded: ${err.message}. The visible criteria above are based only on listing data.`));
  }
}

$("#close-why-match-modal").addEventListener("click", () => {
  $("#why-match-modal").hidden = true;
});

// ============================================================================// 04 / Resume Center Controller
// ============================================================================

// Subtab switching
$("#resume-tabs").addEventListener("click", (e) => {
  if (e.target && e.target.dataset.tab) {
    const tabKey = e.target.dataset.tab;
    $$("#resume-tabs .subtab-btn").forEach((b) => b.classList.remove("active"));
    $$(".resume-tab-pane").forEach((p) => p.classList.remove("active"));

    e.target.classList.add("active");
    const targetPane = $(`#tab-pane-${tabKey}`);
    if (targetPane) targetPane.classList.add("active");
  }
});

$("#trigger-create-new-resume").addEventListener("click", () => {
  $('[data-tab="create-resume"]').click();
});

// Load My Resumes
async function loadMyResumes() {
  const container = $("#my-resumes-list");
  if (!container) return;

  try {
    const res = await apiRequest("/resume/my-resumes");
    const list = res.data || [];

    if (!list.length) {
      container.innerHTML = `
        <div class="surface" style="grid-column: 1/-1; text-align: center; padding: 2.5rem;">
          <p class="kicker">NO RESUMES SAVED YET</p>
          <p style="color: var(--text-muted); margin-top: 0.5rem;">
            You haven't built or uploaded a resume yet. Build one from scratch with our student-friendly builder or upload an existing file.
          </p>
          <button type="button" class="button primary small mt-1" onclick="$('[data-tab=\\'create-resume\\']').click()">
            Create Your First Resume →
          </button>
        </div>
      `;
      return;
    }

    container.replaceChildren();
    list.forEach((r) => {
      const card = document.createElement("article");
      card.className = "my-resume-card";
      const updatedStr = new Date(r.updated_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      });

      card.innerHTML = `
        <div>
          <div class="card-header-flex">
            <span class="my-resume-badge">ATS Score: ${r.ats_score}%</span>
            <span class="source-note">${escapeHtml(updatedStr)}</span>
          </div>
          <h4 style="margin-top: 0.6rem;">${escapeHtml(r.title)}</h4>
          <p class="section-subtext">Target: <b>${escapeHtml(r.target_role)}</b> · Layout: ${escapeHtml(r.template_id.toUpperCase())}</p>
        </div>
        <div class="my-resume-actions">
          <button type="button" class="button outline mini" data-act="edit">Preview / Edit</button>
          <button type="button" class="button outline mini" data-act="pdf">PDF ↓</button>
          <button type="button" class="button outline mini" data-act="docx">DOCX ↓</button>
          <button type="button" class="button ghost mini" style="color:var(--danger);" data-act="delete">✕</button>
        </div>
      `;

      card.querySelector('[data-act="edit"]').onclick = () => loadResumeIntoBuilder(r);
      card.querySelector('[data-act="pdf"]').onclick = () => downloadResumeFile(r.content, r.template_id, "pdf");
      card.querySelector('[data-act="docx"]').onclick = () => downloadResumeFile(r.content, r.template_id, "docx");
      card.querySelector('[data-act="delete"]').onclick = async () => {
        if (confirm(`Delete '${r.title}'?`)) {
          await apiRequest(`/resume/${r.id}`, { method: "DELETE" });
          showToast("Resume deleted.", "info");
          loadMyResumes();
          loadDashboardSummary();
        }
      };

      container.appendChild(card);
    });
  } catch (err) {
    console.warn("Could not load resumes:", err);
  }
}

// Upload Resume Handler (.pdf, .docx, .txt)
const dropzone = $("#resume-dropzone");
const resumeFileInput = $("#resume-file-input");
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

$("#upload-resume-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = $("#upload-error");
  errorEl.hidden = true;

  const file = resumeFileInput.files[0];
  if (!file) {
    errorEl.textContent = "Please select a .pdf, .docx, or .txt file.";
    errorEl.hidden = false;
    return;
  }

  const role = $("#upload-target-role").value.trim() || "Software Developer";
  const btn = $("#upload-analyze-btn");
  btn.disabled = true;
  btn.innerHTML = `<span>Processing volatile memory stream…</span>`;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("target_role", role);

  try {
    const res = await apiRequest("/resume/upload-and-analyze", {
      method: "POST",
      body: formData,
    });

    activeResumeDocument = res.document;
    currentAtsResult = res.ats_result;

    // Populate builder with parsed data
    populateBuilderFromDocument(res.document);

    // Switch to ATS Checker sub-tab and render score
    renderAtsResults(res.ats_result, role);
    $('[data-tab="ats-checker"]').click();
    showToast("Resume parsed & ATS readiness evaluated!", "success");
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.hidden = false;
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Upload & Check ATS Readiness</span> <span class="arrow">→</span>`;
  }
});

// Dynamic Rows for Builder
$("#b-add-edu-btn").addEventListener("click", () => {
  const container = $("#b-edu-container");
  const div = document.createElement("div");
  div.className = "dynamic-row-card";
  div.innerHTML = `
    <button type="button" class="dynamic-row-remove-btn" onclick="this.parentElement.remove()">✕ Remove</button>
    <div class="form-grid four">
      <label>Degree <input class="b-edu-degree" placeholder="Degree / Diploma"></label>
      <label>Institution <input class="b-edu-inst" placeholder="College / University"></label>
      <label>Year <input class="b-edu-year" placeholder="e.g. 2022 – 2026"></label>
      <label>CGPA / Score <input class="b-edu-score" placeholder="e.g. 8.5 / 10.0"></label>
    </div>
  `;
  container.appendChild(div);
});

$("#b-add-proj-btn").addEventListener("click", () => {
  const container = $("#b-proj-container");
  const div = document.createElement("div");
  div.className = "dynamic-row-card";
  div.innerHTML = `
    <button type="button" class="dynamic-row-remove-btn" onclick="this.parentElement.remove()">✕ Remove</button>
    <div class="form-grid three">
      <label>Project Title <input class="b-proj-title" placeholder="Project Name"></label>
      <label>Technologies Used <input class="b-proj-tech" placeholder="e.g. Python, SQL, Docker"></label>
      <label>Demo / Repo Link <input class="b-proj-link" placeholder="https://github.com/..."></label>
    </div>
    <label class="mt-half">Bullet Points (One per line)
      <textarea class="b-proj-bullets" rows="2" placeholder="• STAR-format achievement bullet..."></textarea>
    </label>
  `;
  container.appendChild(div);
});

$("#b-add-exp-btn").addEventListener("click", () => {
  const container = $("#b-exp-container");
  const div = document.createElement("div");
  div.className = "dynamic-row-card";
  div.innerHTML = `
    <button type="button" class="dynamic-row-remove-btn" onclick="this.parentElement.remove()">✕ Remove</button>
    <div class="form-grid three">
      <label>Role / Title <input class="b-exp-role" placeholder="e.g. Engineering Intern"></label>
      <label>Company / Organization <input class="b-exp-company" placeholder="Company Name"></label>
      <label>Duration <input class="b-exp-duration" placeholder="e.g. Summer 2025"></label>
    </div>
    <label class="mt-half">Impact Bullets (One per line)
      <textarea class="b-exp-bullets" rows="2" placeholder="• Quantifiable contribution bullet..."></textarea>
    </label>
  `;
  container.appendChild(div);
});

function collectBuilderDocument() {
  const eduRows = $$("#b-edu-container .dynamic-row-card");
  const education = Array.from(eduRows).map((row) => ({
    degree: row.querySelector(".b-edu-degree")?.value.trim() || "",
    institution: row.querySelector(".b-edu-inst")?.value.trim() || "",
    year: row.querySelector(".b-edu-year")?.value.trim() || "",
    score: row.querySelector(".b-edu-score")?.value.trim() || "",
  })).filter((e) => e.degree || e.institution);

  const projRows = $$("#b-proj-container .dynamic-row-card");
  const projects = Array.from(projRows).map((row) => ({
    title: row.querySelector(".b-proj-title")?.value.trim() || "",
    tech: row.querySelector(".b-proj-tech")?.value.trim() || "",
    link: row.querySelector(".b-proj-link")?.value.trim() || "",
    bullets: (row.querySelector(".b-proj-bullets")?.value || "").split("\n").map((b) => b.trim()).filter(Boolean),
  })).filter((p) => p.title);

  const expRows = $$("#b-exp-container .dynamic-row-card");
  const experience = Array.from(expRows).map((row) => ({
    role: row.querySelector(".b-exp-role")?.value.trim() || "",
    company: row.querySelector(".b-exp-company")?.value.trim() || "",
    duration: row.querySelector(".b-exp-duration")?.value.trim() || "",
    bullets: (row.querySelector(".b-exp-bullets")?.value || "").split("\n").map((b) => b.trim()).filter(Boolean),
  })).filter((e) => e.role);

  return {
    personal_info: {
      name: $("#b-name").value.trim(),
      email: $("#b-email").value.trim(),
      phone: $("#b-phone").value.trim(),
      location: $("#b-location").value.trim(),
      github: $("#b-github").value.trim(),
      linkedin: $("#b-linkedin").value.trim(),
      portfolio: $("#b-portfolio").value.trim(),
    },
    summary: $("#b-summary").value.trim(),
    education: education,
    skills: {
      languages: splitValues($("#b-skills-lang").value),
      frameworks: splitValues($("#b-skills-frameworks").value),
      databases: splitValues($("#b-skills-db").value),
      tools: splitValues($("#b-skills-tools").value),
    },
    projects: projects,
    experience: experience,
    certifications: ($("#b-certifications").value || "").split("\n").map((s) => s.trim()).filter(Boolean),
    achievements: ($("#b-achievements").value || "").split("\n").map((s) => s.trim()).filter(Boolean),
  };
}

function populateBuilderFromDocument(doc) {
  if (!doc) return;
  const info = doc.personal_info || {};
  if ($("#b-name")) $("#b-name").value = info.name || "";
  if ($("#b-email")) $("#b-email").value = info.email || "";
  if ($("#b-phone")) $("#b-phone").value = info.phone || "";
  if ($("#b-location")) $("#b-location").value = info.location || "";
  if ($("#b-github")) $("#b-github").value = info.github || "";
  if ($("#b-linkedin")) $("#b-linkedin").value = info.linkedin || "";
  if ($("#b-portfolio")) $("#b-portfolio").value = info.portfolio || "";
  if ($("#b-summary")) $("#b-summary").value = doc.summary || "";

  // Populate skills
  if (doc.skills) {
    if (Array.isArray(doc.skills)) {
      $("#b-skills-lang").value = doc.skills.join(", ");
    } else if (typeof doc.skills === "object") {
      $("#b-skills-lang").value = (doc.skills.languages || []).join(", ");
      $("#b-skills-frameworks").value = (doc.skills.frameworks || []).join(", ");
      $("#b-skills-db").value = (doc.skills.databases || []).join(", ");
      $("#b-skills-tools").value = (doc.skills.tools || []).join(", ");
    }
  }

  activeResumeDocument = doc;
}

function loadResumeIntoBuilder(resumeItem) {
  populateBuilderFromDocument(resumeItem.content);
  $("#builder-template-select").value = resumeItem.template_id || "classic";
  $('[data-tab="create-resume"]').click();
  showToast(`Loaded '${resumeItem.title}' into editor.`, "info");
}

// Builder Form Save
$("#builder-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const doc = collectBuilderDocument();
  const templateId = $("#builder-template-select").value;
  const targetRole = $("#prof-target-role")?.value || "Software Developer";

  try {
    const atsRes = await apiRequest("/resume/ats-check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_data: doc, target_role: targetRole }),
    });

    await apiRequest("/resume/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: `${doc.personal_info.name} — ${targetRole}`,
        target_role: targetRole,
        template_id: templateId,
        content: doc,
        ats_score: atsRes.data.ats_readiness_score,
      }),
    });

    activeResumeDocument = doc;
    currentAtsResult = atsRes.data;
    showToast("Resume saved to My Resumes!", "success");
    loadMyResumes();
    loadDashboardSummary();
  } catch (err) {
    showToast(err.message, "error");
  }
});

// Download PDF / DOCX
async function downloadResumeFile(doc, templateId, format = "pdf") {
  const endpoint = format === "pdf" ? "/resume/export-pdf" : "/resume/export-docx";
  const filename = format === "pdf" ? "JobFit_ATS_Resume.pdf" : "JobFit_ATS_Resume.docx";

  try {
    showToast(`Generating ATS ${format.toUpperCase()}…`, "info");
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_data: doc, template_id: templateId }),
    });

    if (!response.ok) throw new Error(`Failed to generate ${format.toUpperCase()}`);

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast(`Downloaded ATS-friendly ${format.toUpperCase()}!`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

$("#b-download-pdf-btn").addEventListener("click", () => {
  const doc = collectBuilderDocument();
  const templateId = $("#builder-template-select").value;
  downloadResumeFile(doc, templateId, "pdf");
});

$("#b-download-docx-btn").addEventListener("click", () => {
  const doc = collectBuilderDocument();
  const templateId = $("#builder-template-select").value;
  downloadResumeFile(doc, templateId, "docx");
});

$("#b-eval-ats-btn").addEventListener("click", async () => {
  const doc = collectBuilderDocument();
  const targetRole = $("#prof-target-role")?.value || "Software Developer";
  try {
    const res = await apiRequest("/resume/ats-check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_data: doc, target_role: targetRole }),
    });
    activeResumeDocument = doc;
    currentAtsResult = res.data;
    renderAtsResults(res.data, targetRole);
    $('[data-tab="ats-checker"]').click();
  } catch (err) {
    showToast(err.message, "error");
  }
});

// Render ATS Results
function renderAtsResults(data, role) {
  const score = data.ats_readiness_score || 0;
  $("#ats-score-display").textContent = `${score}%`;

  const ring = $("#ats-score-ring");
  if (ring) {
    const radius = ring.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    ring.style.strokeDasharray = `${circumference} ${circumference}`;
    ring.style.strokeDashoffset = offset;
  }

  $("#ats-score-heading").textContent = `${role} ATS Readiness`;
  $("#ats-score-target").textContent = `Evaluated against key competencies (${data.word_count} words).`;

  // Checklist
  const checklist = $("#ats-checklist");
  checklist.replaceChildren();
  const labels = {
    contact_info: "Contact & Identity Header",
    education: "Academic Background",
    skills: "Technical Skills Matrix",
    projects: "Applied Projects Showcase",
    experience: "Experience / Internships",
    certifications: "Industry Certifications",
  };

  Object.entries(data.structure_checklist || {}).forEach(([k, passed]) => {
    const li = document.createElement("li");
    li.className = passed ? "pass" : "fail";
    li.innerHTML = `<span>${passed ? "✓" : "✗"}</span> <span>${labels[k] || k}</span>`;
    checklist.appendChild(li);
  });

  // Action verbs & metrics box
  const metricsBox = $("#ats-metrics-box");
  metricsBox.replaceChildren();

  const vChip = document.createElement("span");
  vChip.className = "skill-chip match";
  vChip.textContent = `${data.action_verbs_found?.length || 0} Action Verbs`;
  metricsBox.appendChild(vChip);

  const mChip = document.createElement("span");
  mChip.className = "skill-chip match";
  mChip.textContent = `${data.metric_indicators_found || 0} Quantified Impact Metrics`;
  metricsBox.appendChild(mChip);

  // Suggestions
  const suggestionsList = $("#ats-suggestions");
  suggestionsList.replaceChildren();
  [...(data.strengths || []), ...(data.improvements || [])].forEach((s) => {
    const li = document.createElement("li");
    li.textContent = s;
    suggestionsList.appendChild(li);
  });
}

// Prefill Job Optimizer from Opportunity Card
function prefillJobOptimizer(opp) {
  $('[data-tab="job-optimizer"]').click();
  $("#opt-job-title").value = opp.title;
  $("#opt-job-desc").value = `${opp.title} at ${opp.company}\n\n${opp.description}\n\nRequired Skills: ${(opp.skills || []).join(", ")}`;
  showToast(`Prefilled optimizer with '${opp.title}'`, "info");
}

// Job Optimizer Form Submit
$("#job-optimize-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#run-optimization-btn");
  btn.disabled = true;
  btn.textContent = "Comparing resume against requirements…";

  const resumeData = activeResumeDocument || collectBuilderDocument();
  const jobTitle = $("#opt-job-title").value.trim();
  const jobDesc = $("#opt-job-desc").value.trim();

  try {
    const res = await apiRequest("/resume/optimize-for-job", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_data: resumeData,
        job_description: jobDesc,
        job_title: jobTitle,
      }),
    });
    const d = res.data;

    $("#opt-alignment-score").textContent = `Competency Alignment: ${d.alignment_percentage}%`;

    const matchedBox = $("#opt-matched-skills");
    matchedBox.replaceChildren();
    (d.matched_skills || []).forEach((s) => {
      const chip = document.createElement("span");
      chip.textContent = s;
      matchedBox.appendChild(chip);
    });
    if (!d.matched_skills?.length) {
      matchedBox.innerHTML = "<small style='color:var(--text-dim);'>No direct skill matches</small>";
    }

    const missingBox = $("#opt-missing-skills");
    missingBox.replaceChildren();
    (d.missing_skills || []).forEach((s) => {
      const chip = document.createElement("span");
      chip.textContent = `+ ${s}`;
      missingBox.appendChild(chip);
    });
    if (!d.missing_skills?.length) {
      missingBox.innerHTML = "<small style='color:var(--text-dim);'>All key skills matched!</small>";
    }

    const sugList = $("#opt-suggestions-list");
    sugList.replaceChildren();
    (d.recommendations || []).forEach((r) => {
      const li = document.createElement("li");
      li.textContent = r;
      sugList.appendChild(li);
    });

    $("#optimization-results").hidden = false;
    showToast("Optimization analysis complete!", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Compare & Optimize</span> <span class="arrow">→</span>`;
  }
});

// ============================================================================
// 05 / Career Roadmap Controller
// ============================================================================

$("#trigger-career-analysis-btn").addEventListener("click", async () => {
  const btn = $("#trigger-career-analysis-btn");
  btn.disabled = true;
  btn.textContent = "Analyzing against live signals…";

  const p = currentProfile || collectProfileFormData();
  const targetRole = p.target_roles?.[0] || p.target_role || "Full Stack Developer";

  try {
    const payload = {
      name: p.name || "Student Candidate",
      degree: p.degree || "B.Tech",
      branch: p.branch || "CSE",
      graduation_year: p.graduation_year || 2026,
      cgpa: p.cgpa || 8.0,
      backlogs: p.backlogs || 0,
      technical_skills: p.skills?.length ? p.skills : ["Python", "SQL", "Git", "REST API"],
      soft_skills: ["Problem Solving", "Agile Collaboration"],
      certifications: p.certifications || [],
      projects: typeof p.projects === "number" ? p.projects : (Array.isArray(p.projects) ? p.projects.length : 2),
      internships: typeof p.internships === "number" ? p.internships : (Array.isArray(p.internships) ? p.internships.length : 0),
      aptitude_score: 75.0,
      interview_score: 70.0,
      target_role: targetRole,
    };

    const res = await apiRequest("/career/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    renderRoadmapAnalysis(res);
    $("#analysis-results").hidden = false;
    $("#analysis-results").scrollIntoView({ behavior: "smooth" });
    showToast("Career roadmap diagnostics complete!", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>⚡ Run Full Analysis</span>`;
  }
});

function renderRoadmapAnalysis(data) {
  const { profile, analysis } = data;

  $("#analysis-title").textContent = `${profile.target_role} Readiness`;
  $("#readiness-label").textContent = analysis.readiness_label;
  $("#readiness-score").textContent = `${analysis.readiness_score}%`;

  const ring = $("#readiness-ring");
  if (ring) {
    const radius = ring.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (analysis.readiness_score / 100) * circumference;
    ring.style.strokeDasharray = `${circumference} ${circumference}`;
    ring.style.strokeDashoffset = offset;
  }

  const bd = analysis.score_breakdown;
  $("#academic-score").textContent = `${bd.academics}%`;
  $("#academic-bar").style.width = `${bd.academics}%`;

  $("#technical-score").textContent = `${bd.technical_skills}%`;
  $("#technical-bar").style.width = `${bd.technical_skills}%`;

  $("#experience-score").textContent = `${bd.experience}%`;
  $("#experience-bar").style.width = `${bd.experience}%`;

  $("#interview-score").textContent = `${bd.interview}%`;
  $("#interview-bar").style.width = `${bd.interview}%`;

  $("#source-note").textContent = `Benchmarked against ${analysis.skill_gap.source}.`;
  $("#next-action").textContent = analysis.next_action;

  const reasonList = $("#reason-list");
  reasonList.replaceChildren();
  (analysis.reasons || []).forEach((r) => {
    const li = document.createElement("li");
    li.textContent = r;
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
    chip.innerHTML = `${escapeHtml(skill)} <small>${isMatch ? "✓ MATCH" : isPriority ? "★ GAP" : "GAP"}</small>`;
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

  $("#copy-roadmap-btn").onclick = () => {
    const text = (analysis.roadmap || []).map((r) => `### ${r.period}: ${r.topic}\n${r.action}`).join("\n\n");
    navigator.clipboard.writeText(text);
    showToast("7-Week Sprint copied to clipboard!", "success");
  };

  // Interview Prompts
  const interviewContainer = $("#interview-list");
  interviewContainer.replaceChildren();
  (analysis.interview_prep || []).forEach((q) => {
    const li = document.createElement("li");
    li.textContent = q;
    interviewContainer.appendChild(li);
  });

  // Projects
  const projectIdeasList = $("#project-ideasList");
  if (projectIdeasList && analysis.project_ideas) {
    projectIdeasList.replaceChildren();
    analysis.project_ideas.forEach((p) => {
      const pCard = document.createElement("div");
      pCard.className = "project-idea-card";
      pCard.innerHTML = `
        <h4>🚀 ${escapeHtml(p.title)}</h4>
        <p>${escapeHtml(p.description)}</p>
        <div class="mt-half">
          <button type="button" class="button outline mini" onclick="window.location.hash='#opportunities'">Find Matching Internships →</button>
        </div>
      `;
      projectIdeasList.appendChild(pCard);
    });
  }

  // Verified Employer Criteria
  const eligibilityContainer = $("#eligibility-list");
  if (eligibilityContainer) {
    eligibilityContainer.replaceChildren();
    (analysis.eligibility || []).forEach((item) => {
      const card = document.createElement("article");
      card.className = "eligibility-card";
      const stateClass = item.status === "Eligible" ? "eligible" : item.status === "Almost Eligible" ? "almost" : "not";
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
}

// ============================================================================
// 06 / Application Tracker Controller
// ============================================================================

let currentFilterStatus = "All";

async function loadApplications() {
  const container = $("#applications-container");
  if (!container) return;

  try {
    const res = await apiRequest("/api/applications");
    const apps = res.data || [];

    const filtered = currentFilterStatus === "All"
      ? apps
      : apps.filter((a) => a.status === currentFilterStatus);

    if (!filtered.length) {
      container.innerHTML = `
        <div class="surface" style="grid-column: 1/-1; text-align: center; padding: 2.5rem;">
          <p class="kicker">NO APPLICATIONS FOUND</p>
          <p style="color: var(--text-muted); margin-top: 0.5rem;">
            No applications found in '${currentFilterStatus}'. Bookmark opportunities or manually record an application above.
          </p>
        </div>
      `;
      return;
    }

    container.replaceChildren();
    filtered.forEach((app) => {
      const card = document.createElement("article");
      card.className = "application-card";

      const appliedStr = app.applied_date ? `Applied: ${app.applied_date}` : "Date not recorded";
      const interviewStr = app.interview_date ? ` · Interview: ${app.interview_date}` : "";

      card.innerHTML = `
        <div>
          <div class="card-header-flex">
            <span class="app-status-badge ${escapeHtml(app.status)}">${escapeHtml(app.status)}</span>
            <select class="app-status-select" data-id="${app.id}">
              ${["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected", "Closed"]
                .map((st) => `<option value="${st}" ${st === app.status ? "selected" : ""}>${st}</option>`)
                .join("")}
            </select>
          </div>
          <h3 style="margin-top: 0.7rem;">${escapeHtml(app.role)}</h3>
          <p class="job-company">🏢 ${escapeHtml(app.company)}</p>
          <p class="source-note" style="margin: 0.4rem 0;">${escapeHtml(appliedStr)}${escapeHtml(interviewStr)}</p>
          ${app.notes ? `<p class="job-desc" style="font-style: italic;">“${escapeHtml(app.notes)}”</p>` : ""}
        </div>
        <div class="job-footer-row mt-half">
          ${app.url ? `<a class="source-link" href="${escapeHtml(app.url)}" target="_blank" rel="noreferrer">Job Portal ↗</a>` : "<span></span>"}
          <button type="button" class="button ghost mini" style="color:var(--danger);" data-action="delete-app">Delete</button>
        </div>
      `;

      card.querySelector(".app-status-select").onchange = async (e) => {
        const newStatus = e.target.value;
        await apiRequest(`/api/applications/${app.id}/status`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: newStatus }),
        });
        showToast(`Status updated to ${newStatus}`, "success");
        loadApplications();
        loadDashboardSummary();
      };

      card.querySelector('[data-action="delete-app"]').onclick = async () => {
        if (confirm(`Remove application for ${app.company}?`)) {
          await apiRequest(`/api/applications/${app.id}`, { method: "DELETE" });
          showToast("Application removed.", "info");
          loadApplications();
          loadDashboardSummary();
        }
      };

      container.appendChild(card);
    });
  } catch (err) {
    console.warn("Could not load applications:", err);
  }
}

$("#open-add-app-modal").addEventListener("click", () => {
  const box = $("#add-app-box");
  box.hidden = !box.hidden;
  if (!box.hidden) {
    box.scrollIntoView({ behavior: "smooth" });
  }
});

$("#cancel-add-app-btn").addEventListener("click", () => {
  $("#add-app-box").hidden = true;
});

$("#add-app-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await apiRequest("/api/applications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company: $("#app-company").value.trim(),
        role: $("#app-role").value.trim(),
        status: $("#app-status").value,
        applied_date: $("#app-applied-date").value || null,
        interview_date: $("#app-interview-date").value || null,
        url: $("#app-url").value.trim(),
        notes: $("#app-notes").value.trim(),
      }),
    });

    $("#add-app-box").hidden = true;
    $("#add-app-form").reset();
    showToast("Application added to tracker!", "success");
    loadApplications();
    loadDashboardSummary();
  } catch (err) {
    showToast(err.message, "error");
  }
});

$("#app-status-tabs").addEventListener("click", (e) => {
  if (e.target && e.target.dataset.status) {
    $$("#app-status-tabs .cat-pill").forEach((p) => p.classList.remove("active"));
    e.target.classList.add("active");
    currentFilterStatus = e.target.dataset.status;
    loadApplications();
  }
});

// Quick Role Chips in Overview
$("#quick-role-chips").addEventListener("click", (e) => {
  if (e.target && e.target.dataset.role) {
    const role = e.target.dataset.role;
    oppCurrentQuery = role;
    $("#opp-query").value = role;
    window.location.hash = "#opportunities";
    fetchOpportunities(1, false);
    showToast(`Filtering opportunities by: ${role}`, "info");
  }
});

// Logout Handler
$("#logout").addEventListener("click", async () => {
  try {
    await fetch("/auth/logout", { method: "POST" });
    window.location.href = "/login";
  } catch {
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
    await loadStudentProfile();
    handleViewChange();
    await fetchOpportunities(1, false);
    await loadDashboardSummary();
  } catch (err) {
    console.error("Boot error:", err);
  }
})();
