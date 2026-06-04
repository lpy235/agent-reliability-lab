# Dashboard Design

## Purpose

The dashboard makes saved agent behavior inspectable without requiring curl or direct SQLite access. It is a compact debugging workbench for run lists, trace steps, outputs, replay, and diff.

## Scope

This phase implements:

- `GET /dashboard` HTML entrypoint.
- Static assets under `app/web/`.
- Run list loaded from `GET /runs`.
- Run detail loaded from `GET /runs/{run_id}`.
- Trace timeline cards for each step.
- JSON panels for run output and step events.
- Replay button for the selected run.
- Diff controls for base and candidate run IDs.

This phase does not implement authentication, charts, server-side templates, screenshots, or a production frontend build pipeline.

## UI Shape

The interface is a dense operational dashboard:

- left rail: recent runs
- main panel: selected run summary and trace timeline
- right panel: output JSON, replay action, diff controls

## Acceptance Criteria

- `/dashboard` returns HTML.
- `/static/app.js` and `/static/styles.css` are served.
- Dashboard can load run lists and selected run details through the existing API.
- Tests cover the dashboard route and static asset routes.
- Existing API and harness tests continue to pass.

