#!/usr/bin/env python3
import sys
from typing import List
from .git_operations import GitOperations
from .ai_analyzer import AIAnalyzer
from .cli_interface import CLIInterface
from .cli_args import parse_args
from rich.console import Console

console = Console()


class AiCommit:
    def __init__(self, repo_path: str = "."):
        self.git_ops = GitOperations(repo_path)
        self.ai_analyzer = AIAnalyzer()
        self.cli = CLIInterface()

    def _handle_changes(self) -> List[dict]:
        """Handle and return git changes"""
        staged_changes = self.git_ops.get_staged_changes()
        if staged_changes:
            self.cli.display_info("Found staged changes, analyzing only those changes.")
            return staged_changes
        return self.git_ops.get_unstaged_changes()

    def _create_new_commits(self, approved_groups: List[dict]) -> None:
        """Process approved commit groups"""
        for group in approved_groups:
            try:
                self.git_ops.stage_files(group["files"])
                self.git_ops.commit_changes(f"{group['commit_message']}\n\n{group['description']}")
                self.cli.display_success(f"Created commit: {group['commit_message']}")
            except Exception as e:
                self.cli.display_error(f"Failed to create commit: {str(e)}")

    def _handle_push(self) -> None:
        """Handle pushing changes if confirmed"""
        if self.cli.confirm_push():
            try:
                self.git_ops.push_changes()
                self.cli.display_success("Successfully pushed all commits!")
            except Exception as e:
                self.cli.display_error(f"Failed to push commits: {str(e)}")

    def run(self):
        """Main execution flow"""
        try:
            self.cli.display_welcome()
            self.cli.display_repo_info(self.git_ops.repo.working_dir, self.git_ops.get_current_branch())

            changes = self._handle_changes()

            self.cli.display_changes(changes)
            self.cli.display_ai_analysis_start(self.ai_analyzer.base_url, self.ai_analyzer.model)

            commit_groups = self.ai_analyzer.analyze_changes(changes)
            approved_groups = self.cli.display_commit_groups(commit_groups)

            self.cli.display_groups_approval_status(len(approved_groups), len(commit_groups))

            self._create_new_commits(approved_groups)
            self._handle_push()

        except KeyboardInterrupt:
            self.cli.exit_program("\nOperation cancelled by user.")
        except Exception as e:
            self.cli.display_error(str(e))
            sys.exit(1)


def cli():
    # Create and run assistant
    try:
        parse_args()
        assistant = AiCommit()
        assistant.run()
    except Exception as e:
        # Other runtime errors
        CLIInterface.display_error(str(e))
        sys.exit(1)
