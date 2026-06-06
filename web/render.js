const SEVERITY_BADGE = {
  error: { label: "ERROR", classes: "bg-red-100 text-red-800" },
  warning: { label: "WARN", classes: "bg-amber-100 text-amber-800" },
  info: { label: "INFO", classes: "bg-slate-100 text-slate-700" },
};

function humaniseCode(code) {
  if (!code) return "";
  return code
    .replace(/_/g, " ")
    .replace(/^./, (c) => c.toUpperCase());
}

const RULE_SUMMARIES = {
  // "always" rules surface in the overall feedback whenever they fire at all
  // (regardless of how many references trigger them), and their individual
  // per-instance cards are hidden from the details list to avoid duplication.
  references_not_alphabetised: {
    always: "Your reference list is not in alphabetical order.",
  },
  hanging_indent_missing: {
    target: "references",
    half: "Most references lack the APA 7 hanging indent.",
    quarter: "Several references lack the APA 7 hanging indent.",
  },
  journal_italics_missing: {
    target: "references",
    half: "Most journal titles are not italicised.",
    quarter: "Several journal titles are not italicised.",
  },
  book_title_italics_missing: {
    target: "references",
    half: "Most book titles are not italicised.",
    quarter: "Several book titles are not italicised.",
  },
  title_not_sentence_case: {
    target: "references",
    half: "Most reference titles use title case instead of sentence case.",
    quarter: "Several reference titles use title case instead of sentence case.",
  },
  doi_malformed: {
    target: "references",
    half: "Most DOIs are malformed.",
    quarter: "Several DOIs are malformed.",
  },
  citation_without_reference: {
    target: "citations",
    half: "Most in-text citations don't have a matching reference list entry.",
    quarter: "Several in-text citations don't have a matching reference list entry.",
  },
  reference_uncited: {
    target: "references",
    half: "Most reference list entries are not cited in the body.",
    quarter: "Several reference list entries are not cited in the body.",
  },
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

// Rule codes whose per-instance cards are suppressed because they're already
// summarised in the Overall Feedback section.
const ALWAYS_SUMMARISED_CODES = new Set(
  Object.entries(RULE_SUMMARIES)
    .filter(([, summary]) => "always" in summary)
    .map(([code]) => code),
);

export function renderIssues(report) {
  if (report.issues.length === 0) {
    return `<p class="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">No issues found.</p>`;
  }

  // Group by code|message so identical findings collapse into one card.
  // Hide issues whose rule is already summarised in the Overall Feedback section.
  const groups = new Map();
  for (const iss of report.issues) {
    if (ALWAYS_SUMMARISED_CODES.has(iss.code)) continue;
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

  // If filtering left nothing, show the empty-state message.
  if (groups.size === 0) {
    return `<p class="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">No detailed issues — see the Overall feedback above.</p>`;
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
              <span class="text-sm font-medium text-slate-700" title="${escapeHtml(g.code)}">${escapeHtml(humaniseCode(g.code))}</span>
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

export function renderOverall(report) {
  const refCount = report.references.length || 1;
  const citCount = report.citations.length || 1;

  // Count distinct refs/citations per rule code (use position.start as identity).
  const codeCounts = new Map();
  for (const iss of report.issues) {
    const key = iss.code;
    if (!codeCounts.has(key)) codeCounts.set(key, new Set());
    codeCounts.get(key).add(iss.position?.start ?? "");
  }

  const lines = [];
  for (const [code, summary] of Object.entries(RULE_SUMMARIES)) {
    const n = codeCounts.get(code)?.size ?? 0;
    if (n === 0) continue;
    if ("always" in summary) {
      lines.push({ text: summary.always, count: n });
      continue;
    }
    const denom = summary.target === "references" ? refCount : citCount;
    const ratio = n / denom;
    if (ratio >= 0.5) lines.push({ text: summary.half, count: n });
    else if (ratio >= 0.25) lines.push({ text: summary.quarter, count: n });
  }

  if (lines.length === 0) return "";

  return `
    <div class="rounded-md border border-amber-200 bg-amber-50 p-4">
      <h3 class="text-sm font-semibold text-amber-900">Overall feedback</h3>
      <ul class="mt-2 space-y-1 text-sm text-amber-900">
        ${lines.map(l => `<li>• ${escapeHtml(l.text)}</li>`).join("")}
      </ul>
    </div>
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
