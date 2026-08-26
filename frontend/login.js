const message = document.getElementById("login-message");
const googleButton = document.getElementById("google-login");
const devButton = document.getElementById("dev-login");

// Starfield background particle effect
(function initStarfield() {
  const canvas = document.getElementById("starfield-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let stars = [];
  const count = 75;

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
      size: Math.random() * 1.6 + 0.3,
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
      ctx.shadowBlur = star.size * 4;
      ctx.shadowColor = "#c8ff00";
      ctx.fill();
    }
    requestAnimationFrame(render);
  }
  render();
})();

(async () => {
  try {
    const response = await fetch("/api/auth/config");
    const config = await response.json();
    if (!config.google_enabled) {
      googleButton.disabled = true;
      googleButton.title = "Google OAuth credentials not configured in .env";
      message.innerHTML = 'Google OAuth is unconfigured. Click below for <strong>Local Development Session</strong> or add Google credentials to <code>.env</code>.';
    }
    if (config.development_login_enabled) {
      devButton.hidden = false;
    }
  } catch {
    message.textContent = "Unable to connect to JobFit server. Please ensure FastAPI server is running.";
  }
})();

googleButton.addEventListener("click", () => {
  window.location.href = "/auth/google/login";
});

devButton.addEventListener("click", async () => {
  try {
    devButton.disabled = true;
    devButton.textContent = "Entering development session…";
    const response = await fetch("/auth/dev-login", { method: "POST" });
    if (response.ok) {
      window.location.href = "/";
    } else {
      message.textContent = "Local development sign-in is disabled on this server.";
      devButton.disabled = false;
      devButton.textContent = "⚡ Local Development Session";
    }
  } catch (e) {
    message.textContent = "Could not sign in: " + e.message;
    devButton.disabled = false;
  }
});

