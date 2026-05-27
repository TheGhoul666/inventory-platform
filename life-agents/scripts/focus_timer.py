"""🍅 Focus Timer — טיימר פוקוס Pomodoro."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage

db = Storage()
CATEGORY = "focus_sessions"


def run_timer(label: str, seconds: int) -> bool:
    """Run countdown timer. Returns True if completed."""
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
    from rich.live import Live
    from shared.ui import console

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[bold yellow]{task.fields[remaining]}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                label,
                total=seconds,
                remaining=f"{seconds // 60:02d}:{seconds % 60:02d}",
            )
            for elapsed in range(seconds):
                time.sleep(1)
                remaining = seconds - elapsed - 1
                progress.update(
                    task,
                    advance=1,
                    remaining=f"{remaining // 60:02d}:{remaining % 60:02d}",
                )
        return True
    except KeyboardInterrupt:
        return False


def pomodoro_session() -> None:
    UI.rule("🍅 סשן פוקוס חדש")
    task_name = UI.input("על מה אתה עובד?")
    work_mins = int(UI.input("זמן עבודה (דקות)", default="25"))
    break_mins = int(UI.input("זמן הפסקה (דקות)", default="5"))
    rounds = int(UI.input("כמה סבבים?", default="4"))

    from shared.ui import console
    total_focus = 0
    completed_rounds = 0

    for i in range(1, rounds + 1):
        UI.rule(f"🍅 סבב {i}/{rounds} — {task_name}")
        console.print(f"[bold green]▶ מתחיל {work_mins} דקות של פוקוס...[/bold green]")

        completed = run_timer(f"💪 עובד על: {task_name}", work_mins * 60)

        if not completed:
            UI.warning("הטיימר הופסק")
            break

        print('\a')  # Bell notification
        total_focus += work_mins
        completed_rounds += 1
        UI.success(f"סבב {i} הושלם! 🎉 +{work_mins} דקות")

        if i < rounds:
            console.print(f"[bold cyan]☕ הפסקה של {break_mins} דקות...[/bold cyan]")
            run_timer("☕ הפסקה", break_mins * 60)
            print('\a')

    # Save session
    if completed_rounds > 0:
        db.save(CATEGORY, {
            "task": task_name,
            "rounds_completed": completed_rounds,
            "rounds_planned": rounds,
            "focus_minutes": total_focus,
            "date": datetime.now().strftime("%d/%m/%Y"),
            "time": datetime.now().strftime("%H:%M"),
        })
        UI.success(f"✅ סשן הסתיים! {completed_rounds} סבבים | {total_focus} דקות פוקוס")
    else:
        UI.warning("סשן לא הושלם")


def view_stats() -> None:
    sessions = db.list_all(CATEGORY)
    if not sessions:
        UI.info("אין סשנים קודמים.")
        return

    total_minutes = sum(s.get("focus_minutes", 0) for s in sessions)
    total_sessions = len(sessions)
    today = datetime.now().strftime("%d/%m/%Y")
    today_minutes = sum(s.get("focus_minutes", 0) for s in sessions if s.get("date") == today)

    from shared.ui import console
    console.print(f"\n  ⏱️  סה\"כ זמן פוקוס: [bold green]{total_minutes // 60}h {total_minutes % 60}m[/bold green]")
    console.print(f"  🍅 סה\"כ סשנים: [bold]{total_sessions}[/bold]")
    console.print(f"  ☀️  היום: [bold cyan]{today_minutes} דקות[/bold cyan]\n")

    rows = [
        [s.get("date", "—"), s.get("task", "—"), str(s.get("rounds_completed", 0)), f"{s.get('focus_minutes', 0)} דק'"]
        for s in sessions[:10]
    ]
    UI.table("📊 סשנים אחרונים", ["תאריך", "משימה", "סבבים", "זמן פוקוס"], rows)


def main() -> None:
    UI.header("🍅 Focus Timer", "Pomodoro — עבודה מרוכזת")

    while True:
        choice = UI.menu("תפריט", [
            "▶ התחל סשן פוקוס",
            "📊 סטטיסטיקות",
            "🚪 יציאה",
        ])
        if choice == 0:
            pomodoro_session()
        elif choice == 1:
            view_stats()
        elif choice == 2:
            UI.success("יאללה לעבוד! 💪")
            break


if __name__ == "__main__":
    main()
