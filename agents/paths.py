from __future__ import annotations

from importlib import resources
from pathlib import Path


def resolve_demo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.exists() or candidate.is_absolute():
        return candidate

    parts = candidate.parts
    if len(parts) == 1 and parts[0] == "sample_docs":
        return Path(str(resources.files("sample_docs")))
    if len(parts) >= 2 and parts[0] == "evals":
        return Path(str(resources.files("evals").joinpath(*parts[1:])))

    return candidate
