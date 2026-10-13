from pathlib import Path

from wanderlens.config import load_config


def test_config_reads_yaml_and_env(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("data_dir: /tmp/wl-data\nvlm_model: test-model\n")

    cfg = load_config(cfg_file, env={"WANDERLENS_VLM_API_KEY": "secret"})

    assert cfg.data_dir == Path("/tmp/wl-data")
    assert cfg.vlm_model == "test-model"
    assert cfg.api_key == "secret"


def test_config_defaults_without_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config(None, env={"OPENROUTER_API_KEY": "or-key"})

    assert cfg.photos_dir.name == "photos"
    assert cfg.db_path.name == "wanderlens.sqlite3"
    assert cfg.api_key == "or-key"
    assert "tile.openstreetmap.org" in cfg.tile_url


def test_tile_url_is_configurable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config(None, env={"WANDERLENS_TILE_URL": "https://tiles.example/{z}/{x}/{y}.png"})

    assert cfg.tile_url == "https://tiles.example/{z}/{x}/{y}.png"


def test_config_is_auto_discovered_from_cwd(tmp_path, monkeypatch):
    (tmp_path / "config.yaml").write_text("api_key: auto\nllm_model: auto-model\n")
    monkeypatch.chdir(tmp_path)

    cfg = load_config(None, env={})

    assert cfg.api_key == "auto"
    assert cfg.llm_model == "auto-model"


def test_config_path_from_env(tmp_path):
    path = tmp_path / "custom.yaml"
    path.write_text("api_key: frompath\n")

    cfg = load_config(None, env={"WANDERLENS_CONFIG": str(path)})

    assert cfg.api_key == "frompath"


def test_explicit_config_wins_over_discovery(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text("api_key: cwd\n")
    explicit = tmp_path / "explicit.yaml"
    explicit.write_text("api_key: explicit\n")

    cfg = load_config(explicit, env={})

    assert cfg.api_key == "explicit"
