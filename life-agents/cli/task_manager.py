"""📋 Task Manager — ניהול משימות עם עזרת AI."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "tasks"

PRIORITIES = {"high": "🔴 גבוהה", "medium": "🟡 בינונית", "low": "🟢 נמוכה"}
STATUSES = {"pending": "⏳ ממתין", "in_progress": "🔄 בתהליך", "done": "✅ הושלם"}


def add_task() -> None:
    UI.rule("➕ הוספת משימה חדשה")
    title = UI.input("שם המשימה")
    if not title:
        return
    desc = UI.input("תיאור (אופציונלי)", default="")
    pri_idx = UI.menu("עדיפות", ["🔴 גבוהה", "🟡 בינונית", "🟢 נמוכה"])
    priority = ["high", "medium", "low"][pri_idx]
    due = UI.input("תאריך יעד (DD/MM/YYYY, אופציונלי)", default="")
    tags = UI.input("תגיות (מופרדות בפסיק)", default="")

    task = {
        "title": title,
        "description": desc,
        "priority": priority,
        "due_date": due,
        "status": "pending",
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "created": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    task_id = db.save(CATEGORY, task)
    UI.success(f"משימה #{task_id} נוספה: {title}")


def view_tasks(filter_status: str = "all") -> list:
    tasks = db.list_all(CATEGORY)
    if filter_status != "all":
        tasks = [t for t in tasks if t.get("status") == filter_status]

    if not tasks:
        UI.info("אין משימות להצגה.")
        return []

    rows = []
    for t in tasks:
        rows.append([
            str(t["_id"]),
            t.get("title", ""),
            PRIORITIES.get(t.get("priority", "medium"), ""),
            STATUSES.get(t.get("status", "pending"), ""),
            t.get("due_date", "—"),
            ", ".join(t.get("tags", [])),
        ])

    UI.table(
        "📋 משימות",
        ["#", "משימה", "עדיפות", "סטטוס", "תאריך יעד", "תגיות"],
        rows,
    )
    return tasks


def update_task_status() -> None:
    tasks = view_tasks("pending")
    if not tasks:
        return
    task_id = UI.input("מספר המשימה לעדכון")
    try:
        task_id = int(task_id)
    except ValueError:
        UI.error("מספר לא חוקי")
        return

    task = db.load(CATEGORY, task_id)
    if not task:
        UI.error(f"משימה #{task_id} לא נמצאה")
        return

    status_idx = UI.menu("סטטוס חדש", ["⏳ ממתין", "🔄 בתהליך", "✅ הושלם"])
    new_status = ["pending", "in_progress", "done"][status_idx]
    task["status"] = new_status
    # Remove metadata keys before saving back
    clean = {k: v for k, v in task.items() if not k.startswith("_")}
    db.update(CATEGORY, task_id, clean)
    UI.success(f"משימה #{task_id} עודכנה ל-{STATUSES[new_status]}")


def delete_task() -> None:
    view_tasks()
    task_id = UI.input("מספר המשימה למחיקה")
    try:
        task_id = int(task_id)
    except ValueError:
        UI.error("מספר לא חוקי")
        return
    if UI.confirm(f"למחוק משימה #{task_id}?"):
        if db.delete(CATEGORY, task_id):
            UI.success(f"משימה #{task_id} נמחקה")
        else:
            UI.error("משימה לא נמצאה")


def ai_prioritize() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    tasks = db.list_all(CATEGORY)
    pending = [t for t in tasks if t.get("status") != "done"]
    if not pending:
        UI.info("אין משימות ממתינות לניתוח.")
        return

    task_list = "\n".join(
        f"- [{t.get('priority','medium').upper()}] {t.get('title','')} "
        f"(יעד: {t.get('due_date','לא ידוע')}) — {t.get('description','')}"
        for t in pending
    )

    system = (
        "אתה מנהל משימות מומחה. עזור למשתמש לתעדף את המשימות שלו בצורה חכמה. "
        "ענה בעברית, בצורה ברורה ומעשית."
    )
    prompt = (
        f"יש לי {len(pending)} משימות פתוחות:\n\n{task_list}\n\n"
        "תן לי:\n"
        "1. סדר עדיפויות מומלץ (ממוספר)\n"
        "2. הסבר קצר לכל בחירה\n"
        "3. אילו משימות ניתן לדחות\n"
        "4. טיפ אחד לניהול זמן"
    )

    UI.rule("🤖 ניתוח AI")
    try:
        client = ClaudeClient()
        UI.stream_print(client.stream_chat(system, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def main() -> None:
    UI.header("📋 Task Manager", "ניהול משימות חכם עם עזרת AI")

    options = [
        "➕ הוסף משימה חדשה",
        "📋 הצג כל המשימות",
        "⏳ הצג משימות פתוחות בלבד",
        "✅ הצג משימות שהושלמו",
        "🔄 עדכן סטטוס משימה",
        "🗑️  מחק משימה",
        "🤖 בקש מ-AI לתעדף משימות",
        "🚪 יציאה",
    ]

    while True:
        console_choice = UI.menu("תפריט ראשי", options)
        if console_choice == 0:
            add_task()
        elif console_choice == 1:
            view_tasks("all")
        elif console_choice == 2:
            view_tasks("pending")
        elif console_choice == 3:
            view_tasks("done")
        elif console_choice == 4:
            update_task_status()
        elif console_choice == 5:
            delete_task()
        elif console_choice == 6:
            ai_prioritize()
        elif console_choice == 7:
            UI.success("להתראות! 👋")
            break


if __name__ == "__main__":
    main()
