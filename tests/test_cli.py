import pytest
from git import Repo
from unittest.mock import patch
from aicmt.cli import AiCommit, cli
from aicmt.git_operations import Change


@pytest.fixture
def assistant(monkeypatch, tmp_path):
    monkeypatch.setattr("aicmt.config._load_cli_config", lambda: {})
    Repo.init(tmp_path)
    return AiCommit(repo_path=str(tmp_path))


def test_git_commit_assistant_init(assistant):
    assert hasattr(assistant, "git_ops")
    assert hasattr(assistant, "ai_analyzer")
    assert hasattr(assistant, "cli")


def test_run_keyboard_interrupt(assistant, capsys):
    """Test that KeyboardInterrupt is handled properly in AiCommit.run"""
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]

    with patch.multiple(assistant.git_ops, get_unstaged_changes=lambda: changes, get_current_branch=lambda: "main"):
        with patch.object(assistant.ai_analyzer, "analyze_changes", side_effect=KeyboardInterrupt()):
            with pytest.raises(SystemExit):
                assistant.run()

    captured = capsys.readouterr()
    assert "Operation cancelled by user" in captured.out


def test_run_no_changes(assistant):
    with patch("aicmt.git_operations.GitOperations.get_unstaged_changes", return_value=[]):
        with pytest.raises(SystemExit):
            assistant.run()


@patch("rich.prompt.Confirm.ask")
def test_run_successful_flow(mock_confirm, assistant):
    # Mock necessary dependencies
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit", "description": "test description"}]

    # Mock user confirmation to always return True
    mock_confirm.return_value = True

    with patch.multiple(
        assistant.git_ops,
        get_unstaged_changes=lambda: changes,
        get_current_branch=lambda: "main",
        stage_files=lambda x: None,
        commit_changes=lambda x: None,
        push_changes=lambda: None,
    ):
        with patch.multiple(assistant.ai_analyzer, analyze_changes=lambda x: commit_groups):
            with patch.multiple(assistant.cli, display_commit_groups=lambda x: commit_groups, confirm_push=lambda: True):
                assistant.run()


@patch("rich.prompt.Confirm.ask")
def test_run_commit_error(mock_confirm, assistant):
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit", "description": "test description"}]

    # Mock user confirmation
    mock_confirm.return_value = True

    with patch.multiple(
        assistant.git_ops,
        get_unstaged_changes=lambda: changes,
        get_current_branch=lambda: "main",
        stage_files=lambda x: None,
        commit_changes=lambda x: exec('raise Exception("Commit failed")'),
    ):
        with patch.multiple(assistant.ai_analyzer, analyze_changes=lambda x: commit_groups):
            with patch.multiple(assistant.cli, display_commit_groups=lambda x: commit_groups):
                assistant.run()


@patch("rich.prompt.Confirm.ask")
def test_run_push_error(mock_confirm, assistant):
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit", "description": "test description"}]

    # Mock user confirmation
    mock_confirm.return_value = True

    with patch.multiple(
        assistant.git_ops,
        get_unstaged_changes=lambda: changes,
        get_current_branch=lambda: "main",
        stage_files=lambda x: None,
        commit_changes=lambda x: None,
        push_changes=lambda: exec('raise Exception("Push failed")'),
    ):
        with patch.multiple(assistant.ai_analyzer, analyze_changes=lambda x: commit_groups):
            with patch.multiple(assistant.cli, display_commit_groups=lambda x: commit_groups, confirm_push=lambda: True):
                assistant.run()


@patch("aicmt.cli.parse_args")
@patch("aicmt.cli.AiCommit")
def test_cli_runtime_error(mock_assistant, mock_parse_args, capsys):
    # Mock AiCommit to raise a runtime error
    mock_instance = mock_assistant.return_value
    mock_instance.run.side_effect = Exception("Simulated runtime error")

    # Call cli function and expect system exit
    with pytest.raises(SystemExit) as exc_info:
        cli()

    # Check exit code
    assert exc_info.value.code == 1

    # Check error message
    captured = capsys.readouterr()
    assert "Error: Simulated runtime error" in captured.out


@patch("rich.prompt.Confirm.ask")
def test_run_no_approved_groups(mock_confirm, assistant):
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit", "description": "test description"}]

    # Mock user confirmation
    mock_confirm.return_value = True

    with patch.multiple(assistant.git_ops, get_unstaged_changes=lambda: changes, get_current_branch=lambda: "main"):
        with patch.multiple(assistant.ai_analyzer, analyze_changes=lambda x: commit_groups):
            with patch.multiple(assistant.cli, display_commit_groups=lambda x: []):
                assistant.run()


def test_create_new_commits(assistant, capsys):
    commit_groups = [{"files": [], "commit_message": "test commit", "description": "test description"}]
    assistant._create_new_commits(commit_groups)
    captured = capsys.readouterr()
    assert "No files to stage!" in captured.out


def test_commit_creation_failure(assistant, capsys):
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit", "description": "test description"}]

    with patch.multiple(
        assistant.git_ops,
        get_unstaged_changes=lambda: changes,
        get_current_branch=lambda: "main",
        stage_files=lambda x: None,
        commit_changes=lambda x: exec('raise Exception("Failed to create commit")'),
    ):
        with patch.multiple(assistant.ai_analyzer, analyze_changes=lambda x: commit_groups):
            with patch.multiple(assistant.cli, display_commit_groups=lambda x: commit_groups):
                with pytest.raises(SystemExit):
                    assistant.run()

                captured = capsys.readouterr()
                assert "Failed to create commit" in captured.out


def test_push_confirmation_declined(assistant):
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit", "description": "test description"}]

    with patch.multiple(
        assistant.git_ops, get_unstaged_changes=lambda: changes, get_current_branch=lambda: "main", stage_files=lambda x: None, commit_changes=lambda x: None
    ):
        with patch.multiple(assistant.ai_analyzer, analyze_changes=lambda x: commit_groups):
            with patch.multiple(assistant.cli, display_commit_groups=lambda x: commit_groups, confirm_push=lambda: False):
                assistant.run()


def test_push_changes_failure(assistant):
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit", "description": "test description"}]

    with patch.multiple(
        assistant.git_ops,
        get_unstaged_changes=lambda: changes,
        get_current_branch=lambda: "main",
        stage_files=lambda x: None,
        commit_changes=lambda x: None,
        push_changes=lambda: exec('raise Exception("Failed to push commits")'),
    ):
        with patch.multiple(assistant.ai_analyzer, analyze_changes=lambda x: commit_groups):
            with patch.multiple(assistant.cli, display_commit_groups=lambda x: commit_groups, confirm_push=lambda: True):
                assistant.run()


def test_push_changes_network_error(assistant):
    """Test push changes fails due to network error"""
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit", "description": "test description"}]

    with patch.multiple(
        assistant.git_ops,
        get_unstaged_changes=lambda: changes,
        get_current_branch=lambda: "main",
        stage_files=lambda x: None,
        commit_changes=lambda x: None,
        push_changes=lambda: exec('raise ConnectionError("Network connection failed")'),
    ):
        with patch.multiple(assistant.ai_analyzer, analyze_changes=lambda x: commit_groups):
            with patch.multiple(assistant.cli, display_commit_groups=lambda x: commit_groups, confirm_push=lambda: True):
                assistant.run()


def test_run_with_staged_changes(assistant, capsys):
    """Test that the correct message is displayed when staged changes are found"""
    staged_changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]

    with patch.multiple(assistant.git_ops, get_staged_changes=lambda: staged_changes, get_current_branch=lambda: "main", stage_files=lambda x: None):
        with patch.object(assistant.ai_analyzer, "analyze_changes", return_value=[]):
            with pytest.raises(SystemExit):
                assistant.run()

    captured = capsys.readouterr()
    assert "Found staged changes, analyzing only those changes." in captured.out
