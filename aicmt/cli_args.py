import argparse
from .__version__ import VERSION


def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments for configuration."""
    parser = argparse.ArgumentParser(
        description="<<< AICMT (AI Commit) - AI-powered Git commit assistant >>>",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-v", "--version", action="version", version=VERSION)

    # OpenAI API Configuration
    # api_group = parser.add_argument_group("OpenAI API Settings")
    parser.add_argument("--api-key", help="OpenAI API key for authentication", metavar="KEY")
    parser.add_argument(
        "--base-url",
        help="Custom API base URL (default: https://api.openai.com/v1)",
        metavar="URL",
    )
    parser.add_argument("--model", help="AI model to use (default: gpt-4o-mini)", metavar="MODEL")
    # Commit Settings
    # commit_group = parser.add_argument_group("Commit Settings")
    parser.add_argument("-n", "--num-commits", help="Number of commits to generate (default: AI decides)", type=int, metavar="N")

    # Parse args
    args = parser.parse_args()

    return args
