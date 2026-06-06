const PYODIDE_VERSION = "0.26.4";
// Bump WHEEL_CACHE_BUSTER whenever the engine wheel changes so browsers refetch
// instead of serving the old wheel from HTTP cache. (GitHub Pages serves wheels
// with a 10-minute Cache-Control by default, which leaves them cached for hours
// in client browsers.)
const WHEEL_CACHE_BUSTER = "2026-06-06-loosen-website-and-urls";
const ENGINE_WHEEL = `./dist/apa7_validator-0.1.0-py3-none-any.whl?v=${WHEEL_CACHE_BUSTER}`;

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

export async function annotateDocx(jobId) {
  // Reuses the cached pyodide instance — assumes runValidate has already been called.
  const pyodide = await loadPyodideOnce(() => {});
  pyodide.globals.set("job_id_input", jobId);
  const result = pyodide.runPython(`
from apa7_validator.browser import annotate
annotate(job_id_input)
  `);
  // Convert Python bytes to JS Uint8Array.
  const bytes = result.toJs({ create_proxies: false });
  result.destroy();
  return bytes;
}

export async function runValidate(text, format, onProgress) {
  const pyodide = await loadPyodideOnce(onProgress);
  onProgress("Validating…");

  // For Uint8Array input (DOCX bytes), convert explicitly to Python bytes —
  // Pyodide's default conversion wraps typed arrays as JsProxy, which the
  // engine's bytes-expecting code (io.BytesIO, .decode, etc.) rejects with
  // "a bytes-like object is required, not 'pyodide.ffi.JsProxy'".
  // Strings pass through unchanged.
  const sourceForPython =
    text instanceof Uint8Array ? pyodide.toPy(text) : text;

  pyodide.globals.set("source_input", sourceForPython);
  pyodide.globals.set("fmt_input", format);

  const resultJson = await pyodide.runPythonAsync(`
from apa7_validator.browser import run
await run(source_input, fmt_input)
  `);

  return JSON.parse(resultJson);
}
