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
            console.print("[cyan]━━━ Starting AICMT execution ━━━[/cyan]")
            self.cli.display_welcome()

            # Get unstaged changes
            console.print("\n[cyan]━━━ Git Repository Analysis ━━━[/cyan]")
            console.print("Repository: ", self.git_ops.repo.working_dir)
            console.print("Branch: ", self.git_ops.get_current_branch())

            changes = self.git_ops.get_unstaged_changes()
            if not changes:
                console.print("❌ No unstaged changes found")
                self.cli.exit_program("No changes to commit.")

            # Display current changes with detailed info
            console.print(f"Found {len(changes)} unstaged changes")
            console.print("\n[cyan]━━━ Changes Details ━━━[/cyan]")

            self.cli.display_changes(changes)

            # Analyze changes with AI
            console.print("\n[cyan]━━━ AI Analysis Phase ━━━[/cyan]")
            console.print("Base url: ", self.ai_analyzer.base_url)
            console.print("Model: ", self.ai_analyzer.model)
            console.print("Analyzing changes...")

            commit_groups = self.ai_analyzer.analyze_changes(changes)
            approved_groups = self.cli.display_commit_groups(commit_groups)

            if not approved_groups:
                console.print("No commit groups were approved by user")
                # self.cli.exit_program("No commit groups were approved.")
            else:
                console.print(f"{len(approved_groups)} of {len(commit_groups)} groups approved")

            # Create commits for approved groups
            for group in approved_groups:
                try:
                    # Stage files for this group
                    self.git_ops.stage_files(group["files"])

                    # Create commit
                    self.git_ops.commit_changes(group["commit_message"])

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

        # If help info requested, parse_args has handled it
        if "--help" in sys.argv or "-h" in sys.argv:
            return

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
