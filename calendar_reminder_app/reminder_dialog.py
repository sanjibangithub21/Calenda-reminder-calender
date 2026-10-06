"""
Modal dialog for creating and editing reminders.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from theme_config import CATEGORIES, FONTS, DEFAULT_CATEGORY


class ReminderDialog(ctk.CTkToplevel):
    """Modern modal dialog for adding or editing a reminder."""

    def __init__(
        self,
        parent: ctk.CTk,
        initial_date: Optional[str] = None,
        reminder_data: Optional[Dict[str, Any]] = None,
        on_save_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        super().__init__(parent)
        self.parent = parent
        self.reminder_data = reminder_data
        self.is_edit_mode = reminder_data is not None
        self.on_save_callback = on_save_callback

        # Initial values
        now = datetime.now()
        self.default_date = initial_date or now.strftime("%Y-%m-%d")

        # Next upcoming rounded time (e.g. if 10:14, default to 11:00)
        next_hour = (now + timedelta(hours=1)).replace(minute=0)
        self.default_time = next_hour.strftime("%H:%M")

        self.title("Edit Reminder" if self.is_edit_mode else "New Reminder")
        self.geometry("480x580")
        self.minsize(440, 540)
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._center_window()
        self._build_ui()

    def _center_window(self) -> None:
        """Centers the dialog relative to parent."""
        self.update_idletasks()
        w = 480
        h = 580
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_rootx()
        py = self.parent.winfo_rooty()
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        """Builds dialog form fields and controls."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scrollable.grid(row=0, column=0, sticky="nsew", padx=20, pady=(15, 10))
        scrollable.grid_columnconfigure(0, weight=1)

        # Header Title
        title_text = "✏️ Edit Reminder" if self.is_edit_mode else "➕ Add New Reminder"
        header = ctk.CTkLabel(
            scrollable,
            text=title_text,
            font=ctk.CTkFont(family=FONTS["family"], size=18, weight="bold"),
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", pady=(0, 15))

        # Title Field
        lbl_title = ctk.CTkLabel(
            scrollable,
            text="Reminder Title *",
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
        )
        lbl_title.grid(row=1, column=0, sticky="w", pady=(5, 2))

        self.title_entry = ctk.CTkEntry(
            scrollable,
            placeholder_text="e.g., Team Sync, Dentist Appointment, Pay Utility Bill",
            height=38,
            font=ctk.CTkFont(family=FONTS["family"], size=13),
        )
        self.title_entry.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Date Field & Quick Selection
        lbl_date = ctk.CTkLabel(
            scrollable,
            text="Date (YYYY-MM-DD) *",
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
        )
        lbl_date.grid(row=3, column=0, sticky="w", pady=(5, 2))

        date_row = ctk.CTkFrame(scrollable, fg_color="transparent")
        date_row.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        date_row.grid_columnconfigure(0, weight=1)

        self.date_entry = ctk.CTkEntry(
            date_row,
            height=36,
            font=ctk.CTkFont(family=FONTS["family"], size=13),
        )
        self.date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_today = ctk.CTkButton(
            date_row,
            text="Today",
            width=65,
            height=36,
            fg_color=("gray80", "#334155"),
            hover_color=("gray70", "#475569"),
            command=self._set_today,
        )
        btn_today.grid(row=0, column=1, padx=(0, 4))

        btn_tmrw = ctk.CTkButton(
            date_row,
            text="Tomorrow",
            width=75,
            height=36,
            fg_color=("gray80", "#334155"),
            hover_color=("gray70", "#475569"),
            command=self._set_tomorrow,
        )
        btn_tmrw.grid(row=0, column=2)

        # Time Row (Hours & Minutes combo)
        lbl_time = ctk.CTkLabel(
            scrollable,
            text="Scheduled Time (24-Hour format HH:MM) *",
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
        )
        lbl_time.grid(row=5, column=0, sticky="w", pady=(5, 2))

        time_row = ctk.CTkFrame(scrollable, fg_color="transparent")
        time_row.grid(row=6, column=0, sticky="ew", pady=(0, 10))
        time_row.grid_columnconfigure((0, 1), weight=1)

        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(0, 60, 5)]

        self.hour_combo = ctk.CTkComboBox(
            time_row,
            values=hours,
            height=36,
            font=ctk.CTkFont(family=FONTS["family"], size=13),
        )
        self.hour_combo.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.min_combo = ctk.CTkComboBox(
            time_row,
            values=minutes,
            height=36,
            font=ctk.CTkFont(family=FONTS["family"], size=13),
        )
        self.min_combo.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Category Selector
        lbl_cat = ctk.CTkLabel(
            scrollable,
            text="Category / Tag",
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
        )
        lbl_cat.grid(row=7, column=0, sticky="w", pady=(5, 2))

        category_names = list(CATEGORIES.keys())
        self.category_var = ctk.StringVar(value=DEFAULT_CATEGORY)
        self.category_combo = ctk.CTkComboBox(
            scrollable,
            values=category_names,
            variable=self.category_var,
            height=36,
            font=ctk.CTkFont(family=FONTS["family"], size=13),
            command=self._update_category_color,
        )
        self.category_combo.grid(row=8, column=0, sticky="ew", pady=(0, 10))

        # Description / Notes
        lbl_desc = ctk.CTkLabel(
            scrollable,
            text="Notes / Description (Optional)",
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
        )
        lbl_desc.grid(row=9, column=0, sticky="w", pady=(5, 2))

        self.desc_text = ctk.CTkTextbox(
            scrollable,
            height=85,
            wrap="word",
            font=ctk.CTkFont(family=FONTS["family"], size=12),
        )
        self.desc_text.grid(row=10, column=0, sticky="ew", pady=(0, 12))

        # Alarm Switch
        self.alarm_var = ctk.BooleanVar(value=True)
        self.alarm_switch = ctk.CTkSwitch(
            scrollable,
            text="Enable Audio Alarm & Popup Notification",
            variable=self.alarm_var,
            font=ctk.CTkFont(family=FONTS["family"], size=12),
            progress_color="#3B82F6",
        )
        self.alarm_switch.grid(row=11, column=0, sticky="w", pady=(0, 10))

        # Validation error message
        self.error_label = ctk.CTkLabel(
            scrollable,
            text="",
            text_color="#EF4444",
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
        )
        self.error_label.grid(row=12, column=0, sticky="w", pady=(0, 10))

        # Bottom Action Bar
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        btn_bar.grid_columnconfigure((0, 1), weight=1)

        cancel_btn = ctk.CTkButton(
            btn_bar,
            text="Cancel",
            height=38,
            fg_color=("gray75", "#334155"),
            hover_color=("gray65", "#475569"),
            command=self.destroy,
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        save_btn = ctk.CTkButton(
            btn_bar,
            text="Save Reminder",
            height=38,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=ctk.CTkFont(family=FONTS["family"], size=13, weight="bold"),
            command=self._handle_save,
        )
        save_btn.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        # Populate with existing or default values
        self._populate_fields()

    def _populate_fields(self) -> None:
        """Fills fields with either existing reminder data or sensible defaults."""
        if self.is_edit_mode and self.reminder_data:
            self.title_entry.insert(0, self.reminder_data.get("title", ""))
            self.date_entry.insert(0, self.reminder_data.get("date", self.default_date))

            raw_time = self.reminder_data.get("time", self.default_time)
            parts = raw_time.split(":")
            h = parts[0] if len(parts) > 0 else "09"
            m = parts[1] if len(parts) > 1 else "00"
            self.hour_combo.set(f"{int(h):02d}")
            self.min_combo.set(f"{int(m):02d}")

            cat = self.reminder_data.get("category", DEFAULT_CATEGORY)
            self.category_combo.set(cat)

            desc = self.reminder_data.get("description", "")
            if desc:
                self.desc_text.insert("1.0", desc)

            self.alarm_var.set(bool(self.reminder_data.get("alarm_enabled", 1)))
        else:
            self.date_entry.insert(0, self.default_date)
            parts = self.default_time.split(":")
            self.hour_combo.set(parts[0])
            self.min_combo.set(parts[1])

        self.title_entry.focus_set()

    def _set_today(self) -> None:
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def _set_tomorrow(self) -> None:
        self.date_entry.delete(0, "end")
        tmrw = datetime.now() + timedelta(days=1)
        self.date_entry.insert(0, tmrw.strftime("%Y-%m-%d"))

    def _update_category_color(self, choice: str) -> None:
        pass

    def _handle_save(self) -> None:
        """Validates inputs and triggers callback."""
        title = self.title_entry.get().strip()
        date_val = self.date_entry.get().strip()
        hour_val = self.hour_combo.get().strip()
        min_val = self.min_combo.get().strip()
        category = self.category_combo.get().strip()
        desc = self.desc_text.get("1.0", "end-1c").strip()
        alarm = self.alarm_var.get()

        if not title:
            self.error_label.configure(text="⚠️ Please enter a title for the reminder.")
            self.title_entry.focus_set()
            return

        # Validate Date format
        try:
            parsed_date = datetime.strptime(date_val, "%Y-%m-%d")
            formatted_date = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            self.error_label.configure(text="⚠️ Invalid date format. Use YYYY-MM-DD (e.g. 2026-10-07).")
            self.date_entry.focus_set()
            return

        # Validate Time format
        try:
            h_int = int(hour_val)
            m_int = int(min_val)
            if not (0 <= h_int <= 23 and 0 <= m_int <= 59):
                raise ValueError()
            formatted_time = f"{h_int:02d}:{m_int:02d}"
        except ValueError:
            self.error_label.configure(text="⚠️ Invalid time. Hour must be 0-23, minute 0-59.")
            return

        payload = {
            "title": title,
            "date": formatted_date,
            "time": formatted_time,
            "category": category if category in CATEGORIES else DEFAULT_CATEGORY,
            "description": desc,
            "alarm_enabled": alarm,
        }

        if self.is_edit_mode and self.reminder_data:
            payload["id"] = self.reminder_data["id"]

        if self.on_save_callback:
            self.on_save_callback(payload)

        self.destroy()
