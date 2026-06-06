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

const RUBRIC_CHECKS = [
  {
    id: "source_count",
    label: "Uses ≥10 sources",
    check: (report) => {
      const n = report.references.length;
      if (n === 0) return { status: "fail", note: "No references parsed." };
      const belowMin = report.issues.some((i) => i.code === "reference_count_below_minimum");
      if (belowMin) return { status: "fail", note: `Found ${n} sources; rubric expects at least 10.` };
      return { status: "pass", note: `${n} sources found.` };
    },
  },
  {
    id: "alphabetical",
    label: "Reference list in alphabetical order",
    check: (report) => {
      const fail = report.issues.some((i) => i.code === "references_not_alphabetised");
      return fail
        ? { status: "fail", note: "Sort references by first author's surname." }
        : { status: "pass" };
    },
  },
  {
    id: "complete",
    label: "Reference list is complete",
    check: (report) => {
      const orphans = report.issues.filter((i) => i.code === "citation_without_reference").length;
      const uncited = report.issues.filter((i) => i.code === "reference_uncited").length;
      if (orphans > 0 && uncited > 0) {
        return { status: "fail", note: `${orphans} citation(s) without a reference; ${uncited} unused reference(s).` };
      }
      if (orphans > 0) return { status: "fail", note: `${orphans} citation(s) without a matching reference list entry.` };
      if (uncited > 0) return { status: "partial", note: `${uncited} reference(s) appear in the list but aren't cited in the body.` };
      return { status: "pass" };
    },
  },
  {
    id: "hanging",
    label: "Reference list uses hanging indent",
    check: (report) => {
      const n = report.issues.filter((i) => i.code === "hanging_indent_missing").length;
      if (n === 0) return { status: "pass" };
      const refCount = report.references.length;
      if (refCount > 0 && n / refCount >= 0.5) return { status: "fail", note: `${n} of ${refCount} references lack hanging indent.` };
      return { status: "partial", note: `${n} reference(s) lack hanging indent.` };
    },
  },
  {
    id: "no_other_styles",
    label: "No phrases from other referencing styles",
    check: (report) => {
      const codes = ["deprecated_retrieved_from", "deprecated_accessed_date", "deprecated_no_publisher_marker", "deprecated_ibid"];
      const found = report.issues.filter((i) => codes.includes(i.code));
      if (found.length === 0) return { status: "pass" };
      const labels = [...new Set(found.map((i) => i.code.replace("deprecated_", "").replace(/_/g, " ")))];
      return { status: "fail", note: `Detected: ${labels.join(", ")}.` };
    },
  },
  {
    id: "no_library_proxy",
    label: "References cite canonical sources (not library proxies)",
    check: (report) => {
      const n = report.issues.filter((i) => i.code === "reference_uses_library_proxy_url").length;
      if (n === 0) return { status: "pass" };
      return {
        status: "fail",
        note: `${n} reference${n > 1 ? "s use" : " uses"} a library-proxy URL — replace with the canonical source.`,
      };
    },
  },
  {
    id: "source_quality",
    label: "Source quality",
    check: (report) => {
      const tier1 = report.references.filter((r) => r.tier === 1).length;
      const tier3 = report.references.filter((r) => r.tier === 3).length;
      const note = `Tier 1 (peer-reviewed / books): ${tier1}. Tier 3 (other / unverified): ${tier3}.`;
      if (tier1 >= 5) return { status: "pass", note };
      if (tier1 >= 3) return { status: "partial", note };
      return { status: "fail", note: note + " Aim for at least 5 Tier 1 sources." };
    },
  },
  // One criterion not yet automated — note it as "manual check" so students
  // know it still applies.

  {
    id: "quote_pages",
    label: "Direct-quote citations include page numbers",
    check: () => ({
      status: "manual",
      note: "Direct-quote detection is not yet supported. Confirm page numbers manually for any quoted passages.",
    }),
  },
];

const RUBRIC_STATUS_BADGE = {
  pass: { label: "✓", classes: "bg-emerald-100 text-emerald-800" },
  fail: { label: "✗", classes: "bg-red-100 text-red-800" },
  partial: { label: "~", classes: "bg-amber-100 text-amber-800" },
  manual: { label: "i", classes: "bg-slate-100 text-slate-700" },
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
// covered by a rubric line in the Overall section.
const RUBRIC_SUPPRESSED_CODES = new Set([
  "references_not_alphabetised",
  "reference_count_below_minimum",
  "deprecated_retrieved_from",
  "deprecated_accessed_date",
  "deprecated_no_publisher_marker",
  "deprecated_ibid",
  "reference_uses_library_proxy_url",
]);

function extractInstanceLabel(message) {
  if (!message) return "";
  const match = message.match(/'([^']+)'/);
  return match ? match[1] : message;
}

export function renderIssues(report) {
  if (report.issues.length === 0) {
    return `<p class="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">No issues found.</p>`;
  }

  // Group by code only. Within each code, collect unique instance labels with their lines.
  const groups = new Map();
  for (const iss of report.issues) {
    if (RUBRIC_SUPPRESSED_CODES.has(iss.code)) continue;
    if (!groups.has(iss.code)) {
      groups.set(iss.code, {
        code: iss.code,
        severity: iss.severity,
        suggestion: iss.suggestion,
        instances: new Map(), // label -> Set(lines)
      });
    }
    const g = groups.get(iss.code);
    const label = extractInstanceLabel(iss.message);
    if (!g.instances.has(label)) {
      g.instances.set(label, new Set());
    }
    if (typeof iss.line === "number") {
      g.instances.get(label).add(iss.line);
    }
  }

  if (groups.size === 0) {
    return `<p class="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">No detailed issues — see the Overall feedback above.</p>`;
  }

  const severityOrder = { error: 0, warning: 1, info: 2 };
  const groupList = Array.from(groups.values()).sort((a, b) => {
    const sev = (severityOrder[a.severity] ?? 99) - (severityOrder[b.severity] ?? 99);
    return sev !== 0 ? sev : a.code.localeCompare(b.code);
  });

  return `
    <ul class="space-y-3">
      ${groupList.map((g) => {
        const badge = SEVERITY_BADGE[g.severity] || SEVERITY_BADGE.info;
        const totalOccurrences = Array.from(g.instances.values()).reduce(
          (acc, lineSet) => acc + Math.max(lineSet.size, 1),
          0,
        );
        const occurrenceBadge =
          totalOccurrences > 1
            ? `<span class="ml-auto inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">${totalOccurrences} occurrences</span>`
            : "";
        const instanceItems = Array.from(g.instances.entries())
          .map(([label, lineSet]) => {
            const lines = Array.from(lineSet).sort((a, b) => a - b);
            const lineStr =
              lines.length > 0
                ? ` <span class="text-xs text-slate-500">— line${lines.length > 1 ? "s" : ""} ${lines.join(", ")}</span>`
                : "";
            return `<li class="text-sm text-slate-700">${escapeHtml(label)}${lineStr}</li>`;
          })
          .join("");
        return `
          <li class="rounded-md border border-slate-200 bg-white p-4">
            <div class="flex items-center gap-2">
              <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badge.classes}">${badge.label}</span>
              <span class="text-sm font-medium text-slate-700" title="${escapeHtml(g.code)}">${escapeHtml(humaniseCode(g.code))}</span>
              ${occurrenceBadge}
            </div>
            <ul class="mt-2 list-disc pl-5 space-y-1">${instanceItems}</ul>
            ${g.suggestion ? `<p class="mt-2 text-sm text-slate-600">↪ ${escapeHtml(g.suggestion)}</p>` : ""}
          </li>`;
      }).join("")}
    </ul>
  `;
}

export function generateFeedback(report) {
  const lines = [];
  lines.push("APA 7 Referencing Feedback");
  lines.push("");

  // Build the rubric line-items using the same RUBRIC_CHECKS evaluation logic
  // as renderOverall, but as plain-text bullets.
  const checks = RUBRIC_CHECKS.map((c) => ({ label: c.label, result: c.check(report) }));
  for (const c of checks) {
    const symbol = ({ pass: "✓", fail: "✗", partial: "~", manual: "i" })[c.result.status] || "i";
    let line = `${symbol} ${c.label}`;
    if (c.result.note) {
      line += ` — ${c.result.note}`;
    }
    lines.push(line);
  }

  // Then list the specific orphan citations / typos that need addressing.
  // Reuse the same grouping logic as renderIssues so this matches the UI.
  const groups = new Map();
  for (const iss of report.issues) {
    if (RUBRIC_SUPPRESSED_CODES.has(iss.code)) continue;
    if (!groups.has(iss.code)) {
      groups.set(iss.code, { code: iss.code, suggestion: iss.suggestion, instances: new Map() });
    }
    const g = groups.get(iss.code);
    const label = extractInstanceLabel(iss.message);
    if (!g.instances.has(label)) g.instances.set(label, new Set());
    if (typeof iss.line === "number") g.instances.get(label).add(iss.line);
  }

  if (groups.size > 0) {
    lines.push("");
    lines.push("Specific items to address:");
    for (const g of groups.values()) {
      lines.push("");
      lines.push(`• ${humaniseCode(g.code)}:`);
      for (const [label, lineSet] of g.instances.entries()) {
        const sortedLines = Array.from(lineSet).sort((a, b) => a - b);
        const lineStr = sortedLines.length > 0
          ? ` (line${sortedLines.length > 1 ? "s" : ""} ${sortedLines.join(", ")})`
          : "";
        lines.push(`    - ${label}${lineStr}`);
      }
      if (g.suggestion) {
        lines.push(`    Fix: ${g.suggestion}`);
      }
    }
  }

  lines.push("");
  lines.push("---");
  lines.push("Generated by the APA 7 Validator (https://mq-edtech.github.io/apa7-reference-checker/).");

  return lines.join("\n");
}

export function renderOverall(report) {
  const checks = RUBRIC_CHECKS.map((c) => ({ label: c.label, result: c.check(report) }));
  return `
    <div class="rounded-md border border-slate-200 bg-white p-4">
      <h3 class="text-sm font-semibold text-slate-900">APA 7 rubric check</h3>
      <p class="mt-1 text-xs text-slate-500">A first-pass against your assignment's APA 7 rubric. Items marked <span class="font-medium">i</span> need a manual check.</p>
      <ul class="mt-3 space-y-2 text-sm">
        ${checks.map((c) => {
          const badge = RUBRIC_STATUS_BADGE[c.result.status] || RUBRIC_STATUS_BADGE.manual;
          return `
            <li class="flex items-start gap-3">
              <span class="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${badge.classes}">${badge.label}</span>
              <div class="flex-1">
                <div class="font-medium text-slate-900">${escapeHtml(c.label)}</div>
                ${c.result.note ? `<div class="mt-0.5 text-xs text-slate-600">${escapeHtml(c.result.note)}</div>` : ""}
              </div>
            </li>`;
        }).join("")}
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
