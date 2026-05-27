"""💸 Budget Tracker — מעקב תקציב עם תובנות AI."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from collections import defaultdict
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()

EXPENSE_CATS = ["🍔 אוכל", "🚗 תחבורה", "🎮 בידור", "⚡ שירותים", "👕 קניות", "🏥 בריאות", "📚 חינוך", "🏠 בית", "💼 עבודה", "🔵 אחר"]
EXPENSE_KEYS = ["food", "transport", "entertainment", "utilities", "shopping", "health", "education", "home", "work", "other"]


def add_expense() -> None:
    UI.rule("💸 הוספת הוצאה")
    amount = UI.input("סכום (₪)")
    try:
        float(amount)
    except ValueError:
        UI.error("סכום לא חוקי")
        return

    cat_idx = UI.menu("קטגוריה", EXPENSE_CATS)
    desc = UI.input("תיאור")
    date_str = UI.input("תאריך (DD/MM/YYYY)", default=datetime.now().strftime("%d/%m/%Y"))

    db.save("expenses", {
        "amount": float(amount),
        "category": EXPENSE_KEYS[cat_idx],
        "category_name": EXPENSE_CATS[cat_idx],
        "description": desc,
        "date": date_str,
        "month": date_str[3:10] if len(date_str) >= 10 else datetime.now().strftime("%m/%Y"),
    })
    UI.success(f"הוצאה של ₪{amount} נרשמה! ({EXPENSE_CATS[cat_idx]})")


def add_income() -> None:
    UI.rule("💰 הוספת הכנסה")
    amount = UI.input("סכום (₪)")
    try:
        float(amount)
    except ValueError:
        UI.error("סכום לא חוקי")
        return

    source = UI.input("מקור (משכורת/פרילנס/שכר דירה/אחר)", default="משכורת")
    date_str = UI.input("תאריך", default=datetime.now().strftime("%d/%m/%Y"))

    db.save("income", {
        "amount": float(amount),
        "source": source,
        "date": date_str,
        "month": date_str[3:10] if len(date_str) >= 10 else datetime.now().strftime("%m/%Y"),
    })
    UI.success(f"הכנסה של ₪{amount} נרשמה!")


def monthly_summary() -> None:
    current_month = datetime.now().strftime("%m/%Y")
    expenses = db.list_all("expenses")
    income_records = db.list_all("income")

    month_expenses = [e for e in expenses if e.get("month") == current_month]
    month_income = [i for i in income_records if i.get("month") == current_month]

    total_expense = sum(e.get("amount", 0) for e in month_expenses)
    total_income = sum(i.get("amount", 0) for i in month_income)
    balance = total_income - total_expense

    UI.rule(f"📊 סיכום חודשי — {current_month}")
    from shared.ui import console
    console.print(f"  💰 הכנסות:  [bold green]₪{total_income:,.2f}[/bold green]")
    console.print(f"  💸 הוצאות:  [bold red]₪{total_expense:,.2f}[/bold red]")
    balance_color = "green" if balance >= 0 else "red"
    console.print(f"  💼 יתרה:    [bold {balance_color}]₪{balance:,.2f}[/bold {balance_color}]")

    # Category breakdown
    by_cat: dict = defaultdict(float)
    for e in month_expenses:
        by_cat[e.get("category_name", "אחר")] += e.get("amount", 0)

    if by_cat:
        rows = sorted(
            [[cat, f"₪{amt:,.2f}", f"{amt/total_expense*100:.1f}%" if total_expense else "0%"]
             for cat, amt in by_cat.items()],
            key=lambda x: float(x[1][1:].replace(",", "")),
            reverse=True,
        )
        UI.table("הוצאות לפי קטגוריה", ["קטגוריה", "סכום", "אחוז"], rows)


def ai_insights() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    current_month = datetime.now().strftime("%m/%Y")
    expenses = [e for e in db.list_all("expenses") if e.get("month") == current_month]
    income_records = [i for i in db.list_all("income") if i.get("month") == current_month]

    total_expense = sum(e.get("amount", 0) for e in expenses)
    total_income = sum(i.get("amount", 0) for i in income_records)

    by_cat: dict = defaultdict(float)
    for e in expenses:
        by_cat[e.get("category_name", "אחר")] += e.get("amount", 0)

    breakdown = "\n".join(f"- {cat}: ₪{amt:,.2f}" for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]))

    system = "אתה יועץ פיננסי אישי מומחה לשוק הישראלי. ענה בעברית, בצורה מעשית ואישית."
    prompt = (
        f"סיכום חודשי של המשתמש:\n"
        f"- הכנסה: ₪{total_income:,.2f}\n"
        f"- הוצאות: ₪{total_expense:,.2f}\n"
        f"- יתרה: ₪{total_income - total_expense:,.2f}\n\n"
        f"פירוט הוצאות:\n{breakdown}\n\n"
        "תן:\n"
        "1. 📊 ניתוח דפוסי הוצאות\n"
        "2. 🚨 אזהרות (אם יש הוצאה גבוהה מדי בקטגוריה)\n"
        "3. 💡 3 המלצות ספציפיות לחסכון\n"
        "4. 🎯 יעד חיסכון ריאלי לחודש הבא"
    )

    UI.rule("🤖 תובנות AI")
    try:
        client = ClaudeClient()
        UI.stream_print(client.stream_chat(system, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def main() -> None:
    UI.header("💸 Budget Tracker", "מעקב תקציב אישי עם תובנות AI")

    while True:
        choice = UI.menu("תפריט", [
            "💸 הוסף הוצאה",
            "💰 הוסף הכנסה",
            "📊 סיכום חודשי",
            "🤖 תובנות AI",
            "🚪 יציאה",
        ])
        if choice == 0:
            add_expense()
        elif choice == 1:
            add_income()
        elif choice == 2:
            monthly_summary()
        elif choice == 3:
            ai_insights()
        elif choice == 4:
            UI.success("להתראות! 💸")
            break


if __name__ == "__main__":
    main()
