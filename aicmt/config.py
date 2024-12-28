import os
import configparser
from pathlib import Path
from typing import Dict, Any, Optional
from .cli_args import parse_args
from .cli_interface import CLIInterface

# Default configuration settings for OpenAI API integration and prompt templates
_DEFAULT_CONFIG = {
    "base_url": "https://api.openai.com/v1",
    "api_key": "api_key",
    "model": "gpt-4o-mini",
    "analysis_prompt": """
You are a Git commit expert who must analyze code changes and provide commit suggestions.
Requirements:
1. Group related changes together logically
2. Use conventional commits format for messages (e.g., feat:, fix:, docs:)
3. Keep commits reasonably sized
4. Provide clear descriptions of why changes are grouped together

Respond strictly in this JSON format:
{
  "commit_groups": [
    {
      "files": ["file1", "file2"],
      "commit_message": "feat: add feature",
      "description": "These changes implement certain functionality"
    }
  ]
}
""",
}


def _get_xdg_config_home() -> Path:
    """
    Get XDG_CONFIG_HOME directory path.
    Returns ~/.config if XDG_CONFIG_HOME is not set.
    """
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home)
    return Path.home() / ".config"


def _get_config_paths() -> Optional[str]:
    """
    Get configuration file paths in priority order:
    1. Local configuration (./.aicmtrc)
    2. XDG configuration ($XDG_CONFIG_HOME/aicmt/.aicmtrc or ~/.config/aicmt/.aicmtrc)
    """

    config_path = [
        Path.cwd() / ".aicmtrc",  # Local config
        _get_xdg_config_home() / "aicmt" / ".aicmtrc",  # XDG config
        Path.home() / ".aicmtrc",  # Legacy global config
    ]

    for path in config_path:
        if path.is_file():
            return path

    return None


def _merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries while preserving existing values in the base dictionary.

    Args:
        base (Dict[str, Any]): The base configuration dictionary.
        override (Dict[str, Any]): The configuration dictionary to merge.
    """
    result = base.copy()

    for key, value in override.items():
        if value is not None:
            result[key] = value

    return result


def _parse_config_file(config_path: Path) -> Dict[str, Any]:
    """Parse a single configuration file and return the configuration dictionary."""

    result = {}

    try:
        # Create ConfigParser with multiline value support
        config = configparser.ConfigParser(
            interpolation=None,  # Disable interpolation to preserve prompt templates
            inline_comment_prefixes=("#", ";"),
            comment_prefixes=("#", ";"),
            delimiters=("=",),  # Only use = as delimiter for clarity
        )

        # Read the configuration file with UTF-8 encoding
        with open(config_path, "r", encoding="utf-8") as f:
            config.read_file(f)

        # Read OpenAI section
        if config.has_section("openai"):
            for key in ["api_key", "base_url", "model"]:
                if config.has_option("openai", key):
                    value = config.get("openai", key)
                    if value and not value.startswith(("#", ";")):
                        result[key] = value.strip()

        # Process prompts section with improved multiline handling
        if config.has_section("prompts"):
            for key in ["analysis_prompt"]:
                if config.has_option("prompts", key):
                    value = config.get("prompts", key, raw=True)
                    if not value.lstrip().startswith(("#", ";")):
                        # Preserve indentation while removing common leading spaces
                        lines = value.splitlines()
                        # Find minimum indentation (excluding empty lines)
                        min_indent = float("inf")
                        for line in lines:
                            if line.strip():
                                indent = len(line) - len(line.lstrip())
                                min_indent = min(min_indent, indent)
                        min_indent = 0 if min_indent == float("inf") else min_indent

                        # Process lines preserving formatting
                        processed_lines = []
                        for line in lines:
                            if not line.lstrip().startswith(("#", ";")):
                                # Remove common indentation while preserving relative indentation
                                processed_lines.append(line[min_indent:])

                        if processed_lines:
                            result[key] = "\n".join(processed_lines)

    except configparser.Error as e:
        CLIInterface.display_warning(
            f"Warning: Failed to parse config file {config_path}\n"
            f"[blue]Error message: {str(e)}[/blue]\n"
            "[yellow]Please check the following:[/yellow]\n"
            "1. Ensure the config file format is correct\n"
            "2. Check if all configuration items have correct section tags (e.g., [openai], [prompts])\n"
            "3. Ensure the file is saved with UTF-8 encoding"
        )
    except Exception as e:
        CLIInterface.display_warning(
            f"Warning: Unexpected error occurred while reading config file {config_path}\n"
            f"[blue]Error message: {str(e)}[/blue]\n"
            "[yellow]Suggested actions:[/yellow]\n"
            "1. Check file permissions\n"
            "2. Ensure the file is not locked by other programs\n"
            "3. If the problem persists, try recreating the config file from template"
        )

    return result


def _load_config_file() -> Dict[str, Any]:
    """Load configuration from .aicmtrc files following priority order:
    1. Local configuration (./.aicmtrc)
    2. Global configuration ($XDG_CONFIG_HOME/aicmt/.aicmtrc or ~/.config/aicmt/.aicmtrc)

    Returns:
        Dict[str, Any]: Configuration dictionary. Empty dict if no valid config found.
    """

    # Define configuration paths with priority
    # global_config_path = Path.home() / ".aicmtrc"
    # local_config_path = Path.cwd() / ".aicmtrc"

    config_path = _get_config_paths()
    if config_path:
        return _parse_config_file(config_path)
    else:
        # Create default configuration file in xdg config directory if it doesn't exist.
        xdg_config_path = _get_xdg_config_home() / "aicmt" / ".aicmtrc"
        if not xdg_config_path.exists():
            xdg_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(xdg_config_path, "w", encoding="utf-8") as f:
                f.write(
                    "## Configuration Example ##\n"
                    "## More info: https://github.com/versun/aicmt ##\n"
                    "[openai]\n"
                    "api_key = your-api-key-here\n"
                    "model = gpt-4o-mini\n"
                    "base_url = https://api.openai.com/v1\n"
                )

        CLIInterface.display_warning(f"Auto created configuration file in {xdg_config_path}\n" "Please check and update your configuration file.")
        return _parse_config_file(xdg_config_path)

    # if not global_config_path.exists() and not local_config_path.exists() and not xdg_config_path.exists():
    #     CLIInterface.display_error(
    #         "No configuration file found.\n"
    #         "Please create .aicmtrc file in the home directory with the following format:\n\n"
    #         "## Configuration Example ##\n"
    #         "\[openai]\n"
    #         "api_key = your-api-key-here\n"
    #         "model = gpt-4\n"
    #         "base_url = https://api.openai.com/v1\n"
    #         "## More info: https://github.com/versun/aicmt ##\n"
    #     )
    #     sys.exit(1)

    # # First try local configuration (higher priority)
    # if local_config_path.exists() and local_config_path.is_file():
    #     return _parse_config_file(local_config_path)

    # # Then try global configuration (lower priority)
    # if global_config_path.exists() and global_config_path.is_file():
    #     return _parse_config_file(global_config_path)

    # return {}


def _load_cli_config() -> Dict[str, Any]:
    """Load configuration from command line arguments."""
    args = parse_args()

    cli_config = {}

    if args.num_commits is not None:
        cli_config["num_commits"] = args.num_commits
    return cli_config


def load_config() -> Dict[str, Any]:
    """
    Load configuration with strict priority order:
    1. Command line arguments (highest priority)
    2. Local configuration (./.aicmtrc)
    3. Global configuration ($XDG_CONFIG_HOME/aicmt/.aicmtrc or ~/.config/aicmt/.aicmtrc)
    4. Default configuration (lowest priority)
    """
    config = dict(_DEFAULT_CONFIG)

    file_config = _load_config_file()
    if file_config:
        config = _merge_configs(config, file_config)

    cli_config = _load_cli_config()
    if cli_config:
        config = _merge_configs(config, cli_config)

    try:
        validate_config(config)
    except ValueError as e:
        CLIInterface.display_error(f"Configuration Error: {str(e)}")
        raise

    return config


def validate_config(config: Dict[str, Any]):
    """
    Validate OpenAI configuration settings with proper source tag handling and helpful error messages.
    """

    # Check for openai section
    required_fields = ["base_url", "model", "api_key", "analysis_prompt"]
    missing_fields = [field for field in required_fields if field not in config]

    # API key validation
    if "api_key" in missing_fields:
        raise ValueError(
            "OpenAI API key not configured. To fix this:\n" "add below configuration to .aicmtrc file:\n" "   [openai]\n" "   api_key = your-api-key-here"
        )

    if "model" in missing_fields:
        raise ValueError("No model specified. To fix this:\n" "add below configuration to .aicmtrc file:\n" "   [openai]\n" "   model = gpt-4o-mini")

    if "base_url" in missing_fields:
        raise ValueError(
            "No base URL specified. To fix this:\n" "add below configuration to .aicmtrc file:\n" "   [openai]\n" "   base_url = https://your-base-url.com"
        )

    if "analysis_prompt" in missing_fields:
        raise ValueError(
            "No analysis prompt specified. To fix this:\n"
            "add below configuration to .aicmtrc file:\n"
            "   [prompts]\n"
            "   analysis_prompt = Your analysis prompt here"
        )

    # Base URL validation
    base_url = config.get("base_url")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError(
            f"Invalid API URL format: {base_url}\n"
            "The base_url must:\n"
            "1. Start with http:// or https://\n"
            "2. Be a valid URL\n"
            "Example: https://api.openai.com/v1\n"
            "Current source tags will be preserved after validation"
        )

    # Prompt validation with enhanced feedback
    prompt = config.get("analysis_prompt")
    if prompt:
        if len(prompt.strip()) < 10:
            CLIInterface.display_warning(f"Warning: analysis prompt is too short " f"({len(prompt.strip())} characters), " "this may affect analysis quality")
