"""🗂️ Project Tracker — מעקב פרויקטים ומשימות (Streamlit)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

st.set_page_config(page_title="Project Tracker", page_icon="🗂️", layout="wide")

db = Storage()

st.markdown("""
<style>
.metric-card {background: #1e1e2e; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;}
.priority-high {color: #f38ba8;}
.priority-medium {color: #f9e2af;}
.priority-low {color: #a6e3a1;}
</style>
""", unsafe_allow_html=True)


def main():
    st.title("🗂️ Project Tracker")

    # Sidebar — New Project
    with st.sidebar:
        st.header("➕ פרויקט חדש")
        with st.form("new_project"):
            name = st.text_input("שם הפרויקט")
            desc = st.text_area("תיאור", height=80)
            deadline = st.date_input("תאריך יעד")
            status = st.selectbox("סטטוס", ["🟢 פעיל", "⏸️ מושהה", "✅ הושלם"])
            if st.form_submit_button("➕ צור פרויקט") and name:
                db.save("projects", {
                    "name": name,
                    "description": desc,
                    "deadline": str(deadline),
                    "status": status,
                    "created_at": datetime.now().strftime("%d/%m/%Y"),
                })
                st.success(f"פרויקט '{name}' נוצר!")
                st.rerun()

        st.divider()
        st.caption("ניווט")
        view = st.radio("", ["📋 כל הפרויקטים", "📊 סטטיסטיקות"], label_visibility="collapsed")

    projects = db.list_all("projects")

    if view == "📊 סטטיסטיקות":
        # Stats
        tasks = db.list_all("project_tasks")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("פרויקטים", len(projects))
        col2.metric("משימות כולל", len(tasks))
        active_tasks = [t for t in tasks if t.get("status") != "✅ הושלם"]
        col3.metric("משימות פתוחות", len(active_tasks))
        overdue = [t for t in tasks if t.get("due_date") and t.get("due_date") < datetime.now().strftime("%Y-%m-%d") and t.get("status") != "✅ הושלם"]
        col4.metric("⚠️ באיחור", len(overdue))
        return

    # Project list
    if not projects:
        st.info("אין פרויקטים עדיין. צור את הפרויקט הראשון בסרגל הצד!")
        return

    # Tabs per status
    tabs = st.tabs(["🟢 פעילים", "⏸️ מושהים", "✅ הושלמו", "📋 הכל"])
    filters = [("🟢 פעיל",), ("⏸️ מושהה",), ("✅ הושלם",), None]

    for tab, filter_status in zip(tabs, filters):
        with tab:
            filtered = [p for p in projects if filter_status is None or p.get("status") in filter_status]
            if not filtered:
                st.info("אין פרויקטים בקטגוריה זו.")
                continue
            for project in filtered:
                _render_project(project)


def _render_project(project: dict):
    pid = project["_id"]
    tasks = [t for t in db.list_all("project_tasks") if str(t.get("project_id")) == str(pid)]
    done_tasks = [t for t in tasks if t.get("status") == "✅ הושלם"]
    progress = len(done_tasks) / len(tasks) if tasks else 0

    with st.expander(f"{project.get('status', '')} **{project.get('name', '')}** — {project.get('deadline', '')}"):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(project.get("description", ""))
            st.progress(progress, text=f"{len(done_tasks)}/{len(tasks)} משימות הושלמו")

        with col2:
            st.metric("משימות", len(tasks))
            st.metric("הושלמו", len(done_tasks))

        # Tasks
        if tasks:
            st.subheader("📋 משימות")
            cols = st.columns([3, 2, 2, 2])
            cols[0].write("**משימה**")
            cols[1].write("**אחראי**")
            cols[2].write("**יעד**")
            cols[3].write("**סטטוס**")

            for task in tasks:
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                priority_icons = {"🔴 גבוהה": "🔴", "🟡 בינונית": "🟡", "🟢 נמוכה": "🟢"}
                icon = priority_icons.get(task.get("priority", ""), "")
                c1.write(f"{icon} {task.get('title', '')}")
                c2.write(task.get("assignee", "—"))
                c3.write(task.get("due_date", "—"))

                new_status = c4.selectbox(
                    "סטטוס",
                    ["📝 לביצוע", "🔄 בתהליך", "✅ הושלם"],
                    index=["📝 לביצוע", "🔄 בתהליך", "✅ הושלם"].index(task.get("status", "📝 לביצוע"))
                    if task.get("status") in ["📝 לביצוע", "🔄 בתהליך", "✅ הושלם"] else 0,
                    key=f"status_{task['_id']}",
                    label_visibility="collapsed"
                )
                if new_status != task.get("status"):
                    clean = {k: v for k, v in task.items() if not k.startswith("_")}
                    clean["status"] = new_status
                    db.update("project_tasks", task["_id"], clean)
                    st.rerun()

        # Add new task
        st.divider()
        with st.form(f"task_{pid}"):
            st.write("➕ הוסף משימה")
            c1, c2, c3, c4 = st.columns(4)
            title = c1.text_input("שם המשימה", key=f"t_{pid}")
            assignee = c2.text_input("אחראי", key=f"a_{pid}")
            due = c3.text_input("תאריך יעד", key=f"d_{pid}")
            priority = c4.selectbox("עדיפות", ["🔴 גבוהה", "🟡 בינונית", "🟢 נמוכה"], key=f"p_{pid}")

            if st.form_submit_button("הוסף") and title:
                db.save("project_tasks", {
                    "project_id": pid,
                    "title": title,
                    "assignee": assignee,
                    "due_date": due,
                    "priority": priority,
                    "status": "📝 לביצוע",
                })
                st.rerun()

        # AI Suggestions
        if config.has_api_key() and st.button(f"🤖 קבל המלצות AI לפרויקט", key=f"ai_{pid}"):
            with st.spinner("Claude מנתח..."):
                try:
                    client = ClaudeClient()
                    task_list = "\n".join(f"- {t.get('title')} [{t.get('status')}]" for t in tasks)
                    response = client.chat(
                        "אתה מנהל פרויקטים מנוסה. ענה בעברית.",
                        f"פרויקט: {project.get('name')}\n"
                        f"תיאור: {project.get('description')}\n"
                        f"יעד: {project.get('deadline')}\n"
                        f"משימות:\n{task_list or 'אין עדיין'}\n\n"
                        "מה הצעדים הבאים המומלצים?"
                    )
                    st.info(response)
                except Exception as e:
                    st.error(f"שגיאה: {e}")


if __name__ == "__main__":
    main()
