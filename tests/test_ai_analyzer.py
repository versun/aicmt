import json

import pytest
from unittest.mock import Mock, patch
from aicmt.ai_analyzer import AIAnalyzer


@pytest.fixture
def analyzer(monkeypatch):
    monkeypatch.setattr("aicmt.config._load_cli_config", lambda: {})
    return AIAnalyzer()


def test_init(analyzer):
    assert analyzer.client is None
    assert analyzer.model == analyzer.CONFIG.get("model", "gpt-4o-mini")
    assert analyzer.base_url == analyzer.CONFIG.get("base_url", "https://api.openai.com/v1")


def test_client_no_api_key(analyzer):
    # monkeypatch.setattr("aicmt.config._load_cli_config", lambda: {})
    # analyzer = AIAnalyzer()
    with patch.dict(analyzer.CONFIG, {"api_key": None}):
        with pytest.raises(ValueError, match="OpenAI API key not set"):
            analyzer._client()


def test_client_no_model(analyzer):
    with patch.dict(analyzer.CONFIG, {"model": None}):
        with pytest.raises(ValueError, match="Error: No model specified"):
            analyzer._client()


def test_client_no_base_url(analyzer):
    with patch.dict(analyzer.CONFIG, {"base_url": None}):
        with pytest.raises(ValueError, match="Error: No base URL specified"):
            analyzer._client()


def test_analyze_changes_empty_list(analyzer):
    result = analyzer.analyze_changes([])
    assert result == []


@pytest.mark.parametrize(
    "mock_response,expected",
    [
        (
            {"commit_groups": [{"files": ["test.py"], "commit_message": "test: add test", "description": "Add test file"}]},
            [{"files": ["test.py"], "commit_message": "test: add test", "description": "Add test file"}],
        )
    ],
)
def test_analyze_changes_success(analyzer, mock_response, expected):
    with patch.dict(analyzer.CONFIG, {"api_key": "test_key", "model": "test-model"}):
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content=json.dumps(mock_response)))]
        mock_client.chat.completions.create.return_value = mock_completion
        analyzer.client = mock_client

        changes = [Mock(file="test.py", status="modified", diff="test diff")]
        result = analyzer.analyze_changes(changes)
        assert result == expected


def test_generate_system_prompt(analyzer):
    with patch.dict(analyzer.CONFIG, {"analysis_prompt": "Test prompt", "num_commits": 3}):
        prompt = analyzer._generate_system_prompt()
        assert "Test prompt" in prompt
        assert "3 commits" in prompt


def test_generate_user_prompt(analyzer):
    changes = [Mock(file="test.py", status="modified", diff="test diff")]
    prompt = analyzer._generate_user_prompt(changes)
    assert "File: test.py" in prompt
    assert "Status: modified" in prompt
    assert "test diff" in prompt
