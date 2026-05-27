"""🚀 Life Agents — תפריט ראשי לכל 30 ה-Agents."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt

console = Console()

BASE = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

AGENTS = {
    "work": [
        ("📋 Task Manager",           "cli/task_manager.py",         "cli"),
        ("📧 Email Composer",          "cli/email_composer.py",        "cli"),
        ("🔍 Research Agent",          "cli/research_agent.py",        "cli"),
        ("📅 Daily Planner",           "cli/daily_planner.py",         "cli"),
        ("🍅 Focus Timer",             "scripts/focus_timer.py",       "script"),
        ("🗂️  Project Tracker",        "dashboards/project_tracker.py","dashboard"),
        ("📊 Meeting Notes",           "subagents/meeting_notes.md",   "subagent"),
        ("📄 Doc Analyzer",            "subagents/doc_analyzer.md",    "subagent"),
        ("💻 Code Reviewer",           "subagents/code_reviewer.md",   "subagent"),
    ],
    "home": [
        ("🍳 Recipe Finder",           "cli/recipe_finder.py",         "cli"),
        ("🗓️  Meal Planner",            "cli/meal_planner.py",          "cli"),
        ("🛒 Shopping Smart",          "scripts/shopping_smart.py",    "script"),
        ("🏠 Home Maintenance",        "dashboards/home_maintenance.py","dashboard"),
        ("🧊 Fridge Tracker",          "scripts/fridge_tracker.py",    "script"),
        ("🥗 Calorie Counter",         "scripts/calorie_counter.py",   "script"),
        ("💰 Grocery Budget",          "scripts/grocery_budget.py",    "script"),
    ],
    "finance": [
        ("💸 Budget Tracker",          "cli/budget_tracker.py",        "cli"),
        ("🔔 Bill Reminder",           "scripts/bill_reminder.py",     "script"),
        ("📈 Investment Monitor",      "dashboards/investment_monitor.py","dashboard"),
        ("🏦 Financial Advisor",       "cli/financial_advisor.py",     "cli"),
        ("🎯 Savings Goals",           "dashboards/savings_goals.py",  "dashboard"),
        ("🧾 Expense Analyzer",        "subagents/expense_analyzer.md","subagent"),
        ("📋 Tax Helper",              "subagents/tax_helper.md",      "subagent"),
    ],
    "health": [
        ("🏋️  Workout Planner",         "cli/workout_planner.py",       "cli"),
        ("🥦 Nutrition Tracker",       "dashboards/nutrition_tracker.py","dashboard"),
        ("😴 Sleep Coach",             "cli/sleep_coach.py",           "cli"),
        ("🧠 Mental Health",           "cli/mental_health.py",         "cli"),
        ("🏥 Medical Tracker",         "scripts/medical_tracker.py",   "script"),
        ("💧 Water Reminder",          "scripts/water_reminder.py",    "script"),
        ("☀️  Morning Briefing",         "cli/morning_briefing.py",      "cli"),
    ],
}

CATEGORIES = {
    "work":    "💼 עבודה ופרודוקטיביות",
    "home":    "🏠 בית ואוכל",
    "finance": "💰 כספים ותקציב",
    "health":  "❤️  בריאות וכושר",
}

TYPE_BADGE = {
    "cli":       "[bold cyan]  CLI  [/bold cyan]",
    "script":    "[bold yellow]SCRIPT[/bold yellow]",
    "dashboard": "[bold green]  WEB  [/bold green]",
    "subagent":  "[bold magenta] AGENT[/bold magenta]",
}


def print_header():
    console.print(Panel(
        "[bold yellow]  ██╗     ██╗███████╗███████╗\n"
        "  ██║     ██║██╔════╝██╔════╝\n"
        "  ██║     ██║█████╗  █████╗  \n"
        "  ██║     ██║██╔══╝  ██╔══╝  \n"
        "  ███████╗██║██║     ███████╗\n"
        "  ╚══════╝╚═╝╚═╝     ╚══════╝\n"
        "  [bold white]    AGENTS  [/bold white][dim]30 AI Agents for Life[/dim][/bold yellow]",
        border_style="bold blue",
        padding=(0, 2),
    ))


def print_menu():
    all_agents = []
    n = 1

    for cat_key, cat_name in CATEGORIES.items():
        table = Table(
            title=f"\n  {cat_name}",
            box=box.SIMPLE,
            show_header=False,
            padding=(0, 1),
            title_style="bold white",
        )
        table.add_column("num", style="bold cyan", width=4)
        table.add_column("badge", width=8)
        table.add_column("name")

        for name, path, agent_type in AGENTS[cat_key]:
            table.add_row(f"{n}.", TYPE_BADGE[agent_type], name)
            all_agents.append((name, path, agent_type))
            n += 1

        console.print(table)

    console.print()
    console.print("  [dim]🟦 CLI = שיחה בטרמינל | 🟨 SCRIPT = הרצה חד-פעמית | 🟩 WEB = Streamlit | 🟪 AGENT = Claude Code sub-agent[/dim]")
    console.print()
    return all_agents


def run_agent(name: str, path: str, agent_type: str):
    full_path = os.path.join(BASE, path)

    if agent_type == "subagent":
        # Show the sub-agent instructions
        console.print(Panel(
            f"[bold]Agent: {name}[/bold]\n\n"
            f"[cyan]כדי להשתמש ב-agent זה בתוך Claude Code:[/cyan]\n\n"
            f"[yellow]1.[/yellow] העתק את הקובץ:\n"
            f"   [dim]cp {full_path} .claude/agents/[/dim]\n\n"
            f"[yellow]2.[/yellow] בתוך Claude Code, הפעל עם:\n"
            f"   [bold magenta]/meeting-notes[/bold magenta]  (לפי שם ה-agent)\n\n"
            f"[yellow]3.[/yellow] הדבק טקסט ותן ל-agent לעבד.",
            title="📋 Sub-Agent Usage",
            border_style="magenta",
        ))

        # Show content
        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read()
            if Prompt.ask("\n[yellow]הצג תוכן הקובץ?[/yellow]", choices=["y", "n"], default="n") == "y":
                console.print(content)
        except Exception as e:
            console.print(f"[red]שגיאה בקריאת הקובץ: {e}[/red]")

    elif agent_type == "dashboard":
        console.print(f"\n[bold green]🌐 פותח Dashboard: {name}[/bold green]")
        console.print(f"[dim]→ http://localhost:8501[/dim]\n")
        try:
            subprocess.run([PYTHON, "-m", "streamlit", "run", full_path], check=True)
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard נסגר.[/yellow]")
        except FileNotFoundError:
            console.print("[red]❌ streamlit לא מותקן. הרץ: pip install streamlit[/red]")

    else:
        # CLI or Script
        console.print(f"\n[bold cyan]▶ מריץ: {name}[/bold cyan]\n")
        try:
            subprocess.run([PYTHON, full_path], check=False)
        except KeyboardInterrupt:
            console.print("\n[yellow]הופסק.[/yellow]")
        except Exception as e:
            console.print(f"[red]שגיאה: {e}[/red]")


def check_env():
    """Check for API key and warn if missing."""
    try:
        from shared.config import config
        if not config.has_api_key():
            console.print(Panel(
                "[yellow]⚠️  ANTHROPIC_API_KEY לא מוגדר![/yellow]\n\n"
                "[white]ה-agents עובדים גם בלי API key, אבל תכונות ה-AI מושבתות.[/white]\n"
                "[cyan]להפעלת AI מלא:[/cyan]\n"
                "1. עבור ל- [link]https://console.anthropic.com[/link] → API Keys → Create Key\n"
                "2. העתק [bold].env.example[/bold] → [bold].env[/bold]\n"
                "3. הוסף: [bold]ANTHROPIC_API_KEY=sk-ant-api03-...[/bold]",
                border_style="yellow",
            ))
    except ImportError:
        console.print("[red]⚠️  חסרה חבילת python-dotenv. הרץ: pip install -r requirements.txt[/red]")


def main():
    try:
        print_header()
        check_env()
        console.print()

        while True:
            all_agents = print_menu()

            choice = Prompt.ask(
                "[bold yellow]בחר agent (מספר) או [bold red]0[/bold red] ליציאה[/bold yellow]",
                default="0"
            )

            if choice == "0" or choice.lower() in ("q", "quit", "exit", "יציאה"):
                console.print("\n[bold green]להתראות! 👋[/bold green]\n")
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(all_agents):
                    name, path, agent_type = all_agents[idx]
                    run_agent(name, path, agent_type)
                    console.print("\n[dim]לחץ Enter לחזרה לתפריט...[/dim]")
                    input()
                else:
                    console.print(f"[red]נא לבחור בין 1 ל-{len(all_agents)}[/red]")
            except ValueError:
                console.print("[red]נא להזין מספר[/red]")

    except KeyboardInterrupt:
        console.print("\n\n[bold green]להתראות! 👋[/bold green]\n")


if __name__ == "__main__":
    main()
