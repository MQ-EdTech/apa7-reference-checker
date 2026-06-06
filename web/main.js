import { runValidate, annotateDocx, warmup } from "./runtime.js";
import { renderSummary, renderIssues } from "./render.js";

const essayInput = document.getElementById("essay");
const validateButton = document.getElementById("validate-button");
const statusEl = document.getElementById("status");
const resultsSection = document.getElementById("results-section");
const summaryEl = document.getElementById("summary");
const issuesEl = document.getElementById("issues");
const downloadJsonButton = document.getElementById("download-json");
const downloadDocxButton = document.getElementById("download-docx");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const browseButton = document.getElementById("browse-button");
const selectedFileEl = document.getElementById("selected-file");

let lastReport = null;
let lastJobId = null;
let inputMode = "text";        // "text" | "docx"
let docxBytes = null;          // Uint8Array when inputMode === "docx"
let docxFilename = null;

function setStatus(msg) { statusEl.textContent = msg; }

function setValidateEnabled() {
  const haveText = essayInput.value.trim().length > 0;
  const haveDocx = inputMode === "docx" && docxBytes !== null;
  validateButton.disabled = !(haveText || haveDocx);
}

essayInput.addEventListener("input", () => {
  if (essayInput.value.trim().length > 0) {
    inputMode = "text";
    docxBytes = null;
    docxFilename = null;
    selectedFileEl.classList.add("hidden");
  }
  setValidateEnabled();
});

browseButton.addEventListener("click", (e) => {
  e.preventDefault();
  fileInput.click();
});

dropzone.addEventListener("click", (e) => {
  // Click on the zone background = open picker. Avoid double-fire from inner button.
  if (e.target === browseButton) return;
  fileInput.click();
});

dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

["dragenter", "dragover"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add("border-slate-500", "bg-slate-50");
  });
});

["dragleave", "drop"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("border-slate-500", "bg-slate-50");
  });
});

dropzone.addEventListener("drop", async (e) => {
  const file = e.dataTransfer?.files?.[0];
  if (file) await acceptFile(file);
});

fileInput.addEventListener("change", async () => {
  const file = fileInput.files?.[0];
  if (file) await acceptFile(file);
});

async function acceptFile(file) {
  if (!file.name.toLowerCase().endsWith(".docx")) {
    setStatus(`Only .docx supported in this phase — got ${file.name}`);
    return;
  }
  const buf = await file.arrayBuffer();
  docxBytes = new Uint8Array(buf);
  docxFilename = file.name;
  inputMode = "docx";
  selectedFileEl.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  selectedFileEl.classList.remove("hidden");
  essayInput.value = "";   // text input takes priority on next type; clear it
  setValidateEnabled();
  setStatus("Ready to validate.");
}

// Warm up Pyodide as soon as the page loads.
warmup(setStatus).then(() => {
  setStatus("Ready.");
  setValidateEnabled();
}).catch((err) => {
  console.error("Pyodide warmup failed:", err);
  setStatus(`Failed to load Python runtime: ${err.message || String(err)}`);
});

validateButton.addEventListener("click", async () => {
  validateButton.disabled = true;
  resultsSection.classList.add("hidden");
  downloadDocxButton.classList.add("hidden");
  setStatus("Validating…");

  try {
    let result;
    if (inputMode === "docx" && docxBytes) {
      result = await runValidate(docxBytes, "docx", setStatus);
    } else {
      result = await runValidate(essayInput.value, "text", setStatus);
    }
    lastReport = result.report;
    lastJobId = result.job_id;
    summaryEl.innerHTML = renderSummary(result.report);
    issuesEl.innerHTML = renderIssues(result.report);
    resultsSection.classList.remove("hidden");
    // Always show DOCX download — engine generates a fresh DOCX even for text inputs.
    downloadDocxButton.classList.remove("hidden");
    setStatus("Done.");
  } catch (err) {
    console.error(err);
    setStatus(`Error: ${err.message || String(err)}`);
  } finally {
    setValidateEnabled();
  }
});

downloadJsonButton.addEventListener("click", () => {
  if (!lastReport) return;
  const blob = new Blob([JSON.stringify(lastReport, null, 2)], { type: "application/json" });
  triggerDownload(blob, "apa7-report.json");
});

downloadDocxButton.addEventListener("click", async () => {
  if (!lastJobId) return;
  downloadDocxButton.disabled = true;
  try {
    const bytes = await annotateDocx(lastJobId);
    const blob = new Blob([bytes], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const filename = inputMode === "docx" && docxFilename
      ? docxFilename.replace(/\.docx$/i, "-annotated.docx")
      : "apa7-annotated.docx";
    triggerDownload(blob, filename);
  } catch (err) {
    console.error(err);
    setStatus(`Error generating DOCX: ${err.message || String(err)}`);
  } finally {
    downloadDocxButton.disabled = false;
  }
});

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
