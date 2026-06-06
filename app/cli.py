from __future__ import annotations

import argparse
import os

import uvicorn


def _add_server_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db-path", default="runs.db")
    parser.add_argument("--reload", action="store_true")


def _run_server(host: str, port: int, reload: bool) -> None:
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Agent Reliability Lab API and dashboard.")
    _add_server_args(parser)
    args = parser.parse_args()

    os.environ["AGENT_RELIABILITY_DB"] = args.db_path
    _run_server(host=args.host, port=args.port, reload=args.reload)
    return 0


def dashboard_main() -> int:
    parser = argparse.ArgumentParser(description="Open an Agent Reliability Lab dashboard over saved CI artifacts.")
    _add_server_args(parser)
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args()

    os.environ["AGENT_RELIABILITY_DB"] = args.db_path
    os.environ["AGENT_RELIABILITY_REPORTS_DIR"] = args.reports_dir
    _run_server(host=args.host, port=args.port, reload=args.reload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
