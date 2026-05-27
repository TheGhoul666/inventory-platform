"""🎯 Savings Goals — מעקב יעדי חיסכון (Streamlit)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

st.set_page_config(page_title="Savings Goals", page_icon="🎯", layout="wide")
db = Storage()

GOAL_ICONS = ["🏖️ חופשה", "🚗 רכב", "🏠 דירה", "🎓 לימודים", "💍 חתונה",
              "🆘 קרן חירום", "💻 טכנולוגיה", "👴 פרישה", "🎁 מתנה", "💰 כללי"]


def main():
    st.title("🎯 Savings Goals")
    st.caption("מעקב יעדי חיסכון אישי")

    with st.sidebar:
        st.header("➕ יעד חדש")
        with st.form("new_goal"):
            icon_idx = st.selectbox("סוג", range(len(GOAL_ICONS)), format_func=lambda x: GOAL_ICONS[x])
            name = st.text_input("שם היעד")
            target = st.number_input("סכום יעד ₪", min_value=1.0, format="%.0f")
            current_saved = st.number_input("כבר חסכתי ₪", min_value=0.0, format="%.0f")
            deadline = st.date_input("תאריך יעד")
            priority = st.select_slider("עדיפות", options=["נמוכה", "בינונית", "גבוהה"])

            if st.form_submit_button("➕ צור יעד") and name:
                db.save("savings_goals", {
                    "icon": GOAL_ICONS[icon_idx],
                    "name": name,
                    "target": target,
                    "saved": current_saved,
                    "deadline": str(deadline),
                    "priority": priority,
                    "created_at": datetime.now().strftime("%d/%m/%Y"),
                })
                st.success(f"יעד '{name}' נוצר!")
                st.rerun()

    goals = db.list_all("savings_goals")

    if not goals:
        st.info("🎯 הגדר את יעד החיסכון הראשון שלך בסרגל הצד!")
        return

    # Summary metrics
    total_target = sum(g.get("target", 0) for g in goals)
    total_saved = sum(g.get("saved", 0) for g in goals)

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 סה\"כ חסכתי", f"₪{total_saved:,.0f}")
    col2.metric("🎯 סה\"כ יעד", f"₪{total_target:,.0f}")
    col3.metric("📊 התקדמות כוללת", f"{total_saved/total_target*100:.0f}%" if total_target > 0 else "0%")

    st.divider()

    # Goals sorted by priority
    priority_order = {"גבוהה": 0, "בינונית": 1, "נמוכה": 2}
    sorted_goals = sorted(goals, key=lambda g: priority_order.get(g.get("priority", "נמוכה"), 2))

    for goal in sorted_goals:
        _render_goal(goal)


def _render_goal(goal: dict):
    saved = goal.get("saved", 0)
    target = goal.get("target", 1)
    progress = min(saved / target, 1.0)
    remaining = max(target - saved, 0)

    # Calculate projected completion
    contributions = db.list_all("savings_contributions")
    goal_contribs = [c for c in contributions if str(c.get("goal_id")) == str(goal["_id"])]

    with st.container():
        st.subheader(f"{goal.get('icon', '')} {goal.get('name', '')}")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            pct = progress * 100
            color = "🟢" if pct >= 75 else "🟡" if pct >= 40 else "🔴"
            st.progress(progress, text=f"{color} {pct:.1f}% — ₪{saved:,.0f} / ₪{target:,.0f}")

        with col2:
            st.metric("נותר", f"₪{remaining:,.0f}")
            st.caption(f"📅 יעד: {goal.get('deadline', '—')}")

        with col3:
            priority_colors = {"גבוהה": "🔴", "בינונית": "🟡", "נמוכה": "🟢"}
            st.write(f"עדיפות: {priority_colors.get(goal.get('priority', ''), '')} {goal.get('priority', '')}")

            if goal_contribs:
                avg_contrib = sum(c.get("amount", 0) for c in goal_contribs) / len(goal_contribs)
                if avg_contrib > 0:
                    months_left = remaining / avg_contrib
                    st.caption(f"⏱️ ~{months_left:.1f} חודשים בקצב הנוכחי")

        # Add contribution
        with st.expander("💰 הוסף הפקדה"):
            c1, c2, c3 = st.columns(3)
            amount = c1.number_input("סכום ₪", min_value=1.0, key=f"amt_{goal['_id']}")
            contrib_date = c2.date_input("תאריך", key=f"date_{goal['_id']}")
            note = c3.text_input("הערה", key=f"note_{goal['_id']}")

            if st.button("💾 הוסף הפקדה", key=f"add_{goal['_id']}"):
                new_saved = saved + amount
                db.save("savings_contributions", {
                    "goal_id": goal["_id"],
                    "goal_name": goal.get("name"),
                    "amount": amount,
                    "date": str(contrib_date),
                    "note": note,
                })
                clean = {k: v for k, v in goal.items() if not k.startswith("_")}
                clean["saved"] = new_saved
                db.update("savings_goals", goal["_id"], clean)
                st.success(f"₪{amount:,.0f} נוספו! 🎉")
                st.rerun()

            # Show history
            if goal_contribs:
                st.write("**היסטוריית הפקדות:**")
                for c in goal_contribs[:5]:
                    st.caption(f"₪{c.get('amount', 0):,.0f} — {c.get('date', '—')} {c.get('note', '')}")

        # AI Motivation
        if config.has_api_key() and st.button("🤖 מוטיבציה מ-AI", key=f"mot_{goal['_id']}"):
            with st.spinner("..."):
                try:
                    client = ClaudeClient()
                    resp = client.chat(
                        "אתה מאמן אישי פיננסי מעודד. ענה בעברית בצורה חמה ומעוררת השראה.",
                        f"אני חוסך ל: {goal.get('icon')} {goal.get('name')}\n"
                        f"חסכתי: ₪{saved:,.0f} מתוך ₪{target:,.0f}\n"
                        f"יעד: {goal.get('deadline')}\n"
                        f"תן מילה מעודדת ו-3 טיפים ספציפיים להגיע ליעד."
                    )
                    st.success(resp)
                except Exception as e:
                    st.error(f"שגיאה: {e}")

        st.divider()


if __name__ == "__main__":
    main()
