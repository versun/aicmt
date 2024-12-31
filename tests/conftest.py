import sys
import os
import platform
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from git import Repo
import json

root_dir = Path(__file__).parent.parent

sys.path.insert(0, str(root_dir))

@pytest.fixture(params=["Linux", "Darwin", "Windows"], autouse=True)
def platform_system(request, monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: request.param)

# @pytest.fixture(autouse=True)
# def mock_argv():
#     """Mock command line arguments"""
#     with patch.object(sys, "argv", ["aicmt"]):
#         yield


@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = {"api_key": "test-key", "base_url": "https://api.openai.com/v1", "model": "gpt-4"}
    with patch("aicmt.ai_analyzer.load_config", return_value=config), patch("aicmt.config.load_config", return_value=config):
        yield config

@pytest.fixture
def mock_home_dir(tmp_path):
    """Mock home directory"""
    with patch("pathlib.Path.home", return_value=tmp_path):
        yield tmp_path

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