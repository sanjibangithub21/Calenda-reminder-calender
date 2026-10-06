"""
Database management module for Calendar and Reminder App.
Handles SQLite operations for persisting reminders, status, and categories.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class ReminderDatabase:
    """Thread-safe SQLite database manager for reminders."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to reminders.db in the same directory as this module
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, "reminders.db")
        else:
            self.db_path = db_path
        self._mem_conn = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a SQLite connection with row factory enabled."""
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Creates the necessary tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,            -- YYYY-MM-DD
                    time TEXT NOT NULL,            -- HH:MM (24-hour format)
                    category TEXT NOT NULL DEFAULT 'General',
                    description TEXT DEFAULT '',
                    completed INTEGER NOT NULL DEFAULT 0,
                    notified INTEGER NOT NULL DEFAULT 0,
                    alarm_enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reminders_date 
                ON reminders(date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reminders_due 
                ON reminders(date, time, notified, completed)
            """)
            conn.commit()

    def add_reminder(
        self,
        title: str,
        date: str,
        time: str,
        category: str = "General",
        description: str = "",
        alarm_enabled: bool = True,
    ) -> int:
        """Adds a new reminder and returns its generated ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO reminders (title, date, time, category, description, alarm_enabled, completed, notified)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
                """,
                (title.strip(), date, time, category, description.strip(), 1 if alarm_enabled else 0),
            )
            conn.commit()
            return cursor.lastrowid

    def update_reminder(
        self,
        reminder_id: int,
        title: str,
        date: str,
        time: str,
        category: str = "General",
        description: str = "",
        alarm_enabled: bool = True,
    ) -> bool:
        """Updates an existing reminder."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE reminders
                SET title = ?, date = ?, time = ?, category = ?, description = ?, alarm_enabled = ?, notified = 0
                WHERE id = ?
                """,
                (title.strip(), date, time, category, description.strip(), 1 if alarm_enabled else 0, reminder_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_reminder(self, reminder_id: int) -> bool:
        """Deletes a reminder by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_reminder(self, reminder_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single reminder by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_reminders_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Retrieves all reminders for a specific date (YYYY-MM-DD), ordered by time."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM reminders
                WHERE date = ?
                ORDER BY completed ASC, time ASC, id ASC
                """,
                (date_str,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_reminders_for_month(self, year: int, month: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves all reminders for a specific month and groups them by date string (YYYY-MM-DD).
        """
        month_prefix = f"{year:04d}-{month:02d}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM reminders
                WHERE date LIKE ?
                ORDER BY date ASC, time ASC
                """,
                (f"{month_prefix}%",),
            )
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for row in cursor.fetchall():
                data = dict(row)
                d = data["date"]
                if d not in grouped:
                    grouped[d] = []
                grouped[d].append(data)
            return grouped

    def get_all_reminders(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Retrieves reminders ordered by date and time."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM reminders
                ORDER BY date DESC, time ASC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_upcoming_reminders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves pending upcoming reminders from today onwards."""
        today = datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%H:%M")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM reminders
                WHERE completed = 0 AND (date > ? OR (date = ? AND time >= ?))
                ORDER BY date ASC, time ASC
                LIMIT ?
                """,
                (today, today, now_time, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_due_reminders(self) -> List[Dict[str, Any]]:
        """
        Finds all active, unnotified reminders whose scheduled date/time is now or has passed.
        Only considers uncompleted reminders with alarm_enabled = 1.
        """
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM reminders
                WHERE completed = 0
                  AND notified = 0
                  AND alarm_enabled = 1
                  AND (date < ? OR (date = ? AND time <= ?))
                ORDER BY date ASC, time ASC
                """,
                (current_date, current_date, current_time),
            )
            return [dict(row) for row in cursor.fetchall()]

    def mark_notified(self, reminder_id: int) -> None:
        """Marks a reminder as notified so it does not trigger repeatedly."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE reminders SET notified = 1 WHERE id = ?",
                (reminder_id,),
            )
            conn.commit()

    def toggle_completed(self, reminder_id: int) -> bool:
        """Toggles the completed status of a reminder. Returns new status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT completed FROM reminders WHERE id = ?", (reminder_id,))
            row = cursor.fetchone()
            if not row:
                return False
            new_status = 0 if row["completed"] else 1
            cursor.execute(
                "UPDATE reminders SET completed = ? WHERE id = ?",
                (new_status, reminder_id),
            )
            conn.commit()
            return bool(new_status)

    def snooze_reminder(self, reminder_id: int, minutes: int = 10) -> Optional[Dict[str, str]]:
        """
        Snoozes a reminder by pushing its time forward by the given minutes.
        Resets its notified state.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT date, time FROM reminders WHERE id = ?", (reminder_id,))
            row = cursor.fetchone()
            if not row:
                return None

            try:
                current_dt = datetime.strptime(f"{row['date']} {row['time']}", "%Y-%m-%d %H:%M")
            except ValueError:
                current_dt = datetime.now()

            # Ensure snooze is scheduled in the future
            now = datetime.now()
            base_dt = max(current_dt, now)
            new_dt = base_dt + timedelta(minutes=minutes)

            new_date = new_dt.strftime("%Y-%m-%d")
            new_time = new_dt.strftime("%H:%M")

            cursor.execute(
                """
                UPDATE reminders
                SET date = ?, time = ?, notified = 0, completed = 0
                WHERE id = ?
                """,
                (new_date, new_time, reminder_id),
            )
            conn.commit()
            return {"date": new_date, "time": new_time}

    def search_reminders(self, query: str) -> List[Dict[str, Any]]:
        """Searches reminders by title, description, or category."""
        q = f"%{query.strip()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM reminders
                WHERE title LIKE ? OR description LIKE ? OR category LIKE ?
                ORDER BY date DESC, time ASC
                LIMIT 100
                """,
                (q, q, q),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, int]:
        """Returns summary statistics for the user dashboard."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM reminders")
            total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS completed FROM reminders WHERE completed = 1")
            completed = cursor.fetchone()["completed"]

            cursor.execute("SELECT COUNT(*) AS today_pending FROM reminders WHERE date = ? AND completed = 0", (today,))
            today_pending = cursor.fetchone()["today_pending"]

            cursor.execute("SELECT COUNT(*) AS upcoming FROM reminders WHERE date > ? AND completed = 0", (today,))
            upcoming = cursor.fetchone()["upcoming"]

            return {
                "total": total,
                "completed": completed,
                "today_pending": today_pending,
                "upcoming": upcoming,
            }
