"""Pytest environment — no API keys, project root on sys.path."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Ensure imports resolve to this project, not parent git root.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.chdir(ROOT)

SECRET_ENV_KEYS = (
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "VWORLD_API_KEY",
    "DATA_GO_KR_SERVICE_KEY",
    "SENDGRID_API_KEY",
    "EMAIL_ADDRESS",
    "ENABLE_SENDGRID_SEND",
    "VISION_MODEL",
)


@pytest.fixture(autouse=True)
def isolate_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BANDABI_PYTEST", "1")
    for key in SECRET_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv(key, "")


@pytest.fixture
def project_root() -> Path:
    return ROOT


@pytest.fixture
def app_path(project_root: Path) -> Path:
    return project_root / "app.py"
