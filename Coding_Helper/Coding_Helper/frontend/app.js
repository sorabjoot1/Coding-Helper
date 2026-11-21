const form = document.getElementById("assistForm");
const promptEl = document.getElementById("prompt");
const codeEl = document.getElementById("code");
const languageEl = document.getElementById("language");
const runBtn = document.getElementById("runBtn");
const outputEl = document.querySelector("#output code");
const toast = document.getElementById("toast");
const statusEl = document.getElementById("status");
const modeHint = document.getElementById("modeHint");
const clearBtn = document.getElementById("clearBtn");
const copyBtn = document.getElementById("copyBtn");

const SESSION_KEY = "coding_helper_session";
let sessionId = localStorage.getItem(SESSION_KEY) || null;
let mode = "generate";

const HINTS = {
  generate: "Generate a complete runnable solution.",
  explain: "Explain code in simple language.",
  debug: "Detect errors and suggest fixes.",
  optimize: "Improve and optimize existing code.",
  ask: "Answer a programming question.",
};

function showToast(msg, ok = false) {
  toast.textContent = msg;
  toast.classList.toggle("ok", ok);
  toast.classList.remove("hidden");
}

function setLoading(loading) {
  runBtn.disabled = loading;
  runBtn.querySelector(".label").classList.toggle("hidden", loading);
  runBtn.querySelector(".spinner").classList.toggle("hidden", !loading);
}

document.querySelectorAll(".mode").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mode").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    mode = btn.dataset.mode;
    modeHint.textContent = HINTS[mode];
  });
});

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    statusEl.classList.toggle("ok", data.llm_configured);
    statusEl.classList.toggle("err", !data.llm_configured);
    statusEl.textContent = data.llm_configured
      ? `Ready · ${data.model}`
      : "Add OPENROUTER_API_KEY to .env";
  } catch {
    statusEl.classList.add("err");
    statusEl.textContent = "Backend offline";
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  toast.classList.add("hidden");
  setLoading(true);

  try {
    const res = await fetch("/api/assist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode,
        language: languageEl.value,
        prompt: promptEl.value.trim(),
        code: codeEl.value,
        session_id: sessionId,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Assist request failed.");

    sessionId = data.session_id;
    localStorage.setItem(SESSION_KEY, sessionId);
    outputEl.textContent = data.reply;
    showToast("Response ready.", true);
  } catch (err) {
    showToast(err.message || "Something went wrong.");
  } finally {
    setLoading(false);
  }
});

clearBtn.addEventListener("click", async () => {
  try {
    if (sessionId) {
      await fetch(`/api/history/${sessionId}`, { method: "DELETE" });
    }
    outputEl.textContent = "Results appear here.";
    showToast("History cleared.", true);
  } catch (err) {
    showToast(err.message || "Could not clear history.");
  }
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(outputEl.textContent || "");
    showToast("Copied to clipboard.", true);
  } catch {
    showToast("Copy failed.");
  }
});

checkHealth();
