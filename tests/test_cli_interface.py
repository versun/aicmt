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
    mock_change = Mock(file="test.py", status="modified", insertions=1, deletions=2)
    cli.display_changes([mock_change])
    captured = capsys.readouterr()
    assert "test.py" in captured.out
    assert "Modified" in captured.out
    assert "+1/-2" in captured.out


def test_display_commit_groups(cli, capsys):
    groups = [{"files": ["test.py"], "commit_message": "test: add test", "description": "Add test file"}]

    with patch("rich.prompt.Confirm.ask", return_value=True):
        result = cli.display_commit_groups(groups)
        assert result == groups
        captured = capsys.readouterr()
        assert "Suggested Commits" in captured.out
        assert "test.py" in captured.out


def test_display_changes_status_colors(cli, capsys):
    # Test new file status
    new_file = Mock(file="new.py", status="new file", insertions=3, deletions=0)
    cli.display_changes([new_file])
    captured = capsys.readouterr()
    assert "Added" in captured.out
    assert "+3/-0" in captured.out

    # Test modified file status
    modified_file = Mock(file="mod.py", status="modified", insertions=2, deletions=1)
    cli.display_changes([modified_file])
    captured = capsys.readouterr()
    assert "Modified" in captured.out
    assert "+2/-1" in captured.out

    # Test deleted file status
    deleted_file = Mock(file="del.py", status="deleted", insertions=0, deletions=5)
    cli.display_changes([deleted_file])
    captured = capsys.readouterr()
    assert "Deleted" in captured.out
    assert "+0/-5" in captured.out


def test_display_changes_no_modifications(cli, capsys):
    # Test file with no changes
    no_change = Mock(file="unchanged.py", status="modified", insertions=0, deletions=0)
    cli.display_changes([no_change])
    captured = capsys.readouterr()
    assert "-" in captured.out  # Should show "-" when no changes


def test_display_commit_groups_non_interactive(cli, capsys):
    groups = [{"files": ["test.py"], "commit_message": "test: add test", "description": "Add test file"}]

    with patch("rich.prompt.Confirm.ask", side_effect=EOFError):
        result = cli.display_commit_groups(groups)
        assert result == groups
        captured = capsys.readouterr()
        assert "Non-interactive environment" in captured.out


def test_confirm_push(cli):
    with patch("rich.prompt.Confirm.ask", return_value=True):
        assert cli.confirm_push() is True


def test_confirm_push_non_interactive(cli):
    with patch("rich.prompt.Confirm.ask", side_effect=EOFError):
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
