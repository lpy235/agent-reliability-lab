const state = {
  selectedRunId: null,
  runs: [],
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

el("refresh-runs").addEventListener("click", loadRuns);
el("replay-run").addEventListener("click", replaySelectedRun);
el("diff-runs").addEventListener("click", diffRuns);

loadRuns().catch((error) => {
  el("run-summary").className = "summary empty";
  el("run-summary").textContent = error.message;
});
