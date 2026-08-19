const message = document.getElementById("login-message");
const googleButton = document.getElementById("google-login");
const devButton = document.getElementById("dev-login");
(async () => {
  try {
    const response = await fetch("/api/auth/config");
    const config = await response.json();
    if (!config.google_enabled) {
      googleButton.disabled = true;
      message.textContent = "Google sign-in is not configured yet. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to activate it.";
    }
    devButton.hidden = !config.development_login_enabled;
  } catch { message.textContent = "Cannot reach JobFit. Start the Python server and try again."; }
})();
googleButton.addEventListener("click", () => { window.location.href = "/auth/google/login"; });
devButton.addEventListener("click", async () => {
  const response = await fetch("/auth/dev-login", { method: "POST" });
  if (response.ok) window.location.href = "/";
  else message.textContent = "Local development sign-in is unavailable.";
});
