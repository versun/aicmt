import pytest
from unittest.mock import patch
from aicmt.cli import GitCommitAssistant, cli
from aicmt.git_operations import Change


@pytest.fixture
def assistant(monkeypatch):
    monkeypatch.setattr("aicmt.config._load_cli_config", lambda: {})
    return GitCommitAssistant()


def test_git_commit_assistant_init(assistant):
    assert hasattr(assistant, "git_ops")
    assert hasattr(assistant, "ai_analyzer")
    assert hasattr(assistant, "cli")


@patch("aicmt.cli.parse_args")
def test_cli_help(mock_parse_args):
    with patch("sys.argv", ["aicmt", "--help"]):
        cli()
        mock_parse_args.assert_called_once()


@patch("aicmt.cli.GitCommitAssistant")
@patch("aicmt.cli.parse_args")
def test_cli_value_error(mock_parse_args, mock_assistant, capsys):
    mock_assistant.return_value.run.side_effect = ValueError("Test error")

    with pytest.raises(SystemExit):
        cli()

    captured = capsys.readouterr()
    assert "Configuration Error" in captured.out


@patch("aicmt.cli.GitCommitAssistant")
@patch("aicmt.cli.parse_args")
def test_cli_keyboard_interrupt(mock_parse_args, mock_assistant, capsys):
    mock_parse_args.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit):
        cli()

    captured = capsys.readouterr()
    assert "Program interrupted by user" in captured.out


def test_run_no_changes(assistant):
    with patch("aicmt.git_operations.GitOperations.get_unstaged_changes", return_value=[]):
        with pytest.raises(SystemExit):
            assistant.run()


@patch("rich.prompt.Confirm.ask")
def test_run_successful_flow(mock_confirm, assistant):
    # Mock necessary dependencies
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit"}]

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
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit"}]

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
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit"}]

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


@patch("rich.prompt.Confirm.ask")
def test_run_no_approved_groups(mock_confirm, assistant):
    changes = [Change(file="test.py", status="modified", diff="test diff", insertions=1, deletions=0)]
    commit_groups = [{"files": ["test.py"], "commit_message": "test commit"}]

    # Mock user confirmation
    mock_confirm.return_value = True

    with patch.multiple(assistant.git_ops, get_unstaged_changes=lambda: changes, get_current_branch=lambda: "main"):
        with patch.multiple(assistant.ai_analyzer, analyze_changes=lambda x: commit_groups):
            with patch.multiple(assistant.cli, display_commit_groups=lambda x: []):
                assistant.run()
