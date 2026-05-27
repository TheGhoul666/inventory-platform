"""🏠 Home Maintenance — מעקב תחזוקת בית (Streamlit)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime, timedelta
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

st.set_page_config(page_title="Home Maintenance", page_icon="🏠", layout="wide")
db = Storage()

CATEGORIES = ["🔧 אינסטלציה", "⚡ חשמל", "❄️ מיזוג/חימום", "🚿 שירותים ומקלחת",
              "🚗 רכב", "🌳 גינה", "🏠 כללי", "🔵 אחר"]


def main():
    st.title("🏠 Home Maintenance Tracker")

    with st.sidebar:
        st.header("➕ משימת תחזוקה")
        with st.form("add_task"):
            item = st.text_input("פריט (מה צריך תחזוקה?)")
            task_desc = st.text_area("תיאור", height=60)
            due_date = st.date_input("תאריך מתוכנן")
            category = st.selectbox("קטגוריה", CATEGORIES)
            recurring = st.checkbox("חוזר?")
            freq_days = st.number_input("כל כמה ימים?", min_value=1, value=90) if recurring else 0
            cost_est = st.number_input("עלות משוערת ₪", min_value=0.0, format="%.0f")

            if st.form_submit_button("➕ הוסף") and item:
                db.save("maintenance_tasks", {
                    "item": item,
                    "task": task_desc,
                    "due_date": str(due_date),
                    "category": category,
                    "recurring": recurring,
                    "frequency_days": int(freq_days),
                    "cost_estimate": cost_est,
                    "status": "pending",
                    "created_at": datetime.now().strftime("%d/%m/%Y"),
                })
                st.success(f"נוסף: {item}")
                st.rerun()

        st.divider()
        # AI Helper
        st.header("🤖 שאל את ה-AI")
        issue = st.text_area("תאר בעיה בבית:", height=80)
        if st.button("🔍 קבל עזרה") and issue and config.has_api_key():
            with st.spinner("..."):
                try:
                    client = ClaudeClient()
                    resp = client.chat(
                        "אתה מומחה לתחזוקת בית ואינסטלציה בישראל. ענה בעברית.",
                        f"בעיה: {issue}\n\nמה הסיבה האפשרית ואם כדאי לקרוא לאיש מקצוע?"
                    )
                    st.info(resp)
                except Exception as e:
                    st.error(f"שגיאה: {e}")

    # Main content
    tasks = db.list_all("maintenance_tasks")
    log = db.list_all("maintenance_log")

    today = datetime.now().date()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["⚠️ דחוף", "📅 כל המשימות", "📊 יומן תחזוקה"])

    with tab1:
        overdue_and_soon = []
        for t in tasks:
            if t.get("status") == "done":
                continue
            try:
                due = datetime.strptime(t.get("due_date", "2099-01-01"), "%Y-%m-%d").date()
                diff = (due - today).days
                if diff <= 7:
                    overdue_and_soon.append((diff, t))
            except Exception:
                pass

        if not overdue_and_soon:
            st.success("✅ אין משימות דחופות! הבית במצב מצוין.")
        else:
            for diff, t in sorted(overdue_and_soon, key=lambda x: x[0]):
                color = "🔴" if diff < 0 else "🟠" if diff <= 3 else "🟡"
                status_text = f"באיחור {abs(diff)} ימים" if diff < 0 else f"בעוד {diff} ימים"
                with st.container():
                    st.write(f"{color} **{t.get('item')}** — {t.get('task', '')} | {status_text}")
                    c1, c2 = st.columns([1, 4])
                    if c1.button("✅ בוצע", key=f"done_{t['_id']}"):
                        cost = c2.number_input("עלות בפועל ₪", key=f"cost_{t['_id']}", min_value=0.0)
                        clean = {k: v for k, v in t.items() if not k.startswith("_")}
                        clean["status"] = "done"
                        db.update("maintenance_tasks", t["_id"], clean)
                        db.save("maintenance_log", {
                            "item": t.get("item"),
                            "task": t.get("task"),
                            "completed_date": str(today),
                            "cost": cost,
                            "category": t.get("category"),
                        })
                        st.rerun()

    with tab2:
        pending = [t for t in tasks if t.get("status") != "done"]
        if not pending:
            st.info("אין משימות ממתינות.")
        else:
            for t in sorted(pending, key=lambda x: x.get("due_date", "9999")):
                st.write(f"{t.get('category', '')} | **{t.get('item')}** — {t.get('task', '')[:50]} | 📅 {t.get('due_date', '—')} | ₪{t.get('cost_estimate', 0):,.0f}")

    with tab3:
        if not log:
            st.info("אין יומן תחזוקה עדיין.")
        else:
            total_cost = sum(l.get("cost", 0) for l in log)
            st.metric("💰 עלות תחזוקה כוללת", f"₪{total_cost:,.0f}")

            for l in log[:20]:
                st.write(f"✅ {l.get('completed_date', '—')} | {l.get('item', '')} — {l.get('task', '')[:50]} | ₪{l.get('cost', 0):,.0f}")


if __name__ == "__main__":
    main()
