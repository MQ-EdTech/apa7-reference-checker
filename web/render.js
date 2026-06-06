const SEVERITY_BADGE = {
  error: { label: "ERROR", classes: "bg-red-100 text-red-800" },
  warning: { label: "WARN", classes: "bg-amber-100 text-amber-800" },
  info: { label: "INFO", classes: "bg-slate-100 text-slate-700" },
};

export function renderSummary(report) {
  const cards = [
    { label: "References", value: report.references.length },
    { label: "Citations", value: report.citations.length },
    { label: "Issues", value: report.issues.length },
    { label: "Warnings", value: report.warnings.length },
  ];
  return cards
    .map(
      (c) => `
        <div class="rounded-md border border-slate-200 bg-white p-4">
          <div class="text-xs uppercase tracking-wider text-slate-500">${escapeHtml(c.label)}</div>
          <div class="mt-1 text-2xl font-semibold">${c.value}</div>
        </div>`,
    )
    .join("");
}

export function renderIssues(report) {
  if (report.issues.length === 0) {
    return `<p class="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">No issues found.</p>`;
  }
  return `
    <ul class="space-y-3">
      ${report.issues
        .map(
          (iss) => {
            const badge = SEVERITY_BADGE[iss.severity] || SEVERITY_BADGE.info;
            return `
              <li class="rounded-md border border-slate-200 bg-white p-4">
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badge.classes}">${badge.label}</span>
                  <code class="text-xs text-slate-500">${escapeHtml(iss.code)}</code>
                </div>
                <p class="mt-2 text-sm text-slate-800">${escapeHtml(iss.message)}</p>
                ${iss.suggestion ? `<p class="mt-1 text-sm text-slate-600">&#x21AA; ${escapeHtml(iss.suggestion)}</p>` : ""}
              </li>`;
          },
        )
        .join("")}
    </ul>
  `;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
