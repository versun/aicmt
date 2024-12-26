from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.panel import Panel
from typing import List, Dict
from .__version__ import VERSION
import sys

console = Console()

# Constants
WELCOME_MESSAGE = f"AICMT (AI Commit) v{VERSION}\nAnalyze and organize your changes into meaningful commits"


class CLIInterface:
    def __init__(self):
        pass
        # self.console = Console()

    def display_welcome(self):
        """Display welcome message"""
        console.print(
            Panel.fit(
                "[bold blue]" + WELCOME_MESSAGE + "[/bold blue]",
                border_style="blue",
            )
        )

    @classmethod
    def display_info(cls, message: str):
        """Display information message"""
        console.print(f"[bold blue]{message}[/bold blue]")

    @classmethod
    def display_error(cls, message: str):
        """Display error message"""
        console.print(f"[bold red]Error:[/bold red] {message}")

    @classmethod
    def display_success(cls, message: str):
        """Display success message"""
        console.print(f"[bold green]✓[/bold green] {message}")

    @classmethod
    def display_warning(cls, message: str):
        """Display warning message"""
        console.print(f"[bold yellow]⚠️[/bold yellow] {message}")

    def display_changes(self, changes: list):
        """Display current unstaged changes"""
        if not changes:
            self.display_no_changes()
            self.exit_program()

        console.print("\n[cyan]━━━ Changes Details ━━━[/cyan]")
        # Create a simple table without title
        table = Table(
            show_header=True,
            header_style="bold magenta",
            padding=(0, 1),
            expand=False,
            show_lines=True,
        )

        # Add columns
        table.add_column("File", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("±", justify="right")

        # Add rows
        for change in changes:
            # Determine status color
            if change.status == "new file":
                status = "[green]Added[/green]"
            elif change.status == "modified":
                status = "[yellow]Modified[/yellow]"
            else:
                status = "[red]Deleted[/red]"

            # Format changes count
            changes_str = f"+{change.insertions}/-{change.deletions}" if change.insertions + change.deletions > 0 else "-"

            table.add_row(change.file, status, changes_str)

        # Print with minimal spacing
        console.print(table)

    def display_commit_groups(self, groups: List[Dict]) -> List[Dict]:
        """Display suggested commit groups and let user review them"""
        console.print("\n[bold]Suggested Commits:[/bold]")
        console.print(f"[blue]All {len(groups)} suggested commits[/blue]")

        approved_groups = []
        for i, group in enumerate(groups, 1):
            console.print(f"\n[bold]Commit {i}:[/bold]")
            table = Table(show_header=True, header_style="bold green")
            table.add_column("Files")
            table.add_column("Commit Message")
            table.add_column("Description")

            table.add_row("\n".join(group["files"]), group["commit_message"], group["description"])

            console.print(table)

            try:
                if Confirm.ask("Accept this commit?"):
                    approved_groups.append(group)
            except EOFError:
                # In non-interactive environment, accept all groups by default
                console.print("[yellow]Non-interactive environment, accepting this commit by default[/yellow]")
                approved_groups.append(group)

        return approved_groups

    def confirm_push(self) -> bool:
        """Ask user to confirm push operation"""
        try:
            return Confirm.ask("\nDo you want to push the commits?")
        except EOFError:
            return False

    def display_repo_info(self, working_dir: str, branch: str):
        """Display repository information"""
        console.print("\n[cyan]━━━ Git Repository Info ━━━[/cyan]")
        console.print("Repository: ", working_dir)
        console.print("Branch: ", branch)

    def display_commit_info(self, commit_hash: str, commit_message: str):
        """Display commit information"""
        console.print(f"Analyzed commit: {commit_hash[:8]} - {commit_message}")

    def display_no_changes(self):
        """Display no changes message"""
        console.print("❌ No changes found")

    def display_ai_analysis_start(self, base_url: str, model: str):
        """Display AI analysis phase information"""
        console.print("\n[cyan]━━━ AI Analysis Phase ━━━[/cyan]")
        console.print("Base url: ", base_url)
        console.print("Model: ", model)
        console.print("Analyzing changes...")

    def display_groups_approval_status(self, approved_count: int, total_count: int):
        """Display groups approval status"""
        if approved_count == 0:
            console.print("No commit groups were approved by user")
        else:
            console.print(f"{approved_count} of {total_count} groups approved")

    def exit_program(self, message: str = ""):
        """Exit the program with an optional message"""
        if message:
            console.print(message)
        sys.exit(0)
