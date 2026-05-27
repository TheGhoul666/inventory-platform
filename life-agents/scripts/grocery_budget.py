"""💰 Grocery Budget — תקציב קניות חכם."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()


def get_budget() -> float:
    return float(db.get_setting("monthly_grocery_budget") or 800)


def set_budget() -> None:
    current = get_budget()
    new = UI.input(f"תקציב קניות חודשי ₪ (נוכחי: {current:.0f})", default=str(int(current)))
    try:
        db.set_setting("monthly_grocery_budget", float(new))
        UI.success(f"תקציב עודכן: ₪{new}")
    except ValueError:
        UI.error("ערך לא חוקי")


def log_purchase() -> None:
    UI.rule("🛒 רישום קנייה")
    store = UI.input("שם הסופר", default="")
    total = UI.input("סכום כולל ₪")
    try:
        float(total)
    except ValueError:
        UI.error("סכום לא חוקי")
        return

    date_str = UI.input("תאריך (DD/MM/YYYY)", default=datetime.now().strftime("%d/%m/%Y"))
    notes = UI.input("הערות (מה קנית)", default="")

    month = date_str[3:10] if len(date_str) >= 10 else datetime.now().strftime("%m/%Y")
    db.save("grocery_purchases", {
        "store": store,
        "amount": float(total),
        "date": date_str,
        "month": month,
        "notes": notes,
    })
    UI.success(f"קנייה של ₪{total} נרשמה!")
    _show_monthly_summary(month)


def _show_monthly_summary(month: str | None = None) -> None:
    if not month:
        month = datetime.now().strftime("%m/%Y")

    purchases = [p for p in db.list_all("grocery_purchases") if p.get("month") == month]
    total_spent = sum(p.get("amount", 0) for p in purchases)
    budget = get_budget()
    remaining = budget - total_spent
    pct = total_spent / budget * 100 if budget > 0 else 0

    from shared.ui import console
    UI.rule(f"📊 קניות {month}")
    color = "green" if remaining >= 0 else "red"
    console.print(f"  💰 תקציב: [bold]₪{budget:.0f}[/bold]")
    console.print(f"  🛒 הוצאתי: [bold red]₪{total_spent:.2f}[/bold red] ({pct:.0f}%)")
    console.print(f"  💵 נותר: [bold {color}]₪{remaining:.2f}[/bold {color}]")


def view_history() -> None:
    purchases = db.list_all("grocery_purchases")[:20]
    if not purchases:
        UI.info("אין רכישות רשומות.")
        return

    rows = [[p.get("date", "—"), p.get("store", "—"), f"₪{p.get('amount', 0):.2f}", p.get("notes", "—")[:30]]
            for p in purchases]
    UI.table("🛒 היסטוריית קניות", ["תאריך", "סופר", "סכום", "הערות"], rows)

    current_month = datetime.now().strftime("%m/%Y")
    _show_monthly_summary(current_month)


def ai_tips() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    month = datetime.now().strftime("%m/%Y")
    purchases = [p for p in db.list_all("grocery_purchases") if p.get("month") == month]
    total = sum(p.get("amount", 0) for p in purchases)
    budget = get_budget()

    stores = {}
    for p in purchases:
        s = p.get("store", "לא ידוע")
        stores[s] = stores.get(s, 0) + p.get("amount", 0)

    store_summary = "\n".join(f"- {s}: ₪{a:.0f}" for s, a in stores.items())

    system = "אתה מומחה לתקצוב וחסכון בקניות בסופר בישראל. ענה בעברית."
    prompt = (
        f"תקציב חודשי: ₪{budget:.0f}\n"
        f"הוצאתי עד כה: ₪{total:.2f}\n"
        f"נותר: ₪{budget - total:.2f}\n\n"
        f"חנויות:\n{store_summary or 'לא צוין'}\n\n"
        "תן 5 טיפים ספציפיים לחיסכון בקניות בישראל:\n"
        "- מה לקנות בחנויות זולות (ויקטורי, רמי לוי)\n"
        "- אלטרנטיבות זולות למוצרים יקרים\n"
        "- מה לקנות בכמות\n"
        "- תזמון קניות אופטימלי\n"
        "- כיצד להגיע ליעד"
    )

    UI.rule("🤖 טיפים לחיסכון")
    try:
        client = ClaudeClient()
        UI.stream_print(client.stream_chat(system, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def main() -> None:
    UI.header("💰 Grocery Budget", "תקציב קניות חכם")

    while True:
        choice = UI.menu("תפריט", [
            "🛒 רשום קנייה",
            "📊 סיכום חודשי",
            "📅 היסטוריית קניות",
            "🎯 הגדר תקציב",
            "🤖 טיפים לחיסכון",
            "🚪 יציאה",
        ])
        if choice == 0:
            log_purchase()
        elif choice == 1:
            _show_monthly_summary()
        elif choice == 2:
            view_history()
        elif choice == 3:
            set_budget()
        elif choice == 4:
            ai_tips()
        elif choice == 5:
            break

    UI.success("להתראות! 💰")


if __name__ == "__main__":
    main()
