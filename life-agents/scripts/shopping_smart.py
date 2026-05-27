"""🛒 Shopping Smart — רשימת קניות חכמה."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage

db = Storage()
CATEGORY = "shopping_items"

CATS = ["🥦 פירות וירקות", "🥛 מוצרי חלב", "🥩 בשר ודגים", "🍞 לחם ומאפים",
        "🥫 מזון יבש", "🧴 ניקיון וטיפוח", "🧊 קפואים", "🧃 שתייה", "🔵 אחר"]
CAT_KEYS = ["produce", "dairy", "meat", "bakery", "dry_goods", "cleaning", "frozen", "drinks", "other"]


def add_item() -> None:
    UI.rule("➕ הוספת פריט")
    name = UI.input("שם המוצר")
    if not name:
        return
    qty = UI.input("כמות", default="1")
    unit = UI.input("יחידה (יח'/ק\"ג/ליטר/גרם)", default="יח'")
    cat_idx = UI.menu("קטגוריה", CATS)
    price = UI.input("מחיר משוער ₪ (אופציונלי)", default="0")

    db.save(CATEGORY, {
        "name": name,
        "quantity": qty,
        "unit": unit,
        "category": CAT_KEYS[cat_idx],
        "category_name": CATS[cat_idx],
        "price_estimate": float(price) if price.replace('.', '').isdigit() else 0,
        "bought": False,
        "added_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    UI.success(f"'{name}' נוסף לרשימה!")


def view_list() -> None:
    items = db.list_all(CATEGORY)
    pending = [i for i in items if not i.get("bought")]
    bought = [i for i in items if i.get("bought")]

    if not items:
        UI.info("רשימת הקניות ריקה.")
        return

    if pending:
        rows = [
            [str(i["_id"]), i.get("name", "—"), f"{i.get('quantity', '')} {i.get('unit', '')}",
             i.get("category_name", "—"),
             f"₪{i.get('price_estimate', 0):.1f}" if i.get("price_estimate") else "—"]
            for i in pending
        ]
        UI.table("🛒 לקנות", ["#", "מוצר", "כמות", "קטגוריה", "מחיר"], rows)

    if bought:
        UI.info(f"✅ נקנו: {len(bought)} פריטים")

    total = sum(i.get("price_estimate", 0) for i in pending if i.get("price_estimate"))
    if total > 0:
        from shared.ui import console
        console.print(f"\n  💰 סה\"כ משוער: [bold green]₪{total:.2f}[/bold green]")


def mark_bought() -> None:
    items = [i for i in db.list_all(CATEGORY) if not i.get("bought")]
    if not items:
        UI.info("אין פריטים לסמן.")
        return

    rows = [[str(i["_id"]), i.get("name", "—"), f"{i.get('quantity','')} {i.get('unit','')}"]
            for i in items]
    UI.table("🛒 בחר פריט לסמן כנקנה", ["#", "מוצר", "כמות"], rows)

    ids_input = UI.input("הכנס מספרים (מופרדים בפסיקים, או 'הכל')")
    if ids_input.lower() == "הכל":
        for item in items:
            clean = {k: v for k, v in item.items() if not k.startswith("_")}
            clean["bought"] = True
            db.update(CATEGORY, item["_id"], clean)
        UI.success(f"כל {len(items)} הפריטים סומנו כנקנו!")
    else:
        for id_str in ids_input.split(","):
            id_str = id_str.strip()
            if id_str.isdigit():
                item = db.load(CATEGORY, int(id_str))
                if item:
                    clean = {k: v for k, v in item.items() if not k.startswith("_")}
                    clean["bought"] = True
                    db.update(CATEGORY, int(id_str), clean)
                    UI.success(f"✅ {item.get('name', '')} — נקנה!")


def clear_bought() -> None:
    items = db.list_all(CATEGORY)
    bought = [i for i in items if i.get("bought")]
    if not bought:
        UI.info("אין פריטים נקנים למחיקה.")
        return
    if UI.confirm(f"מחק {len(bought)} פריטים נקנים?"):
        for item in bought:
            db.delete(CATEGORY, item["_id"])
        UI.success(f"נמחקו {len(bought)} פריטים!")


def import_from_meal_plan() -> None:
    plans = db.list_all("meal_plans")
    if not plans:
        UI.info("אין תוכניות ארוחות שמורות. צור תפריט שבועי ב-Meal Planner תחילה.")
        return

    latest = plans[0]
    content = latest.get("content", "")
    UI.info("תוכנית הארוחות האחרונה נטענה. חלץ מרכיבים ידנית מהתוכנית:")
    from shared.ui import console
    console.print(content[:800] + "..." if len(content) > 800 else content)
    UI.info("הוסף את המרכיבים ידנית דרך 'הוסף פריט'")


def main() -> None:
    UI.header("🛒 Shopping Smart", "רשימת קניות חכמה")

    while True:
        choice = UI.menu("תפריט", [
            "➕ הוסף פריט",
            "📋 הצג רשימה",
            "✅ סמן כנקנה",
            "🗑️  נקה פריטים שנקנו",
            "📅 ייבא ממתכון שבועי",
            "🚪 יציאה",
        ])
        if choice == 0:
            add_item()
        elif choice == 1:
            view_list()
        elif choice == 2:
            mark_bought()
        elif choice == 3:
            clear_bought()
        elif choice == 4:
            import_from_meal_plan()
        elif choice == 5:
            UI.success("קניות טובות! 🛒")
            break


if __name__ == "__main__":
    main()
