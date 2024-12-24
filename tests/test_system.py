import os
import pytest
from unittest.mock import patch
from aicmt.cli import AiCommit
from aicmt.git_operations import Change


@pytest.fixture
def system_test_setup(tmp_path):
    """Setup a temporary git repository with test files"""
    current_dir = os.getcwd()
    os.chdir(tmp_path)

    # Initialize git repo
    os.system("git init")
    os.system("git config user.email 'test@example.com'")
    os.system("git config user.name 'Test User'")

    # Create test file
    with open("test_file.py", "w") as f:
        f.write("print('Hello World')")

    yield tmp_path
    os.chdir(current_dir)


def test_full_commit_workflow(system_test_setup, capsys):
    """Test the entire commit workflow from start to finish"""
    with patch("aicmt.config._load_cli_config") as mock_config:
        mock_config.return_value = {
            "api_key": "test_key",
            "model": "test-model",
            "num_commits": 1
        }

        # Create an instance of AiCommit
        assistant = AiCommit()

        # Stage the test file
        os.system("git add test_file.py")

        # Mock AI analysis response
        mock_response = {
            "commit_groups": [{
                "files": ["test_file.py"],
                "commit_message": "feat: add test file",
                "description": "Added test file"
            }]
        }

        with patch("openai.Client") as mock_client:
            mock_completion = mock_client.return_value
            mock_completion.chat.completions.create.return_value.choices = [
                type('obj', (), {
                    'message':
                    type('obj', (), {'content': str(mock_response)})()
                })()
            ]

            # Run the commit workflow
            with patch("rich.prompt.Confirm.ask", return_value=True):
                with pytest.raises(SystemExit) as exc_info:
                    assistant.run()
                assert exc_info.value.code == 0

        # Verify commit was made
        result = os.popen("git log --oneline").read()
        assert "feat: add test file" in result


def test_system_with_multiple_files(system_test_setup):
    """Test handling multiple file changes"""
    # Create multiple test files
    files = ["test1.py", "test2.py", "test3.py"]
    for file in files:
        with open(file, "w") as f:
            f.write(f"print('Test file {file}')")

    os.system("git add .")

    with patch("aicmt.config._load_cli_config") as mock_config:
        mock_config.return_value = {
            "api_key": "test_key",
            "model": "test-model",
            "num_commits": 1
        }

        assistant = AiCommit()

        mock_response = {
            "commit_groups": [{
                "files": files,
                "commit_message": "feat: add multiple test files",
                "description": "Added multiple test files"
            }]
        }

        with patch("openai.Client") as mock_client:
            mock_completion = mock_client.return_value
            mock_completion.chat.completions.create.return_value.choices = [
                type('obj', (), {
                    'message':
                    type('obj', (), {'content': str(mock_response)})()
                })()
            ]

            with patch("rich.prompt.Confirm.ask", return_value=True):
                with pytest.raises(SystemExit) as exc_info:
                    assistant.run()
                assert exc_info.value.code == 0

        result = os.popen("git log --oneline").read()
        assert "feat: add multiple test files" in result
