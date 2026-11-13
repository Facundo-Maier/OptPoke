import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import initialize
from app.main import app


@pytest.fixture
def local_data(monkeypatch, tmp_path):
    monkeypatch.setenv("OPTPOKE_DATA_DIR", str(tmp_path / "private"))
    initialize()
    return tmp_path / "private"


@pytest.fixture
def client(local_data):
    with TestClient(app) as test_client:
        yield test_client
