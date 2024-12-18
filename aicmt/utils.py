import os
from typing import List
from rich.console import Console
from rich.prompt import Confirm

console = Console()


def chunk_files(files: List[str], max_size: int = 1000) -> List[List[str]]:
    """Split files into chunks to avoid token limits"""
    chunks = []
    current_chunk = []
    current_size = 0

    for file in files:
        file_size = os.path.getsize(file)
        if current_size + file_size > max_size:
            chunks.append(current_chunk)
            current_chunk = [file]
            current_size = file_size
        else:
            current_chunk.append(file)
            current_size += file_size

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def format_diff(diff_text: str) -> str:
    """Format diff text for enhanced readability with rich color coding"""
    lines = diff_text.split("\n")
    formatted = []
    in_header = True
    chunk_count = 0

    for line in lines:
        # Format diff header lines
        if line.startswith("diff --git"):
            if chunk_count > 0:
                formatted.append("└" + "─" * 50)  # End previous diff block
            formatted.append(f"[bold blue]┌{'─' * 50}[/bold blue]")
            formatted.append(f"[bold blue]│[/bold blue] {line}")
            chunk_count += 1
            continue
        elif line.startswith("index"):
            formatted.append(f"[dim blue]│[/dim blue] {line}")
            continue
        elif line.startswith("+++"):
            formatted.append(f"[bold green]│[/bold green] {line}")
            continue
        elif line.startswith("---"):
            formatted.append(f"[bold red]│[/bold red] {line}")
            continue
        elif any(line.startswith(prefix) for prefix in ["new file", "deleted"]):
            formatted.append(f"[bold yellow]│[/bold yellow] {line}")
            continue
        elif line.startswith("@@"):
            formatted.append(f"[magenta]├{'─' * 10}[/magenta] {line}")
            in_header = False
            continue

        # Format actual changes
        if not in_header:
            if line.startswith("+"):
                # Highlight syntax for added lines
                line_content = line[1:]  # Remove the leading +
                if any(keyword in line_content for keyword in ["def ", "class ", "import ", "from "]):
                    formatted.append(f"[bright_green]│ + {line_content}[/bright_green]")
                else:
                    formatted.append(f"[green]│ + {line_content}[/green]")
            elif line.startswith("-"):
                # Highlight syntax for removed lines
                line_content = line[1:]  # Remove the leading -
                if any(keyword in line_content for keyword in ["def ", "class ", "import ", "from "]):
                    formatted.append(f"[bright_red]│ - {line_content}[/bright_red]")
                else:
                    formatted.append(f"[red]│ - {line_content}[/red]")
            else:
                # Context lines
                if line.strip():
                    formatted.append(f"[dim]│   {line}[/dim]")
                else:
                    formatted.append("│")

    if chunk_count > 0:
        formatted.append("└" + "─" * 50)  # End last diff block

    return "\n".join(formatted)


def confirm_action(message: str) -> bool:
    """Ask for user confirmation"""
    return Confirm.ask(message)
