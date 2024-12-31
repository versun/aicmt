import os
import sys
import pytest
from unittest.mock import patch
import git
from aicmt.cli import AiCommit
from pathlib import Path


def test_help_command(capsys, mock_repo, mock_home_dir):
    """Test help command output"""
    config_file = mock_home_dir / ".config/aicmt/.aicmtrc"
    assert not config_file.exists()
    with patch.object(sys, "argv", ["aicmt", "-h"]):
        with pytest.raises(SystemExit) as e:
            AiCommit(mock_repo).run()
        assert e.value.code == 0

    captured = capsys.readouterr()
    assert "AICMT (AI Commit)" in captured.out
    assert "usage: aicmt [-h] [-v] [-n N]" in captured.out
    assert "-h, --help" in captured.out
    assert "show this help message and exit" in captured.out


def test_version_command(capsys, mock_repo, mock_home_dir):
    """Test version command output"""
    config_file = mock_home_dir / ".config/aicmt/.aicmtrc"
    assert not config_file.exists()
    with patch.object(sys, "argv", ["aicmt", "-v"]):
        with pytest.raises(SystemExit) as e:
            AiCommit(mock_repo).run()
        assert e.value.code == 0
    from aicmt import __version__

    captured = capsys.readouterr()
    assert f"{__version__.VERSION}" in captured.out


def test_no_args_without_repo(tmp_path, mock_home_dir):
    """Test no arguments without a git repository"""
    config_file = mock_home_dir / ".config/aicmt/.aicmtrc"
    assert not config_file.exists()
    os.chdir(tmp_path)
    with patch.object(sys, "argv", ["aicmt"]):
        with pytest.raises(git.exc.InvalidGitRepositoryError) as exc_info:
            AiCommit(tmp_path).run()
        assert str(exc_info.value) == "Not a valid Git repository"


def test_no_config_file(capsys, mock_repo, mock_home_dir):
    """Test no configuration file"""
    config_file = mock_home_dir / ".config/aicmt/.aicmtrc"
    assert not config_file.exists()
    with patch.object(sys, "argv", ["aicmt"]):
        with pytest.raises(SystemExit) as e:
            AiCommit(mock_repo).run()
        assert e.value.code == 0
    captured = capsys.readouterr()
    assert "Please check and update your configuration file." in captured.out
    assert "Auto created configuration file in" in captured.out


def test_auto_create_config(capsys, mock_repo, mock_home_dir):
    """Test no configuration file"""
    config_file = mock_home_dir / ".config/aicmt/.aicmtrc"
    assert not config_file.exists()
    with patch.object(sys, "argv", ["aicmt"]):
        with pytest.raises(SystemExit) as e:
            AiCommit(mock_repo).run()
        assert e.value.code == 0

    assert config_file.exists()
    assert "[openai]" in config_file.read_text()
    assert "api_key = your-api-key-here" in config_file.read_text()
    assert "model = gpt-4o-mini" in config_file.read_text()
    assert "base_url = https://api.openai.com/v1" in config_file.read_text()


def test_read_global_config(capsys, mock_repo, mock_home_dir):
    """Test reading global configuration file"""
    config_file = mock_home_dir / ".config/aicmt/.aicmtrc"
    assert not config_file.exists()

    config_dir = mock_home_dir / ".config/aicmt"
    config_content = """
[openai]
api_key = global-key
model = global-model
base_url = https://api.openai.com/v1
"""
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / ".aicmtrc").write_text(config_content)
    assert (config_dir / ".aicmtrc").exists()
    (Path(mock_repo) / "test.py").write_text("test content")
    with patch.object(sys, "argv", ["aicmt"]):
        with pytest.raises(SystemExit) as e:
            AiCommit(mock_repo).run()
        assert e.value.code == 1

    captured = capsys.readouterr()
    assert "https://api.openai.com/v1" in captured.out
    assert "global-model" in captured.out


def test_no_changes(capsys, mock_repo, mock_home_dir):
    """Test no changes detected"""
    config_dir = mock_home_dir / ".config/aicmt"
    config_content = """
[openai]
api_key = global-key
model = global-model
base_url = https://api.openai.com/v1
"""
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / ".aicmtrc").write_text(config_content)
    assert (config_dir / ".aicmtrc").exists()

    with patch.object(sys, "argv", ["aicmt"]):
        with pytest.raises(SystemExit) as e:
            AiCommit(mock_repo).run()
        assert e.value.code == 0

    captured = capsys.readouterr()
    assert "No changes found" in captured.out


def test_basic_workflow(mock_repo, mock_openai, mock_config):
    """Test basic workflow with unstaged changes"""
    pass


def test_staged_changes_workflow(mock_repo, mock_openai, mock_config):
    """Test workflow with staged changes"""
    pass


def test_error_handling(mock_repo, mock_config):
    """Test error handling when AI analysis fails"""
    pass


def test_push_workflow(mock_repo, mock_openai, mock_config):
    """Test workflow with push operation"""
    pass


def test_modified_file_workflow(mock_repo, mock_openai, mock_config):
    """Test workflow with modified files"""
    pass


def test_deleted_file_workflow(mock_repo, mock_openai, mock_config):
    """Test workflow with deleted files"""
    pass


def test_renamed_file_workflow(mock_repo, mock_openai, mock_config):
    """Test workflow with renamed files"""
    pass
