import pytest
from unittest.mock import patch
from aicmt.cli_args import parse_args


def test_default_args():
    """Test parsing with no arguments."""
    with patch("sys.argv", ["script.py"]):
        args = parse_args()
        assert args.api_key is None
        assert args.base_url is None
        assert args.model is None
        assert args.num_commits is None


def test_api_key():
    """Test parsing API key argument."""
    test_key = "test-api-key"
    with patch("sys.argv", ["script.py", "--api-key", test_key]):
        args = parse_args()
        assert args.api_key == test_key


def test_base_url():
    """Test parsing base URL argument."""
    test_url = "https://test-api.com/v1"
    with patch("sys.argv", ["script.py", "--base-url", test_url]):
        args = parse_args()
        assert args.base_url == test_url


def test_model():
    """Test parsing model argument."""
    test_model = "gpt-4"
    with patch("sys.argv", ["script.py", "--model", test_model]):
        args = parse_args()
        assert args.model == test_model


def test_num_commits():
    """Test parsing number of commits argument."""
    test_num = 5
    with patch("sys.argv", ["script.py", "--num-commits", str(test_num)]):
        args = parse_args()
        assert args.num_commits == test_num


def test_multiple_args():
    """Test parsing multiple arguments together."""
    test_args = ["script.py", "--api-key", "test-key", "--model", "gpt-4", "--num-commits", "3"]
    with patch("sys.argv", test_args):
        args = parse_args()
        assert args.api_key == "test-key"
        assert args.model == "gpt-4"
        assert args.num_commits == 3


def test_version():
    """Test version argument raises SystemExit."""
    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["script.py", "--version"]):
            parse_args()
    assert exc_info.value.code == 0
