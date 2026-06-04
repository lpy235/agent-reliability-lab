from __future__ import annotations

import argparse
import os

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Agent Reliability Lab API and dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db-path", default="runs.db")
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    os.environ["AGENT_RELIABILITY_DB"] = args.db_path
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
