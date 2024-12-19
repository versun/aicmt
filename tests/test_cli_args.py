import pytest
from unittest.mock import patch
from aicmt.cli_args import parse_args


def test_default_args():
    """Test parsing with no arguments."""
    with patch("sys.argv", ["script.py"]):
        args = parse_args()
        assert args.num_commits is None


def test_num_commits():
    """Test parsing number of commits argument."""
    test_num = 5
    with patch("sys.argv", ["script.py", "--num-commits", str(test_num)]):
        args = parse_args()
        assert args.num_commits == test_num


def test_version():
    """Test version argument raises SystemExit."""
    with pytest.raises(SystemExit) as exc_info:
        with patch("sys.argv", ["script.py", "--version"]):
            parse_args()
    assert exc_info.value.code == 0
