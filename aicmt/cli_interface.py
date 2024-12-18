from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.panel import Panel
from typing import List, Dict
import sys

console = Console()


class CLIInterface:
    def __init__(self):
        self.console = Console()

    def display_welcome(self):
        """Display welcome message"""
        console.print(
            Panel.fit(
                "[bold blue]AICMT (AI Commit)[/bold blue]\n" "Analyze and organize your changes into meaningful commits",
                border_style="blue",
            )
        )

    def display_changes(self, changes: list):
        """Display current unstaged changes"""
        if not changes:
            console.print("[yellow]No unstaged changes found.[/yellow]")
            return

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

    def display_error(self, message: str):
        """Display error message"""
        console.print(f"[bold red]Error:[/bold red] {message}")

    def display_success(self, message: str):
        """Display success message"""
        console.print(f"[bold green]Success:[/bold green] {message}")

    def exit_program(self, message: str = ""):
        """Exit the program with an optional message"""
        if message:
            console.print(message)
        sys.exit(0)
