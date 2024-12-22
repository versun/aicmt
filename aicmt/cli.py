#!/usr/bin/env python3
import sys
from .git_operations import GitOperations
from .ai_analyzer import AIAnalyzer
from .cli_interface import CLIInterface
from .cli_args import parse_args
from rich.console import Console

console = Console()


class GitCommitAssistant:
    def __init__(self):
        self.git_ops = GitOperations()
        self.ai_analyzer = AIAnalyzer()
        self.cli = CLIInterface()

    def run(self):
        """Main execution flow"""
        try:
            self.cli.display_welcome()
            # Display repository info
            self.cli.display_repo_info(self.git_ops.repo.working_dir, self.git_ops.get_current_branch())

            # Get changes
            changes = []
            staged_changes = self.git_ops.get_staged_changes()
            if staged_changes:
                changes = staged_changes
                self.cli.display_info("Found staged changes, analyzing only those changes.")
            else:
                changes = self.git_ops.get_unstaged_changes()

            # Display current changes with detailed info
            self.cli.display_changes(changes)

            # Analyze changes with AI
            self.cli.display_ai_analysis_start(self.ai_analyzer.base_url, self.ai_analyzer.model)

            commit_groups = self.ai_analyzer.analyze_changes(changes)
            approved_groups = self.cli.display_commit_groups(commit_groups)
            self.cli.display_groups_approval_status(len(approved_groups), len(commit_groups))

            # Create commits for approved groups
            for group in approved_groups:
                try:
                    # Stage files for this group
                    self.git_ops.stage_files(group["files"])

                    # Create commit
                    self.git_ops.commit_changes(group["commit_message"] + "\n\n" + group["description"])

                    self.cli.display_success(f"Created commit: {group['commit_message']}")
                except Exception as e:
                    self.cli.display_error(f"Failed to create commit: {str(e)}")
                    continue

            # Ask user if they want to push changes
            if self.cli.confirm_push():
                try:
                    self.git_ops.push_changes()
                    self.cli.display_success("Successfully pushed all commits!")
                except Exception as e:
                    self.cli.display_error(f"Failed to push commits: {str(e)}")

        except KeyboardInterrupt:
            self.cli.exit_program("\nOperation cancelled by user.")
        except Exception as e:
            self.cli.display_error(str(e))
            sys.exit(1)


def cli():
    try:
        # First parse command line arguments
        parse_args()

        # Create and run assistant
        try:
            assistant = GitCommitAssistant()
            assistant.run()
        except ValueError as ve:
            # Configuration related errors
            console.print(f"[bold red]Configuration Error:[/bold red] {str(ve)}")
            sys.exit(1)
        except Exception as e:
            # Other runtime errors
            console.print(f"[bold red]Runtime Error:[/bold red] {str(e)}")
            sys.exit(1)
    except KeyboardInterrupt:
        console.print("\nProgram interrupted by user")
        sys.exit(1)
