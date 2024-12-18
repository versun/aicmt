import pytest
from unittest.mock import Mock, patch
from aicmt.cli_interface import CLIInterface


@pytest.fixture
def cli():
    return CLIInterface()


def test_display_welcome(cli, capsys):
    cli.display_welcome()
    captured = capsys.readouterr()
    assert "AICMT (AI Commit)" in captured.out
    assert "Analyze and organize your changes" in captured.out


def test_display_changes_empty(cli, capsys):
    cli.display_changes([])
    captured = capsys.readouterr()
    assert "No unstaged changes found" in captured.out


def test_display_changes(cli, capsys):
    mock_change = Mock(file="test.py",
                       status="modified",
                       insertions=1,
                       deletions=2)
    cli.display_changes([mock_change])
    captured = capsys.readouterr()
    assert "test.py" in captured.out
    assert "Modified" in captured.out
    assert "+1/-2" in captured.out


def test_display_commit_groups(cli, capsys):
    groups = [{
        "files": ["test.py"],
        "commit_message": "test: add test",
        "description": "Add test file"
    }]

    with patch('rich.prompt.Confirm.ask', return_value=True):
        result = cli.display_commit_groups(groups)
        assert result == groups
        captured = capsys.readouterr()
        assert "Suggested Commits" in captured.out
        assert "test.py" in captured.out


def test_display_commit_groups_non_interactive(cli, capsys):
    groups = [{
        "files": ["test.py"],
        "commit_message": "test: add test",
        "description": "Add test file"
    }]

    with patch('rich.prompt.Confirm.ask', side_effect=EOFError):
        result = cli.display_commit_groups(groups)
        assert result == groups
        captured = capsys.readouterr()
        assert "Non-interactive environment" in captured.out


def test_confirm_push(cli):
    with patch('rich.prompt.Confirm.ask', return_value=True):
        assert cli.confirm_push() is True


def test_confirm_push_non_interactive(cli):
    with patch('rich.prompt.Confirm.ask', side_effect=EOFError):
        assert cli.confirm_push() is False


def test_display_error(cli, capsys):
    cli.display_error("Test error")
    captured = capsys.readouterr()
    assert "Error:" in captured.out
    assert "Test error" in captured.out


def test_display_success(cli, capsys):
    cli.display_success("Test success")
    captured = capsys.readouterr()
    assert "Success:" in captured.out
    assert "Test success" in captured.out


def test_exit_program(cli):
    with pytest.raises(SystemExit) as exc_info:
        cli.exit_program("Test exit")
    assert exc_info.value.code == 0
