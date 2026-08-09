const API_BASE = "/api";

const form = document.getElementById("prediction-form");
const formPanel = document.querySelector(".form-panel");
const resultsPanel = document.getElementById("results-panel");
const submitButton = document.getElementById("submit-btn");
const buttonText = submitButton.querySelector("span");
const spinner = document.getElementById("btn-spinner");
const errorBox = document.getElementById("form-error");

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  buttonText.textContent = isLoading ? "Analyzing your profile…" : "Analyze my readiness";
  spinner.hidden = !isLoading;
}

function makeChipList(element, values, emptyMessage, extraClass = "") {
  element.replaceChildren();
  if (!values.length) {
    const item = document.createElement("li");
    item.className = "empty";
    item.textContent = emptyMessage;
    element.append(item);
    return;
  }
  element.className = `chip-list ${extraClass}`;
  values.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    element.append(item);
  });
}

function animateCircle(element, textElement, value, color) {
  const started = performance.now();
  const duration = 900;
  const draw = (now) => {
    const progress = Math.min((now - started) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(value * eased);
    element.style.background = `conic-gradient(${color} ${current}%, #ffffff12 0)`;
    textElement.textContent = `${current}%`;
    if (progress < 1) requestAnimationFrame(draw);
  };
  requestAnimationFrame(draw);
}

function readinessCopy(score) {
  if (score >= 75) return "Strong readiness profile";
  if (score >= 55) return "Promising — keep building";
  return "A great starting point to grow";
}

function showResults(data) {
  formPanel.hidden = true;
  resultsPanel.hidden = false;
  animateCircle(document.getElementById("placement-circle"), document.getElementById("placement-value"), data.prediction_percentage, data.prediction_percentage >= 65 ? "#2dd4a2" : data.prediction_percentage >= 45 ? "#f8b854" : "#fb7185");
  animateCircle(document.getElementById("skill-circle"), document.getElementById("skill-value"), data.skill_score, "#a576ff");
  document.getElementById("readiness-label").textContent = readinessCopy(data.prediction_percentage);
  makeChipList(document.getElementById("matched-list"), data.matched_skills, "Add skills to see your strengths.");
  makeChipList(document.getElementById("recommendation-list"), data.recommended_skills, "Excellent coverage — keep practicing.", "recommend");
  document.getElementById("disclaimer").textContent = data.disclaimer;
  resultsPanel.focus({ preventScroll: true });
  resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  if (!form.reportValidity()) return;
  const skills = document.getElementById("skills").value.split(",").map((value) => value.trim()).filter(Boolean);
  if (!skills.length) {
    showError("Please enter at least one skill.");
    return;
  }
  setLoading(true);
  try {
    const response = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cgpa: Number(document.getElementById("cgpa").value),
        internships: Number(document.getElementById("internships").value),
        projects: Number(document.getElementById("projects").value),
        skills,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "The assessment could not be completed.");
    showResults(data);
    fetchHistory();
  } catch (error) {
    showError(error.message || "Could not connect to the service. Please try again.");
  } finally {
    setLoading(false);
  }
});

document.getElementById("reset-btn").addEventListener("click", () => {
  resultsPanel.hidden = true;
  formPanel.hidden = false;
  form.reset();
  document.getElementById("cgpa").focus();
});
document.getElementById("refresh-history").addEventListener("click", fetchHistory);

async function fetchHistory() {
  const body = document.querySelector("#history-table tbody");
  try {
    const response = await fetch(`${API_BASE}/history?limit=5`);
    const payload = await response.json();
    if (!response.ok) throw new Error();
    body.replaceChildren();
    if (!payload.data.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 6;
      cell.className = "empty-cell";
      cell.textContent = "No saved assessments yet.";
      row.append(cell);
      body.append(row);
      return;
    }
    payload.data.forEach((item) => {
      const row = document.createElement("tr");
      const cells = [
        new Date(item.timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }),
        Number(item.cgpa).toFixed(1), item.internships, item.projects,
        `${Number(item.skill_score).toFixed(0)}%`, `${Number(item.prediction).toFixed(1)}%`,
      ];
      cells.forEach((value) => { const cell = document.createElement("td"); cell.textContent = value; row.append(cell); });
      body.append(row);
    });
  } catch {
    body.replaceChildren();
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6;
    cell.className = "empty-cell";
    cell.textContent = "History is temporarily unavailable.";
    row.append(cell);
    body.append(row);
  }
}

fetchHistory();
