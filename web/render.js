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

  // Group by code|message so identical findings collapse into one card.
  const groups = new Map();
  for (const iss of report.issues) {
    const key = `${iss.code}|${iss.message}`;
    if (!groups.has(key)) {
      groups.set(key, {
        code: iss.code,
        severity: iss.severity,
        message: iss.message,
        suggestion: iss.suggestion,
        target_kind: iss.target_kind,
        lines: [],
      });
    }
    if (typeof iss.line === "number") {
      groups.get(key).lines.push(iss.line);
    }
  }

  // Sort groups by severity (error first), then by code.
  const severityOrder = { error: 0, warning: 1, info: 2 };
  const groupList = Array.from(groups.values()).sort((a, b) => {
    const sev = (severityOrder[a.severity] ?? 99) - (severityOrder[b.severity] ?? 99);
    return sev !== 0 ? sev : a.code.localeCompare(b.code);
  });

  return `
    <ul class="space-y-3">
      ${groupList.map((g) => {
        const badge = SEVERITY_BADGE[g.severity] || SEVERITY_BADGE.info;
        const occurrenceBadge =
          g.lines.length > 1
            ? `<span class="ml-auto inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">${g.lines.length} occurrences</span>`
            : "";
        const linesLine =
          g.lines.length > 0
            ? `<p class="mt-2 text-xs text-slate-500">Line${g.lines.length > 1 ? "s" : ""}: ${[...new Set(g.lines)].sort((a, b) => a - b).join(", ")}</p>`
            : "";
        return `
          <li class="rounded-md border border-slate-200 bg-white p-4">
            <div class="flex items-center gap-2">
              <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badge.classes}">${badge.label}</span>
              <code class="text-xs text-slate-500">${escapeHtml(g.code)}</code>
              ${occurrenceBadge}
            </div>
            <p class="mt-2 text-sm text-slate-800">${escapeHtml(g.message)}</p>
            ${g.suggestion ? `<p class="mt-1 text-sm text-slate-600">&#x21AA; ${escapeHtml(g.suggestion)}</p>` : ""}
            ${linesLine}
          </li>`;
      }).join("")}
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
