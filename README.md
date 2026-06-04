# Agent Reliability Lab

Agent Reliability Lab is a lightweight evaluation and observability toolkit for LLM agents. It focuses on making agent behavior recordable, inspectable, and regression-testable instead of treating each run as a black box.

## What It Will Provide

- Structured traces for agent runs and intermediate steps
- SQLite-backed run storage
- Local-document Docs QA agent for RAG evaluation
- JSONL regression test cases
- RAG groundedness and citation checks
- Markdown eval reports for prompt and model changes
- FastAPI endpoints for manual run inspection

## Current Status

This repository is currently in the design and MVP planning stage. The first implementation target is a traceable Docs QA agent with SQLite storage, JSONL evals, Markdown reports, and a small FastAPI API.

## Project Documents

- [Project overview](Agent_Reliability_Lab_项目说明.md)
- [MVP design spec](docs/superpowers/specs/2026-06-04-agent-reliability-lab-mvp-design.md)
- [MVP implementation plan](docs/superpowers/plans/2026-06-04-agent-reliability-lab-mvp.md)

## Planned Tech Stack

- Python
- FastAPI
- SQLite
- pytest
- OpenAI-compatible LLM API

## Scope

The MVP focuses on agent reliability engineering: tracing, RAG evaluation, regression testing, and inspectable reports. It intentionally avoids private user-memory systems, proactive companion behavior, or unrelated personal-agent product concepts.

