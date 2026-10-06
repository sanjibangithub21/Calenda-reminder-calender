"""
Notification and Alarm Engine for Calendar and Reminder App.
Monitors due reminders, triggers audio chimes, and presents pop-up alerts.
"""

from typing import Callable, Optional, Dict, Any, List
from database import ReminderDatabase
from alert_window import ReminderAlertWindow


class NotificationManager:
    """Manages periodic checks for due reminders and fires notifications."""

    CHECK_INTERVAL_MS = 3000  # Check every 3 seconds

    def __init__(
        self,
        root: Any,
        db: ReminderDatabase,
        on_refresh_callback: Optional[Callable[[], None]] = None,
    ):
        self.root = root
        self.db = db
        self.on_refresh_callback = on_refresh_callback
        self.is_running = False
        self._timer_id: Optional[str] = None
        self.active_alert_windows: Dict[int, ReminderAlertWindow] = {}

    def start(self) -> None:
        """Starts the periodic reminder evaluation loop."""
        if not self.is_running:
            self.is_running = True
            self._schedule_check()

    def stop(self) -> None:
        """Stops the reminder evaluation loop."""
        self.is_running = False
        if self._timer_id:
            try:
                self.root.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

    def _schedule_check(self) -> None:
        """Schedules the next check iteration."""
        if not self.is_running:
            return
        self._timer_id = self.root.after(self.CHECK_INTERVAL_MS, self._check_due_reminders)

    def _check_due_reminders(self) -> None:
        """Checks the database for any due reminders and triggers alerts."""
        if not self.is_running:
            return

        try:
            due_reminders: List[Dict[str, Any]] = self.db.get_due_reminders()
            for reminder in due_reminders:
                rem_id = reminder["id"]
                # Prevent multiple popups for the same reminder if one is already open
                if rem_id in self.active_alert_windows and self.active_alert_windows[rem_id].winfo_exists():
                    continue

                # Mark as notified immediately in DB
                self.db.mark_notified(rem_id)

                # Show popup alert
                self.trigger_alert(reminder)

                # Refresh UI lists if changed
                if self.on_refresh_callback:
                    self.on_refresh_callback()
        except Exception as e:
            print(f"[NotificationManager] Error checking reminders: {e}")
        finally:
            self._schedule_check()

    def trigger_alert(self, reminder: Dict[str, Any]) -> None:
        """Spawns an alert popup window for the given reminder."""
        rem_id = reminder["id"]

        def handle_dismiss(rid: int):
            if rid in self.active_alert_windows:
                del self.active_alert_windows[rid]
            if self.on_refresh_callback:
                self.on_refresh_callback()

        def handle_snooze(rid: int, minutes: int):
            self.db.snooze_reminder(rid, minutes)
            if rid in self.active_alert_windows:
                del self.active_alert_windows[rid]
            if self.on_refresh_callback:
                self.on_refresh_callback()

        def handle_complete(rid: int):
            self.db.toggle_completed(rid)
            if rid in self.active_alert_windows:
                del self.active_alert_windows[rid]
            if self.on_refresh_callback:
                self.on_refresh_callback()

        alert = ReminderAlertWindow(
            parent=self.root,
            reminder=reminder,
            on_dismiss=handle_dismiss,
            on_snooze=handle_snooze,
            on_complete=handle_complete,
        )
        self.active_alert_windows[rem_id] = alert
