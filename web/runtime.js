const PYODIDE_VERSION = "0.26.4";
const ENGINE_WHEEL = "./dist/apa7_validator-0.1.0-py3-none-any.whl";

let pyodideReadyPromise = null;

async function loadPyodideOnce(onProgress) {
  if (pyodideReadyPromise) return pyodideReadyPromise;

  pyodideReadyPromise = (async () => {
    onProgress("Loading Python runtime…");
    // pyodide.js exposes loadPyodide as a global after the script loads.
    const script = document.createElement("script");
    script.src = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;
    await new Promise((resolve, reject) => {
      script.onload = resolve;
      script.onerror = () => reject(new Error("Failed to load pyodide.js"));
      document.head.appendChild(script);
    });

    const pyodide = await loadPyodide({
      indexURL: `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`,
    });

    onProgress("Installing dependencies…");
    await pyodide.loadPackage(["micropip", "lxml"]);
    const micropip = pyodide.pyimport("micropip");
    await micropip.install(["python-docx", "structlog"]);

    onProgress("Installing engine…");
    await micropip.install(ENGINE_WHEEL);

    return pyodide;
  })();

  return pyodideReadyPromise;
}

export async function warmup(onProgress) {
  await loadPyodideOnce(onProgress);
}

export async function runValidate(text, format, onProgress) {
  const pyodide = await loadPyodideOnce(onProgress);
  onProgress("Validating…");

  pyodide.globals.set("source_input", text);
  pyodide.globals.set("fmt_input", format);

  const resultJson = await pyodide.runPythonAsync(`
from apa7_validator.browser import run
await run(source_input, fmt_input)
  `);

  return JSON.parse(resultJson);
}
