const state = {
  activeView: "runs",
  selectedRunId: null,
  runs: [],
  reports: null,
};

const el = (id) => document.getElementById(id);

function pretty(value) {
  return JSON.stringify(value ?? {}, null, 2);
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${text}`);
  }
  return response.json();
}

async function loadRuns() {
  const data = await fetchJson("/runs?limit=50");
  state.runs = data.runs || [];
  el("run-count").textContent = String(state.runs.length);
  renderRuns();
  if (!state.selectedRunId && state.runs.length) {
    await selectRun(state.runs[0].run_id);
  }
}

async function loadReports() {
  const data = await fetchJson("/reports/evals");
  state.reports = data;
  renderReports();
}

function switchView(view) {
  state.activeView = view;
  el("runs-view").classList.toggle("hidden", view !== "runs");
  el("reports-view").classList.toggle("hidden", view !== "reports");
  el("show-runs").classList.toggle("active", view === "runs");
  el("show-reports").classList.toggle("active", view === "reports");

  if (view === "reports" && !state.reports) {
    loadReports().catch(showReportError);
  }
}

function renderRuns() {
  const list = el("run-list");
  list.innerHTML = "";
  for (const run of state.runs) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `run-card${run.run_id === state.selectedRunId ? " selected" : ""}`;
    button.innerHTML = `
      <strong>${run.agent_name}</strong>
      <span class="meta">${run.status} · ${run.metrics?.latency_ms ?? "?"} ms</span>
      <span class="meta">${run.run_id}</span>
    `;
    button.addEventListener("click", () => selectRun(run.run_id));
    list.appendChild(button);
  }
}

function renderReports() {
  if (!state.reports) return;
  el("reports-dir").textContent = state.reports.reports_dir || "reports";
  renderEvalReports(state.reports.evals || []);
  renderBaseline(state.reports.baseline || {});
}

function renderEvalReports(reports) {
  const list = el("eval-report-list");
  list.innerHTML = "";
  for (const report of reports) {
    const summary = report.summary || {};
    const article = document.createElement("article");
    article.className = "report-card";
    article.innerHTML = `
      <div class="report-card-header">
        <div>
          <strong>${report.label}</strong>
          <div class="meta">${report.available ? `Generated ${report.generated_at || "unknown"}` : "Run arl-harness to generate this report."}</div>
        </div>
        <span class="status-pill ${summary.failed ? "failed" : report.available ? "passed" : ""}">
          ${report.available ? `${formatRate(summary.pass_rate)} pass` : "Unavailable"}
        </span>
      </div>
      <div class="metric-grid">
        ${metric("Total", summary.total)}
        ${metric("Passed", summary.passed)}
        ${metric("Failed", summary.failed)}
        ${metric("Pass rate", formatRate(summary.pass_rate))}
      </div>
      <div class="case-table-wrap">
        ${renderCaseTable(report.results || [])}
      </div>
    `;
    list.appendChild(article);
  }
}

function renderBaseline(baseline) {
  const summary = baseline.summary || {};
  el("baseline-status").textContent = baseline.available ? "Available" : "Unavailable";
  el("baseline-status").className = `status-pill ${summary.regressions ? "failed" : baseline.available ? "passed" : ""}`;
  el("baseline-summary").innerHTML = [
    metric("Shared", summary.shared),
    metric("Regressions", summary.regressions),
    metric("Improvements", summary.improvements),
    metric("Added", summary.added),
    metric("Removed", summary.removed),
    metric("Candidate", summary.candidate_total),
  ].join("");

  const changes = [
    ...baselineChangeItems("Regression", baseline.regressions || []),
    ...baselineChangeItems("Improvement", baseline.improvements || []),
    ...baselineChangeItems("Added", baseline.added || []),
    ...baselineChangeItems("Removed", baseline.removed || []),
  ];
  el("baseline-changes").innerHTML = changes.length
    ? changes.join("")
    : `<div class="empty-state">${baseline.available ? "No baseline changes detected." : "Generate baseline-comparison.json to see changes."}</div>`;
}

async function selectRun(runId) {
  state.selectedRunId = runId;
  renderRuns();
  const data = await fetchJson(`/runs/${runId}`);
  renderRunDetail(data.run, data.steps || []);
}

function renderRunDetail(run, steps) {
  const replaySupported = run.agent_name === "docs_qa";
  el("replay-run").disabled = !replaySupported;
  el("base-run-id").value = run.run_id;
  el("candidate-run-id").value = "";
  el("run-summary").className = "summary";
  el("run-summary").innerHTML = `
    <strong>${run.agent_name}</strong>
    <div class="meta">${run.status} · ${run.run_id}</div>
    <div class="meta">Started ${run.started_at || "unknown"}</div>
  `;
  el("run-output").textContent = pretty(run.output);
  el("replay-output").textContent = replaySupported ? "{}" : "Replay is currently available for docs_qa runs.";

  const list = el("step-list");
  list.innerHTML = "";
  for (const step of steps) {
    const card = document.createElement("article");
    card.className = "step-card";
    card.innerHTML = `
      <strong>${step.name}</strong>
      <div class="meta">${step.latency_ms ?? "?"} ms · ${step.reason_tags?.join(", ") || "no tags"}</div>
      <pre>${pretty({
        state_before: step.state_before,
        events: step.events,
        decision: step.decision,
        state_after: step.state_after,
      })}</pre>
    `;
    list.appendChild(card);
  }
}

async function replaySelectedRun() {
  if (!state.selectedRunId) return;
  const result = await fetchJson(`/runs/${state.selectedRunId}/replay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fixed_context: el("fixed-context").checked }),
  });
  el("replay-output").textContent = pretty(result);
  el("candidate-run-id").value = result.replay_run_id;
  await loadRuns();
}

async function diffRuns() {
  const base = el("base-run-id").value.trim();
  const candidate = el("candidate-run-id").value.trim();
  if (!base || !candidate) {
    el("diff-output").textContent = "Provide both run IDs.";
    return;
  }
  const result = await fetchJson(`/runs/diff?base_run_id=${encodeURIComponent(base)}&candidate_run_id=${encodeURIComponent(candidate)}`);
  el("diff-output").textContent = pretty(result);
}

function metric(label, value) {
  return `
    <div class="metric">
      <span>${label}</span>
      <strong>${value ?? 0}</strong>
    </div>
  `;
}

function formatRate(value) {
  if (typeof value !== "number") return "0%";
  return `${Math.round(value * 100)}%`;
}

function renderCaseTable(results) {
  if (!results.length) {
    return `<div class="empty-state">No cases available.</div>`;
  }
  const rows = results.map((result) => `
    <tr>
      <td>${result.case_id || "-"}</td>
      <td>${result.agent || "-"}</td>
      <td><span class="status-pill ${result.passed ? "passed" : "failed"}">${result.passed ? "PASS" : "FAIL"}</span></td>
      <td>${result.latency_ms ?? "?"} ms</td>
      <td>${(result.failed_checks || []).join(", ") || "-"}</td>
    </tr>
  `).join("");
  return `
    <table>
      <thead>
        <tr>
          <th>Case</th>
          <th>Agent</th>
          <th>Status</th>
          <th>Latency</th>
          <th>Failed checks</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function baselineChangeItems(kind, items) {
  return items.map((item) => {
    const failedChecks = item.new_failed_checks || item.failed_checks || item.after?.failed_checks || [];
    return `
      <div class="case-change">
        <strong>${kind}: ${item.case_id || "-"}</strong>
        <span class="meta">${failedChecks.join(", ") || "no failed checks"}</span>
      </div>
    `;
  });
}

function refreshActiveView() {
  if (state.activeView === "reports") {
    loadReports().catch(showReportError);
    return;
  }
  loadRuns().catch(showRunError);
}

function showRunError(error) {
  el("run-summary").className = "summary empty";
  el("run-summary").textContent = error.message;
}

function showReportError(error) {
  el("eval-report-list").innerHTML = `<div class="empty-state">${error.message}</div>`;
}

el("refresh-dashboard").addEventListener("click", refreshActiveView);
el("show-runs").addEventListener("click", () => switchView("runs"));
el("show-reports").addEventListener("click", () => switchView("reports"));
el("replay-run").addEventListener("click", replaySelectedRun);
el("diff-runs").addEventListener("click", diffRuns);

loadRuns().catch(showRunError);
