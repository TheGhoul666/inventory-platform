"""🔔 Bill Reminder — ניהול חשבונות ותשלומים חוזרים."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage

db = Storage()
CATEGORY = "bills"

BILL_CATS = ["⚡ חשמל", "💧 מים", "🌐 אינטרנט", "📱 סלולר", "🏠 שכירות/משכנתא",
             "🛡️ ביטוח", "📺 מנויים", "🚗 רכב", "💊 בריאות", "🔵 אחר"]
BILL_CAT_KEYS = ["electricity", "water", "internet", "mobile", "rent",
                  "insurance", "subscriptions", "car", "health", "other"]


def add_bill() -> None:
    UI.rule("➕ הוספת חשבון")
    name = UI.input("שם החשבון (למשל: חשמל, HOT, ביטוח לאומי)")
    if not name:
        return

    amount = UI.input("סכום ₪", default="0")
    due_day = UI.input("יום בחודש לתשלום (1-31)", default="1")
    freq_idx = UI.menu("תדירות", ["📅 חודשי", "📅 רבעוני", "📅 שנתי", "📅 חד-פעמי"])
    frequency = ["monthly", "quarterly", "yearly", "one_time"][freq_idx]

    cat_idx = UI.menu("קטגוריה", BILL_CATS)
    auto_pay = UI.confirm("תשלום אוטומטי?")
    notes = UI.input("הערות (אופציונלי)", default="")

    db.save(CATEGORY, {
        "name": name,
        "amount": float(amount) if amount.replace('.', '').isdigit() else 0,
        "due_day": int(due_day) if due_day.isdigit() else 1,
        "frequency": frequency,
        "category": BILL_CAT_KEYS[cat_idx],
        "category_name": BILL_CATS[cat_idx],
        "auto_pay": auto_pay,
        "notes": notes,
        "last_paid": None,
        "active": True,
    })
    UI.success(f"חשבון '{name}' נוסף!")


def view_upcoming() -> None:
    bills = [b for b in db.list_all(CATEGORY) if b.get("active")]
    if not bills:
        UI.info("אין חשבונות רשומים.")
        return

    today = datetime.now().day
    month_total = sum(b.get("amount", 0) for b in bills if b.get("frequency") in ("monthly", "one_time"))

    rows = []
    for b in sorted(bills, key=lambda x: abs(x.get("due_day", 0) - today)):
        due = b.get("due_day", 0)
        diff = due - today
        if diff < 0:
            status = "🔴 עבר"
        elif diff == 0:
            status = "🚨 היום!"
        elif diff <= 3:
            status = f"⚠️  בעוד {diff} ימים"
        elif diff <= 7:
            status = f"🟡 בעוד {diff} ימים"
        else:
            status = f"🟢 יום {due}"

        rows.append([
            b.get("name", "—"),
            f"₪{b.get('amount', 0):,.0f}",
            str(due),
            status,
            "✅" if b.get("auto_pay") else "❌",
            b.get("category_name", "—"),
        ])

    UI.table("🔔 חשבונות חוזרים", ["שם", "סכום", "יום", "סטטוס", "אוטומטי", "קטגוריה"], rows)
    from shared.ui import console
    console.print(f"\n  💰 סה\"כ חודשי: [bold red]₪{month_total:,.0f}[/bold red]")


def mark_paid() -> None:
    bills = [b for b in db.list_all(CATEGORY) if b.get("active")]
    if not bills:
        UI.info("אין חשבונות.")
        return

    rows = [[str(b["_id"]), b.get("name", "—"), f"₪{b.get('amount', 0):,.0f}",
             b.get("last_paid", "מעולם")] for b in bills]
    UI.table("בחר לסמן כשולם", ["#", "שם", "סכום", "שולם לאחרונה"], rows)

    bill_id = UI.input("מספר החשבון")
    if not bill_id.isdigit():
        return

    bill = db.load(CATEGORY, int(bill_id))
    if bill:
        clean = {k: v for k, v in bill.items() if not k.startswith("_")}
        clean["last_paid"] = datetime.now().strftime("%d/%m/%Y")
        db.update(CATEGORY, int(bill_id), clean)
        UI.success(f"'{bill.get('name', '')}' סומן כשולם ✅")


def delete_bill() -> None:
    bills = db.list_all(CATEGORY)
    rows = [[str(b["_id"]), b.get("name", "—")] for b in bills]
    UI.table("חשבונות", ["#", "שם"], rows)

    bill_id = UI.input("מספר החשבון למחיקה")
    if bill_id.isdigit() and UI.confirm("מחק?"):
        if db.delete(CATEGORY, int(bill_id)):
            UI.success("חשבון נמחק!")


def main() -> None:
    UI.header("🔔 Bill Reminder", "ניהול חשבונות ותשלומים חוזרים")

    while True:
        choice = UI.menu("תפריט", [
            "➕ הוסף חשבון",
            "📋 הצג חשבונות קרובים",
            "✅ סמן כשולם",
            "🗑️  מחק חשבון",
            "🚪 יציאה",
        ])
        if choice == 0:
            add_bill()
        elif choice == 1:
            view_upcoming()
        elif choice == 2:
            mark_paid()
        elif choice == 3:
            delete_bill()
        elif choice == 4:
            UI.success("להתראות! 🔔")
            break


if __name__ == "__main__":
    main()
