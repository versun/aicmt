import argparse
from .__version__ import VERSION


def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments for configuration."""
    parser = argparse.ArgumentParser(
        description="<<< AICMT (AI Commit) - AI-powered Git commit assistant >>>",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-v", "--version", action="version", version=VERSION)
    # Commit Settings
    parser.add_argument("-n", "--num-commits", help="Number of commits to generate (default: AI decides)", type=int, metavar="N")

    # Parse args
    args = parser.parse_args()

    return args
