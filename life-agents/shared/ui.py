"""Rich-based terminal UI helpers for life-agents."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.live import Live
from rich.text import Text
from rich import box

console = Console()


class UI:
    """Static UI helpers using Rich."""

    @staticmethod
    def header(title: str, subtitle: str = "") -> None:
        content = f"[bold white]{title}[/bold white]"
        if subtitle:
            content += f"\n[dim]{subtitle}[/dim]"
        console.print(Panel(content, style="bold blue", padding=(1, 4)))

    @staticmethod
    def success(msg: str) -> None:
        console.print(f"[bold green]✅ {msg}[/bold green]")

    @staticmethod
    def error(msg: str) -> None:
        console.print(f"[bold red]❌ {msg}[/bold red]")

    @staticmethod
    def info(msg: str) -> None:
        console.print(f"[bold cyan]ℹ️  {msg}[/bold cyan]")

    @staticmethod
    def warning(msg: str) -> None:
        console.print(f"[bold yellow]⚠️  {msg}[/bold yellow]")

    @staticmethod
    def input(prompt: str, default: str = "") -> str:
        return Prompt.ask(f"[bold cyan]{prompt}[/bold cyan]", default=default)

    @staticmethod
    def confirm(prompt: str, default: bool = False) -> bool:
        return Confirm.ask(f"[bold yellow]{prompt}[/bold yellow]", default=default)

    @staticmethod
    def table(title: str, columns: list[str], rows: list[list]) -> None:
        tbl = Table(
            title=f"[bold]{title}[/bold]",
            box=box.ROUNDED,
            header_style="bold magenta",
            show_lines=True,
        )
        for col in columns:
            tbl.add_column(col, overflow="fold")
        for row in rows:
            tbl.add_row(*[str(c) for c in row])
        console.print(tbl)

    @staticmethod
    def rule(title: str = "") -> None:
        if title:
            console.rule(f"[bold dim]{title}[/bold dim]")
        else:
            console.rule()

    @staticmethod
    def stream_print(generator) -> str:
        """Print streaming chunks and return full assembled text."""
        full_text = ""
        console.print()
        for chunk in generator:
            console.print(chunk, end="", markup=False, highlight=False)
            full_text += chunk
        console.print()
        return full_text

    @staticmethod
    def menu(title: str, options: list[str]) -> int:
        """Show numbered menu, return 0-based index of chosen option."""
        UI.rule(title)
        for i, opt in enumerate(options, 1):
            console.print(f"  [bold cyan]{i}.[/bold cyan] {opt}")
        console.print()
        while True:
            choice = Prompt.ask(
                "[bold yellow]בחר אפשרות[/bold yellow]",
                default="1"
            )
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return idx
                UI.error(f"נא לבחור בין 1 ל-{len(options)}")
            except ValueError:
                UI.error("נא להזין מספר")

    @staticmethod
    def countdown(seconds: int, label: str = "") -> None:
        """Display a live countdown timer."""
        import time
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold yellow]{task.fields[remaining]}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                label or "⏱️  זמן נותר",
                total=seconds,
                remaining=f"{seconds//60:02d}:{seconds%60:02d}",
            )
            for elapsed in range(seconds):
                time.sleep(1)
                remaining = seconds - elapsed - 1
                progress.update(
                    task,
                    advance=1,
                    remaining=f"{remaining//60:02d}:{remaining%60:02d}",
                )

    @staticmethod
    def print_api_key_error() -> None:
        console.print(Panel(
            "[bold red]⚠️  ANTHROPIC_API_KEY לא מוגדר![/bold red]\n\n"
            "[white]כדי להשתמש בתכונות AI:[/white]\n"
            "[cyan]1.[/cyan] עבור ל- [link]https://console.anthropic.com[/link]\n"
            "[cyan]2.[/cyan] לחץ על [bold]API Keys[/bold] → [bold]Create Key[/bold]\n"
            "[cyan]3.[/cyan] העתק את הקובץ [bold].env.example[/bold] → [bold].env[/bold]\n"
            "[cyan]4.[/cyan] הוסף: [bold]ANTHROPIC_API_KEY=sk-ant-api03-...[/bold]",
            title="הגדרת API Key",
            border_style="red",
        ))
