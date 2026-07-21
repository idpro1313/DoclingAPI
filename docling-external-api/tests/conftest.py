# region MODULE_CONTRACT [DOMAIN(5): Testing; CONCEPT(4): Pytest, Fixtures; TECH(7): pytest]
## @modulecontract
## @purpose pytest configuration for docling-external-api tests.
## @scope Session fixtures, logging setup, attempt counter for Anti-Loop.
## @changes
## LAST_CHANGE: v0.1.0 - Initial creation
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: pytest, conftest, testing, fixtures, session, configuration

import logging
import sys
from pathlib import Path

import pytest

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

_log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory) -> Path:
    """Create temporary directory for test data."""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture(autouse=True)
def reset_logging():
    """Ensure clean logging state for each test."""
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.root.setLevel(logging.WARNING)
    yield
    logging.root.setLevel(logging.WARNING)