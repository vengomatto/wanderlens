from pathlib import Path

from wanderlens.config import load_config


def test_config_reads_yaml_and_env(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("data_dir: /tmp/wl-data\nvlm_model: test-model\n")

    cfg = load_config(cfg_file, env={"WANDERLENS_VLM_API_KEY": "secret"})

    assert cfg.data_dir == Path("/tmp/wl-data")
    assert cfg.vlm_model == "test-model"
    assert cfg.api_key == "secret"


def test_config_defaults_without_file():
    cfg = load_config(None, env={"OPENROUTER_API_KEY": "or-key"})

    assert cfg.photos_dir.name == "photos"
    assert cfg.db_path.name == "wanderlens.sqlite3"
    assert cfg.api_key == "or-key"
    assert "tile.openstreetmap.org" in cfg.tile_url


def test_tile_url_is_configurable():
    cfg = load_config(None, env={"WANDERLENS_TILE_URL": "https://tiles.example/{z}/{x}/{y}.png"})

    assert cfg.tile_url == "https://tiles.example/{z}/{x}/{y}.png"
