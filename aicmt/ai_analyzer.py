from typing import List, Dict
import json
from openai import OpenAI, OpenAIError
from .config import load_config
from rich.console import Console

console = Console()


class AIAnalyzer:

    def __init__(self):
        self.client = None
        self.CONFIG = load_config()
        self.model = self.CONFIG.get("model", "gpt-4o-mini")
        self.base_url = self.CONFIG.get("base_url",
                                        "https://api.openai.com/v1")

    def _client(self):
        """Ensure OpenAI client is initialized"""
        if self.client is None:
            api_key = self.CONFIG.get("api_key")
            base_url = self.CONFIG.get("base_url")
            model = self.CONFIG.get("model")

            if not api_key:
                console.print(
                    "[red]Error: OpenAI API key not set. Please set it using one of the following methods:[/red]"
                )
                console.print("1. Use --api-key command line argument")
                console.print(
                    "2. Set api_key in the .aicmtrc configuration file")
                raise ValueError("OpenAI API key not set")

            if not model:
                raise ValueError("[red]Error: No model specified[/red]")
                # model = "gpt-4o-mini"

            if not base_url:
                raise ValueError("[red]Error: No base URL specified[/red]")

            # Initialize client
            self.client = OpenAI(api_key=api_key, base_url=base_url)

    def analyze_changes(self, changes: list) -> List[Dict]:
        """Analyze changes and suggest commit groupings"""
        if not changes:
            console.print("No changes to analyze, returning empty list")
            return []

        try:
            self._client()
            if not self.client:
                console.print(
                    "[red]Error: Failed to initialize the OpenAI client[/red]")
                return []

            system_prompt = self._generate_system_prompt()
            user_prompt = self._generate_user_prompt(changes)
            # Get model configuration
            model = self.CONFIG.get("model")

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    },
                ],
                temperature=0.5,
                response_format={"type": "json_object"},
            )

            if not response or not hasattr(response,
                                           "choices") or not response.choices:
                raise ValueError("API returned an empty response: ", response)

            content = response.choices[0].message.content
            if not content or not isinstance(content, str):
                raise ValueError("API returned invalid response content")

            try:
                result = json.loads(content)
            except json.JSONDecodeError as je:
                raise ValueError(
                    f"Format failed: API returned invalid JSON format: {str(je)}"
                )
            except Exception as e:
                raise ValueError(f"An error occurred during retry: {str(e)}")

            # Validate response format
            if not isinstance(result, dict):
                raise ValueError(
                    "API response format error: The returned content is not a JSON object"
                )

            if "commit_groups" not in result:
                raise ValueError(
                    "API response format error: missing required commit_groups field"
                )

            if not isinstance(result["commit_groups"], list):
                raise ValueError(
                    "API response format error: commit_groups must be an array"
                )

            # Validate the format and content of each commit group
            for i, group in enumerate(result["commit_groups"]):
                if not isinstance(group, dict):
                    continue

                required_fields = ["files", "commit_message", "description"]
                missing_fields = [
                    field for field in required_fields if field not in group
                ]

                if missing_fields:
                    # Attempt to fill in missing fields
                    for field in missing_fields:
                        if field == "files":
                            group["files"] = []
                        elif field == "commit_message":
                            group["commit_message"] = "chore: update files"
                        elif field == "description":
                            group["description"] = "Update files"

                if not isinstance(group["files"], list):
                    if isinstance(group["files"], str):
                        group["files"] = [group["files"]]
                    else:
                        group["files"] = []

            return result["commit_groups"]

        except OpenAIError as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg:
                raise ValueError(
                    "Invalid OpenAI API key. Please set the API key using the --api-key command line argument\n"
                    "Or add it to the .aicmtrc configuration file")
            elif "rate_limit" in error_msg:
                raise ValueError(
                    "OpenAI API rate limit exceeded. Suggestions:\n"
                    "1. Wait a moment and try again\n"
                    "2. Check if your API key quota is sufficient\n"
                    "3. If you frequently encounter this problem, consider reducing the request frequency"
                )
            elif "connection" in error_msg.lower():
                raise ValueError(
                    "Failed to connect to the OpenAI API. Please check:\n"
                    "1. Your network connection\n"
                    "2. If using a custom base URL, ensure it is accessible\n"
                    "3. Check if you need to configure a proxy")
            elif "model_not_found" in error_msg:
                raise ValueError(
                    "The model does not exist or you do not have access to it\n"
                )
            else:
                raise ValueError(
                    f"OpenAI API call failed: {error_msg}\n"
                    "If the problem persists, please check the API status or contact support."
                )
        except Exception as e:
            raise ValueError(
                f"{str(e)}\n\n"
                "If this is an unexpected error, please try running the program again."
                "If the problem persists, please report this issue.")

    def _generate_system_prompt(self) -> str:
        """Create a system prompt for the AI"""

        # Get analysis prompt from config
        prompt = self.CONFIG.get("analysis_prompt", "")
        if not prompt:
            console.print(
                "[yellow]Warning: Analysis prompt not found, using default value[/yellow]"
            )

        # Add commit number to prompt
        if self.CONFIG.get("num_commits"):
            console.print(
                f"[yellow] Set commit num: {self.CONFIG['num_commits']} [/yellow]"
            )
            prompt += f"\nImportant: You must group the changes into exactly {self.CONFIG['num_commits']} commits."

        # Validate prompt format
        if not isinstance(prompt, str):
            console.print("Invalid prompt type: %s", type(prompt))
            raise ValueError("Prompt must be a string type")

        if len(prompt.strip()) < 10:
            console.print(
                "[yellow]Warning: Prompt is too short, may affect analysis quality[/yellow]"
            )

        return prompt

    def _generate_user_prompt(self, changes: list) -> str:
        """Create a user prompt for the AI"""
        # Add the changes to the prompt
        changes_text = []
        for change in changes:
            changes_text.append(
                f"File: {change.file}\nStatus: {change.status}\nChanges:\n{change.diff}"
            )

        # Format the final prompt
        user_prompt = "Changes to analyze:\n\n" + "\n\n".join(changes_text)

        return user_prompt