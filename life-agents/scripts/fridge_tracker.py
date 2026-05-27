"""🧊 Fridge Tracker — מה יש במקרר ומה אפשר לבשל."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "fridge_items"


def add_item() -> None:
    UI.rule("➕ הוספת פריט")
    name = UI.input("שם המוצר")
    if not name:
        return

    qty = UI.input("כמות", default="1")
    unit = UI.input("יחידה", default="יח'")
    loc_idx = UI.menu("מיקום", ["🥶 מקפיא", "🧊 מקרר", "🗄️  מזווה/ארון"])
    location = ["freezer", "fridge", "pantry"][loc_idx]

    expiry = UI.input("תאריך תפוגה (DD/MM/YYYY, Enter לדלג)", default="")

    db.save(CATEGORY, {
        "name": name,
        "quantity": qty,
        "unit": unit,
        "location": location,
        "expiry_date": expiry,
        "added_date": datetime.now().strftime("%d/%m/%Y"),
    })
    UI.success(f"'{name}' נוסף!")


def view_inventory() -> None:
    items = db.list_all(CATEGORY)
    if not items:
        UI.info("המקרר/מזווה ריק.")
        return

    today = datetime.now()
    rows = []
    for item in sorted(items, key=lambda x: x.get("expiry_date", "99/99/9999")):
        expiry = item.get("expiry_date", "")
        status = "—"
        if expiry:
            try:
                exp_date = datetime.strptime(expiry, "%d/%m/%Y")
                diff = (exp_date - today).days
                if diff < 0:
                    status = "🔴 פג תוקף!"
                elif diff <= 2:
                    status = f"🔴 {diff} ימים"
                elif diff <= 7:
                    status = f"🟡 {diff} ימים"
                else:
                    status = f"🟢 {diff} ימים"
            except Exception:
                status = expiry

        loc_emoji = {"freezer": "🥶", "fridge": "🧊", "pantry": "🗄️"}.get(item.get("location", ""), "")
        rows.append([
            str(item["_id"]),
            item.get("name", "—"),
            f"{item.get('quantity', '')} {item.get('unit', '')}",
            loc_emoji,
            status,
        ])

    UI.table("🧊 מלאי מטבח", ["#", "מוצר", "כמות", "מיקום", "תוקף"], rows)


def remove_item() -> None:
    view_inventory()
    item_id = UI.input("# למחיקה")
    if item_id.isdigit():
        if db.delete(CATEGORY, int(item_id)):
            UI.success("פריט הוסר!")


def what_can_i_cook() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    items = db.list_all(CATEGORY)
    if not items:
        UI.info("אין פריטים במלאי.")
        return

    today = datetime.now()
    # Filter out expired items
    valid_items = []
    for item in items:
        expiry = item.get("expiry_date", "")
        if expiry:
            try:
                exp = datetime.strptime(expiry, "%d/%m/%Y")
                if exp < today:
                    continue
            except Exception:
                pass
        valid_items.append(item)

    ingredients = ", ".join(f"{i.get('name')} ({i.get('quantity')} {i.get('unit','')})"
                            for i in valid_items)

    UI.rule("👨‍🍳 מה אפשר לבשל?")
    prompt = (
        f"יש לי את המרכיבים הבאים:\n{ingredients}\n\n"
        "הצע 3 ארוחות שאפשר להכין עכשיו:\n"
        "- ארוחה מהירה (עד 20 דקות)\n"
        "- ארוחה בינונית (עד 45 דקות)\n"
        "- ארוחה יצירתית ומפורטת\n"
        "לכל ארוחה: שם, מרכיבים הנדרשים, הוראות קצרות"
    )

    try:
        client = ClaudeClient()
        UI.stream_print(client.stream_chat(
            "אתה שף מקצועי. ענה בעברית.", prompt
        ))
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def main() -> None:
    UI.header("🧊 Fridge Tracker", "מה יש במקרר ומה לבשל")

    while True:
        choice = UI.menu("תפריט", [
            "➕ הוסף מוצר",
            "📋 הצג מלאי",
            "🗑️  הסר מוצר",
            "👨‍🍳 מה אפשר לבשל?",
            "🚪 יציאה",
        ])
        if choice == 0:
            add_item()
        elif choice == 1:
            view_inventory()
        elif choice == 2:
            remove_item()
        elif choice == 3:
            what_can_i_cook()
        elif choice == 4:
            break

    UI.success("להתראות! 🧊")


if __name__ == "__main__":
    main()
