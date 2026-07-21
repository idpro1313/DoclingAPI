"""Pytest configuration and fixtures for docling-external-api tests."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import pytest

package_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(package_path))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)

os.environ.setdefault("DOCLING_SERVE_URL", "http://localhost:5001")
os.environ.setdefault("EXTERNAL_API_PORT", "5002")


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config singleton between tests."""
    import src.config as config_module
    config_module._config_instance = None
    yield
    config_module._config_instance = None