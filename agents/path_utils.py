#!/usr/bin/env python3
"""Utilities for resolving project paths consistently across agents."""

from pathlib import Path
import os


def get_project_root() -> Path:
    """
    Resolve ETHUSDT_TradeBot project root.

    Priority:
    1) ETHUSDT_TRADEBOT_ROOT env var
    2) Parent of this file's directory (repo-relative)
    """
    env_root = os.getenv("ETHUSDT_TRADEBOT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    return Path(__file__).resolve().parent.parent
