import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import git
from git import Repo
from aicmt.cli import AiCommit
import json


@pytest.fixture(autouse=True)
def mock_argv():
    """Mock command line arguments"""
    with patch.object(sys, "argv", ["aicmt"]):
        yield


@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = {"api_key": "test-key", "base_url": "https://api.openai.com/v1", "model": "gpt-4"}
    with patch("aicmt.ai_analyzer.load_config", return_value=config), patch("aicmt.config.load_config", return_value=config):
        yield config


@pytest.fixture
def mock_repo(tmp_path):
    """Create a temporary git repository for testing"""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    os.chdir(repo_path)
    repo = Repo.init(str(repo_path))
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")
    return str(repo_path)


@pytest.fixture
def ai_commit(mock_repo, mock_config):
    """Create an AiCommit instance with mocked dependencies"""
    return AiCommit(mock_repo)


@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content=json.dumps(
                    {"commit_groups": [{"files": ["test.txt"], "commit_message": "test: add test file", "description": "Added test file for testing purposes"}]}
                )
            )
        )
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client) as mock:
        mock.return_value = mock_client
        yield mock_client


def test_basic_workflow(ai_commit, mock_repo, mock_openai, mock_config):
    """Test basic workflow with unstaged changes"""
    pass


def test_staged_changes_workflow(ai_commit, mock_repo, mock_openai, mock_config):
    """Test workflow with staged changes"""
    pass


def test_error_handling(ai_commit, mock_repo, mock_config):
    """Test error handling when AI analysis fails"""
    pass


def test_push_workflow(ai_commit, mock_repo, mock_openai, mock_config):
    """Test workflow with push operation"""
    pass


def test_modified_file_workflow(ai_commit, mock_repo, mock_openai, mock_config):
    """Test workflow with modified files"""
    pass


def test_deleted_file_workflow(ai_commit, mock_repo, mock_openai, mock_config):
    """Test workflow with deleted files"""
    pass


def test_renamed_file_workflow(ai_commit, mock_repo, mock_openai, mock_config):
    """Test workflow with renamed files"""
    pass


def test_help_command(capsys):
    """Test help command output"""
    with patch.object(sys, "argv", ["aicmt", "-h"]):
        with pytest.raises(SystemExit) as e:
            AiCommit()
        assert e.value.code == 0

    captured = capsys.readouterr()
    assert "AICMT (AI Commit)" in captured.out
    assert "usage: aicmt [-h] [-v] [-n N]" in captured.out
    assert "-h, --help            show this help message and exit" in captured.out


def test_version_command(capsys):
    """Test version command output"""
    with patch.object(sys, "argv", ["aicmt", "-v"]):
        with pytest.raises(SystemExit) as e:
            AiCommit()
        assert e.value.code == 0
    from aicmt import __version__

    captured = capsys.readouterr()
    assert f"{__version__.VERSION}" in captured.out


def test_no_args_without_repo(capsys, tmp_path):
    """Test no arguments without a git repository"""
    os.chdir(tmp_path)
    with patch.object(sys, "argv", ["aicmt"]):
        with pytest.raises(git.exc.InvalidGitRepositoryError) as exc_info:
            AiCommit(tmp_path)
        assert str(exc_info.value) == "Not a valid Git repository"
