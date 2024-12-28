import pytest
from aicmt.config import _merge_configs, _parse_config_file, validate_config, _load_config_file, load_config


def test_merge_configs():
    base = {"api_key": "test_key", "model": "gpt-3.5-turbo", "analysis_prompt": "Default analysis prompt"}
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


def test_parse_config_with_comments(tmp_path):
    """Test parsing configuration file with comments."""
    config_content = """
[openai]
# API configuration
api_key = test_key  # This is a test key
model = gpt-4  ; This is a model setting
base_url = https://test.openai.com  # Custom base URL

[prompts]
# Analysis prompt configuration
analysis_prompt = Test analysis prompt  # Default prompt
"""
    config_file = tmp_path / ".aicmtrc"
    config_file.write_text(config_content)

    result = _parse_config_file(config_file)
    assert result["api_key"] == "test_key"
    assert result["model"] == "gpt-4"
    assert result["base_url"] == "https://test.openai.com"
    assert result["analysis_prompt"] == "Test analysis prompt"


def test_parse_multiline_prompt(tmp_path):
    """Test parsing configuration file with multiline prompt."""
    config_content = """
[openai]
api_key = test_key
model = gpt-4
base_url = https://test.openai.com

[prompts]
analysis_prompt = 
    You are a Git commit expert.
    Requirements:
    1. Group related changes
    2. Use conventional commits
    
    Keep commits reasonably sized.
"""
    config_file = tmp_path / ".aicmtrc"
    config_file.write_text(config_content)

    result = _parse_config_file(config_file)
    expected_prompt = """You are a Git commit expert.
Requirements:
1. Group related changes
2. Use conventional commits

Keep commits reasonably sized."""
    assert result["analysis_prompt"].strip() == expected_prompt.strip()


def test_parse_invalid_config_format(tmp_path):
    """Test parsing invalid configuration file format."""
    config_content = """
Invalid format
api_key = test_key
[invalid section
prompt = test
"""
    config_file = tmp_path / ".aicmtrc"
    config_file.write_text(config_content)

    result = _parse_config_file(config_file)
    assert result == {}


def test_parse_empty_config_file(tmp_path):
    """Test parsing empty configuration file."""
    config_file = tmp_path / ".aicmtrc"
    config_file.write_text("")

    result = _parse_config_file(config_file)
    assert result == {}


def test_parse_config_with_encoding_error(tmp_path):
    """Test parsing configuration file with encoding issues."""
    # Create a binary file with invalid UTF-8 encoding
    config_file = tmp_path / ".aicmtrc"
    with open(config_file, "wb") as f:
        f.write(b"[openai]\napi_key = \xff\xfe invalid utf-8\n")

    result = _parse_config_file(config_file)
    assert result == {}


def test_validate_config():
    valid_config = {"api_key": "test_key", "model": "gpt-4", "base_url": "https://api.openai.com/v1", "analysis_prompt": "Test analysis prompt"}
    validate_config(valid_config)

    invalid_config_without_model = {"api_key": "test_key", "base_url": "https://api.openai.com/v1", "analysis_prompt": "Test analysis prompt"}
    invalid_config_without_api_key = {"model": "gpt-4", "base_url": "https://api.openai.com/v1", "analysis_prompt": "Test analysis prompt"}
    invalid_config_without_base_url = {"api_key": "test_key", "model": "gpt-4", "analysis_prompt": "Test analysis prompt"}
    invalid_config_without_prompt = {"api_key": "test_key", "model": "gpt-4", "base_url": "https://api.openai.com/v1"}

    with pytest.raises(ValueError):
        validate_config(invalid_config_without_model)
    with pytest.raises(ValueError):
        validate_config(invalid_config_without_api_key)
    with pytest.raises(ValueError):
        validate_config(invalid_config_without_base_url)
    with pytest.raises(ValueError):
        validate_config(invalid_config_without_prompt)


def test_validate_config_error():
    """Test configuration validation error handling."""
    # Test missing API key
    with pytest.raises(ValueError, match="OpenAI API key not configured"):
        validate_config({"model": "gpt-4"})

    # Test missing model
    with pytest.raises(ValueError, match="No model specified"):
        validate_config({"api_key": "test_key"})

    # Test invalid base URL
    with pytest.raises(ValueError, match="Invalid API URL format"):
        validate_config({"api_key": "test_key", "model": "gpt-4", "base_url": "not-a-url", "analysis_prompt": "test prompt"})

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

def test_load_cli_config(monkeypatch):
    """Test loading configuration from command line arguments."""
    from aicmt.config import _load_cli_config
    from argparse import Namespace

    # Test with num_commits set
    args = Namespace(num_commits=5)
    monkeypatch.setattr("aicmt.config.parse_args", lambda: args)

    result = _load_cli_config()
    assert result == {"num_commits": 5}

    # Test with no arguments set
    args = Namespace(num_commits=None)
    monkeypatch.setattr("aicmt.config.parse_args", lambda: args)

    result = _load_cli_config()
    assert result == {}


def test_load_config_with_cli_override(monkeypatch):
    """Test load_config function with CLI configuration override."""

    # Mock file config with some base settings
    def mock_load_config_file():
        return {"api_key": "test-api-key", "model": "gpt-3.5-turbo", "base_url": "https://api.openai.com", "analysis_prompt": "Test prompt"}

    # Mock CLI config with num_commits override
    def mock_load_cli_config():
        return {"num_commits": 10}

    monkeypatch.setattr("aicmt.config._load_config_file", mock_load_config_file)
    monkeypatch.setattr("aicmt.config._load_cli_config", mock_load_cli_config)

    config = load_config()

    # Verify CLI num_commits overrides file config
    assert config["num_commits"] == 10
    # Verify other values remain unchanged
    assert config["api_key"] == "test-api-key"
    assert config["model"] == "gpt-3.5-turbo"
    assert config["base_url"] == "https://api.openai.com"
    assert config["analysis_prompt"] == "Test prompt"


def test_load_config_validation_error(monkeypatch):
    """Test load_config function when configuration validation fails."""

    # Mock _load_config_file to return an invalid configuration
    def mock_load_config_file():
        return {
            "model": "gpt-4",
            "analysis_prompt": "Test prompt",
            "base_url": "invalid-url",  # Invalid URL format
        }

    monkeypatch.setattr("aicmt.config._load_config_file", mock_load_config_file)
    monkeypatch.setattr("aicmt.config._load_cli_config", lambda: {})

    with pytest.raises(ValueError) as exc_info:
        load_config()

    assert "Invalid API URL format" in str(exc_info.value)
    assert "The base_url must" in str(exc_info.value)
    assert "Start with http:// or https://" in str(exc_info.value)


def test_validate_config_short_prompt(capsys):
    """Test validation of short analysis prompt."""
    # Test short prompt warning
    config = {
        "api_key": "test_key",
        "model": "gpt-4",
        "base_url": "https://test.openai.com",
        "analysis_prompt": "short",  # 5 characters
    }
    validate_config(config)
    captured = capsys.readouterr()
    assert "Warning: analysis prompt is too short" in captured.out
    assert "(5 characters)" in captured.out

    # Test normal length prompt (no warning)
    config["analysis_prompt"] = "This is a normal length analysis prompt"
    validate_config(config)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_get_xdg_config_home(monkeypatch, tmp_path):
    from aicmt.config import _get_xdg_config_home
    from pathlib import Path

    # Test when XDG_CONFIG_HOME is set
    test_path = str(tmp_path / "config")
    monkeypatch.setenv("XDG_CONFIG_HOME", test_path)
    assert _get_xdg_config_home() == Path(test_path)

    # Test when XDG_CONFIG_HOME is not set
    monkeypatch.delenv("XDG_CONFIG_HOME")
    expected_path = Path.home() / ".config"
    assert _get_xdg_config_home() == expected_path
