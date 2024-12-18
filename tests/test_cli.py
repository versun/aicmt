import pytest
from unittest.mock import patch
from aicmt.cli import GitCommitAssistant, cli


@pytest.fixture
def assistant(monkeypatch):
    monkeypatch.setattr("aicmt.config._load_cli_config", lambda: {})
    return GitCommitAssistant()


def test_git_commit_assistant_init(assistant):
    assert hasattr(assistant, 'git_ops')
    assert hasattr(assistant, 'ai_analyzer')
    assert hasattr(assistant, 'cli')


@patch('aicmt.cli.parse_args')
def test_cli_help(mock_parse_args):
    with patch('sys.argv', ['aicmt', '--help']):
        cli()
        mock_parse_args.assert_called_once()


@patch('aicmt.cli.GitCommitAssistant')
@patch('aicmt.cli.parse_args')
def test_cli_value_error(mock_parse_args, mock_assistant, capsys):
    mock_assistant.return_value.run.side_effect = ValueError("Test error")

    with pytest.raises(SystemExit):
        cli()

    captured = capsys.readouterr()
    assert "Configuration Error" in captured.out


@patch('aicmt.cli.GitCommitAssistant')
@patch('aicmt.cli.parse_args')
def test_cli_keyboard_interrupt(mock_parse_args, mock_assistant, capsys):
    mock_parse_args.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit):
        cli()

    captured = capsys.readouterr()
    assert "Program interrupted by user" in captured.out
