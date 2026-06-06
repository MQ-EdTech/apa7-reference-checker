"""Shared pytest fixtures for the engine test suite."""

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_path() -> Path:
    return FIXTURE_DIR
