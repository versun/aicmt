import argparse
from .__version__ import VERSION
from .cli_interface import WELCOME_MESSAGE


def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments for configuration."""
    parser = argparse.ArgumentParser(
        description="=" * 58 + "\n" + WELCOME_MESSAGE + "\n" + "=" * 58,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-v", "--version", action="version", version=VERSION)
    # Commit Settings
    parser.add_argument("-n", "--num-commits", help="Number of commits to generate (default: AI decides)", type=int, metavar="N")

    # Parse args
    args = parser.parse_args()

    return args
