import pytest
from aicmt.config import _merge_configs, _parse_config_file, validate_config, _load_config_file, load_config


def test_merge_configs():
    base = {
        "api_key": "test_key",
        "model": "gpt-3.5-turbo",
        "analysis_prompt": "Default analysis prompt"
    }
    override = {"api_key": "new_key", "base_url": "https://custom.openai.com"}

    result = _merge_configs(base, override)
    assert result["api_key"] == "new_key"
    assert result["model"] == "gpt-3.5-turbo"
    assert result["base_url"] == "https://custom.openai.com"
    assert result["analysis_prompt"] == "Default analysis prompt"


def test_parse_config_file(tmp_path):
    config_content = """
[openai]
api_key = test_key
model = gpt-4
base_url = https://test.openai.com

[prompts]
analysis_prompt = Test analysis prompt
"""
    config_file = tmp_path / ".aicmtrc"
    config_file.write_text(config_content)

    result = _parse_config_file(config_file)
    assert result["api_key"] == "test_key"
    assert result["model"] == "gpt-4"
    assert result["base_url"] == "https://test.openai.com"
    assert result["analysis_prompt"] == "Test analysis prompt"


def test_validate_config():
    valid_config = {
        "api_key": "test_key",
        "model": "gpt-4",
        "base_url": "https://api.openai.com/v1",
        "analysis_prompt": "Test analysis prompt"
    }
    validate_config(valid_config)

    invalid_config_without_model = {
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "analysis_prompt": "Test analysis prompt"
    }
    invalid_config_without_api_key = {
        "model": "gpt-4",
        "base_url": "https://api.openai.com/v1",
        "analysis_prompt": "Test analysis prompt"
    }
    invalid_config_without_base_url = {
        "api_key": "test_key",
        "model": "gpt-4",
        "analysis_prompt": "Test analysis prompt"
    }
    invalid_config_without_prompt = {
        "api_key": "test_key",
        "model": "gpt-4",
        "base_url": "https://api.openai.com/v1"
    }

    with pytest.raises(ValueError):
        validate_config(invalid_config_without_model)
    with pytest.raises(ValueError):
        validate_config(invalid_config_without_api_key)
    with pytest.raises(ValueError):
        validate_config(invalid_config_without_base_url)
    with pytest.raises(ValueError):
        validate_config(invalid_config_without_prompt)


def test_load_config_file_global_only(tmp_path, monkeypatch):
    global_config = tmp_path / ".aicmtrc"
    global_config_content = """
[openai]
api_key = global_key
model = gpt-4
base_url = https://test.openai.com

[prompts]
analysis_prompt = Test analysis prompt
"""
    global_config.write_text(global_config_content)
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)

    result = _load_config_file()

    assert result["api_key"] == "global_key"
    assert result["model"] == "gpt-4"
    assert result["base_url"] == "https://test.openai.com"
    assert result["analysis_prompt"] == "Test analysis prompt"


def test_load_config_file_local_only(tmp_path, monkeypatch):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    local_config = work_dir / ".aicmtrc"
    local_config_content = """
[openai]
api_key = local_key
model = gpt-4
base_url = https://test.openai.com

[prompts]
analysis_prompt = Test analysis prompt
"""
    local_config.write_text(local_config_content)
    monkeypatch.chdir(work_dir)

    # monkeypatch.setattr('pathlib.Path.home', lambda: tmp_path)

    result = _load_config_file()

    assert result["api_key"] == "local_key"
    assert result["model"] == "gpt-4"
    assert result["base_url"] == "https://test.openai.com"
    assert result["analysis_prompt"] == "Test analysis prompt"


def test_load_config_file_both_configs(tmp_path, monkeypatch):

    # set up global config
    global_config = tmp_path / ".aicmtrc"
    global_config_content = """
[openai]
api_key = global_key
model = gpt-4
base_url = https://global.openai.com
"""
    global_config.write_text(global_config_content)
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    # set up local config
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    local_config = work_dir / ".aicmtrc"
    local_config_content = """
[openai]
api_key = local_key
model = gpt-3.5-turbo
base_url = https://local.openai.com
"""
    local_config.write_text(local_config_content)
    monkeypatch.chdir(work_dir)

    monkeypatch.setattr("aicmt.config._load_cli_config", lambda: {})
    result = load_config()

    # Local config should override global config except for base_url
    assert result["api_key"] == "local_key"
    assert result["model"] == "gpt-3.5-turbo"
    assert result["base_url"] == "https://local.openai.com"


def test_load_config_file_no_configs(tmp_path, monkeypatch):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setattr("aicmt.config._load_cli_config", lambda: {})
    result = load_config()

    assert result is not None


def test_load_config_priority(tmp_path, monkeypatch):
    # set global config
    global_config = tmp_path / ".aicmtrc"
    global_config_content = """
[openai]
api_key = global_key
model = global model
base_url = https://global.openai.com

[prompts]
analysis_prompt = global prompt
"""
    global_config.write_text(global_config_content)
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    # set local config
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    local_config = work_dir / ".aicmtrc"
    local_config_content = """
[openai]
api_key = local_key
model = local model
base_url = https://local.openai.com

[prompts]
analysis_prompt = local prompt
"""
    local_config.write_text(local_config_content)
    monkeypatch.chdir(work_dir)

    # set command line config
    monkeypatch.setattr(
        "aicmt.config._load_cli_config",
        lambda: {
            "api_key": "cli_key",
            "model": "cli model",
            "base_url": "https://cli.openai.com",
            "analysis_prompt": "cli prompt"
        },
    )

    result = load_config()

    assert result["api_key"] == "cli_key"
    assert result["model"] == "cli model"
    assert result["base_url"] == "https://cli.openai.com"
    assert result["analysis_prompt"] == "cli prompt"

    # remove command line config, validate local config
    monkeypatch.setattr("aicmt.config._load_cli_config", lambda: {})
    result = load_config()

    assert result["api_key"] == "local_key"
    assert result["model"] == "local model"
    assert result["base_url"] == "https://local.openai.com"
    assert result["analysis_prompt"] == "local prompt"

    # remove local config, validate global config
    local_config.unlink()
    result = load_config()

    assert result["api_key"] == "global_key"
    assert result["model"] == "global model"
    assert result["base_url"] == "https://global.openai.com"
    assert result["analysis_prompt"] == "global prompt"

    # remove global config, validate default config
    global_config.unlink()
    result = load_config()

    assert result["model"] == "gpt-4o-mini"
    assert result["base_url"] == "https://api.openai.com/v1"
