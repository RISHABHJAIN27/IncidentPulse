import json
from pathlib import Path

import pytest

from app import config

# This file tests a Config class (JSON config per environment) that app/config.py
# does not define; config comes from environment variables instead. Skipped rather
# than deleted: either add Config.load() back or remove this file.
if not hasattr(config, "Config"):
    pytest.skip("app.config.Config is not implemented", allow_module_level=True)

from app.config import Config


def _write_config(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_deserializes_valid_config(monkeypatch, tmp_path):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    _write_config(
        cfg_dir / "prod.json",
        {
            "env": "prod",
            "database": {
                "region_name": "us-east-1",
                "endpoint_url": "http://localhost:8001",
                "aws_access_key_id": "local",
                "aws_secret_access_key": "local",
            },
        },
    )
    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)

    loaded = Config.load("prod")

    assert loaded.env == "prod"
    assert loaded.database.region_name == "us-east-1"
    assert loaded.database.endpoint_url == "http://localhost:8001"
    assert loaded.database.aws_access_key_id == "local"
    assert loaded.database.aws_secret_access_key == "local"


def test_load_raises_for_missing_environment_file(monkeypatch, tmp_path):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)

    with pytest.raises(FileNotFoundError):
        Config.load("staging")


def test_load_raises_for_missing_required_keys(monkeypatch, tmp_path):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    _write_config(
        cfg_dir / "staging.json",
        {
            "env": "staging",
            "database": {
                "region_name": "us-east-1",
                "endpoint_url": "http://localhost:8001",
                "aws_access_key_id": "local",
            },
        },
    )
    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)

    with pytest.raises(TypeError):
        Config.load("staging")
