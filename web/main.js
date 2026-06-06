import { warmup, runValidate } from "./runtime.js";
import { renderSummary, renderIssues } from "./render.js";

const essayInput = document.getElementById("essay");
const validateButton = document.getElementById("validate-button");
const statusEl = document.getElementById("status");
const resultsSection = document.getElementById("results-section");
const summaryEl = document.getElementById("summary");
const issuesEl = document.getElementById("issues");
const downloadButton = document.getElementById("download-json");

let lastReport = null;

function setStatus(msg) {
  statusEl.textContent = msg;
}

function setReady() {
  setStatus("Ready.");
  validateButton.disabled = essayInput.value.trim().length === 0;
}

essayInput.addEventListener("input", () => {
  validateButton.disabled = essayInput.value.trim().length === 0;
});

// Kick off Pyodide load immediately so it's ready by the time the user clicks Validate.
warmup(setStatus)
  .then(setReady)
  .catch((err) => {
    console.error("Pyodide warmup failed:", err);
    setStatus(`Failed to load Python runtime: ${err.message || String(err)}`);
  });

validateButton.addEventListener("click", async () => {
  validateButton.disabled = true;
  resultsSection.classList.add("hidden");
  setStatus("Validating…");

  try {
    const result = await runValidate(essayInput.value, "text", setStatus);
    lastReport = result.report;
    summaryEl.innerHTML = renderSummary(result.report);
    issuesEl.innerHTML = renderIssues(result.report);
    resultsSection.classList.remove("hidden");
    setStatus("Done.");
  } catch (err) {
    console.error(err);
    setStatus(`Error: ${err.message || String(err)}`);
  } finally {
    validateButton.disabled = essayInput.value.trim().length === 0;
  }
});

downloadButton.addEventListener("click", () => {
  if (!lastReport) return;
  const blob = new Blob([JSON.stringify(lastReport, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "apa7-report.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
