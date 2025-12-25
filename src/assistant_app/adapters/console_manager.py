from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
import sys

# Central console instance
console = Console()

def print_panel(content: str, title: str = None, style: str = "bold blue"):
    """Prints a styled panel."""
    console.print(Panel(content, title=title, border_style=style))

def print_success(msg: str):
    """Prints a success message."""
    console.print(f"[bold green]✓[/bold green] {msg}")

def print_error(msg: str):
    """Prints an error message."""
    console.print(f"[bold red]✗[/bold red] {msg}")

def print_warning(msg: str):
    """Prints a warning message."""
    console.print(f"[bold yellow]![/bold yellow] {msg}")

def create_table(title: str, columns: list[str]) -> Table:
    """Creates a standardized table."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(col)
    return table

def print_table(table: Table):
    """Prints the table."""
    console.print(table)
