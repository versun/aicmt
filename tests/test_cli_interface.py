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
    with patch.object(cli, "exit_program") as mock_exit:
        cli.display_changes([])
        captured = capsys.readouterr()
        assert "No changes found" in captured.out
        mock_exit.assert_called_once()


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
    assert "✓" in captured.out
    assert "Test success" in captured.out


def test_exit_program(cli):
    with pytest.raises(SystemExit) as exc_info:
        cli.exit_program("Test exit")
    assert exc_info.value.code == 0


def test_display_info(cli, capsys):
    """Test display_info method"""
    test_message = "Test information message"
    cli.display_info(test_message)
    captured = capsys.readouterr()
    assert test_message in captured.out


def test_display_changes_with_multiple_files(cli, capsys):
    """Test display_changes with multiple files with different statuses"""
    mock_changes = [
        Mock(file="test1.py", status="modified", insertions=1, deletions=0),
        Mock(file="test2.py", status="new file", insertions=5, deletions=0),
        Mock(file="test3.py", status="deleted", insertions=0, deletions=3),
    ]
    cli.display_changes(mock_changes)
    captured = capsys.readouterr()

    # Check if all files are displayed
    assert "test1.py" in captured.out
    assert "test2.py" in captured.out
    assert "test3.py" in captured.out

    # Check status displays
    assert "Modified" in captured.out
    assert "Added" in captured.out
    assert "Deleted" in captured.out

    # Check changes count
    assert "+1/-0" in captured.out
    assert "+5/-0" in captured.out
    assert "+0/-3" in captured.out


def test_display_changes_with_large_numbers(cli, capsys):
    """Test display_changes with large number of insertions/deletions"""
    mock_change = Mock(file="large_file.py", status="modified", insertions=1000, deletions=500)
    cli.display_changes([mock_change])
    captured = capsys.readouterr()
    assert "large_file.py" in captured.out
    assert "+1000/-500" in captured.out


def test_display_repo_info(cli, capsys):
    """Test display_repo_info method"""
    working_dir = "/path/to/repo"
    branch = "main"
    cli.display_repo_info(working_dir, branch)
    captured = capsys.readouterr()
    assert "Repository: " in captured.out
    assert working_dir in captured.out
    assert "Branch: " in captured.out
    assert branch in captured.out


def test_display_commit_info(cli, capsys):
    """Test display_commit_info method"""
    commit_hash = "1234567890abcdef"
    commit_message = "feat: add new feature"
    cli.display_commit_info(commit_hash, commit_message)
    captured = capsys.readouterr()
    assert commit_hash[:8] in captured.out
    assert commit_message in captured.out


def test_display_ai_analysis_start(cli, capsys):
    """Test display_ai_analysis_start method"""
    base_url = "http://example.com"
    model = "gpt-4"
    cli.display_ai_analysis_start(base_url, model)
    captured = capsys.readouterr()
    assert "AI Analysis Phase" in captured.out
    assert base_url in captured.out
    assert model in captured.out
    assert "Analyzing changes..." in captured.out


def test_display_groups_approval_status(cli, capsys):
    """Test display_groups_approval_status method with different scenarios"""
    # Test with no approved groups
    cli.display_groups_approval_status(0, 5)
    captured = capsys.readouterr()
    assert "No commit groups were approved by user" in captured.out

    # Test with some approved groups
    cli.display_groups_approval_status(3, 5)
    captured = capsys.readouterr()
    assert "3 of 5 groups approved" in captured.out


def test_display_no_changes(cli, capsys):
    """Test display_no_changes method"""
    cli.display_no_changes()
    captured = capsys.readouterr()
    assert "No changes found" in captured.out
