"""Configuration helpers that never read local key files directly."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _load_dotenv_once() -> None:
    """Load project-root .env into os.environ (values are never logged here)."""
    try:
        from dotenv import load_dotenv

        root = Path(__file__).resolve().parents[1]
        load_dotenv(root / ".env", override=False)
    except Exception:
        pass


_load_dotenv_once()

CONFIG_STATUS_KEYS = (
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "VWORLD_API_KEY",
    "DATA_GO_KR_SERVICE_KEY",
    "SENDGRID_API_KEY",
    "EMAIL_ADDRESS",
    "ENABLE_SENDGRID_SEND",
    "VISION_MODEL",
)

TRUE_STRINGS = {"true"}


def get_secret(name: str, default: Any = None) -> Any:
    """Read a value from st.secrets first, then os.environ; return default on any failure."""
    try:
        import streamlit as st

        value = st.secrets.get(name, None)
        if value not in (None, ""):
            return value
    except Exception:
        pass

    try:
        value = os.environ.get(name)
        if value not in (None, ""):
            return value
    except Exception:
        pass

    return default


def get_bool_secret(name: str, default: bool = False) -> bool:
    """Return True only for boolean True or the string 'true'."""
    value = get_secret(name, None)
    if value is None:
        return default
    if isinstance(value, bool):
        return bool(value)
    return str(value).strip().lower() in TRUE_STRINGS


def get_config_status(name: str) -> str:
    """Return a safe status label without exposing, masking, or measuring the value."""
    if name == "ENABLE_SENDGRID_SEND":
        return "enabled" if get_bool_secret(name, False) else "disabled"
    return "configured" if get_secret(name, None) not in (None, "") else "missing_key"


def list_config_status() -> dict[str, str]:
    """Return safe setting states only. Actual values are never returned."""
    return {key: get_config_status(key) for key in CONFIG_STATUS_KEYS}


def get_setting(name: str, default: Any = "") -> Any:
    """Backward-compatible alias for earlier modules."""
    return get_secret(name, default)


def get_bool_setting(name: str, default: bool = False) -> bool:
    """Backward-compatible alias for earlier modules."""
    return get_bool_secret(name, default)


def configured(name: str) -> bool:
    """Backward-compatible boolean status helper."""
    return get_config_status(name) in {"configured", "enabled"}
