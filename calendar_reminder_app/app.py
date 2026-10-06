"""
Main Application Window for Calendar and Reminder App.
Integrates calendar view, reminder management, live digital clock,
statistics cards, search filters, and background notification monitor.
"""

import sys
import os
import tkinter.messagebox as mb
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from PIL import Image

import customtkinter as ctk

from database import ReminderDatabase
from calendar_view import CalendarView
from reminder_dialog import ReminderDialog
from notification_manager import NotificationManager
from theme_config import CATEGORIES, FONTS, play_chime_sound


# Set default CustomTkinter appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class CalendarReminderApp(ctk.CTk):
    """Main application window for the Calendar and Reminder app."""

    def __init__(self):
        super().__init__()

        self.title("Calenda")
        self.geometry("1160x740")
        self.minsize(980, 640)

        # Initialize database
        self.db = ReminderDatabase()

        # Seed sample data on first run if database is empty
        self._seed_sample_data_if_empty()

        # Active state
        self.selected_date_str = date.today().strftime("%Y-%m-%d")
        self.active_filter = "date"  # 'date', 'today', 'upcoming', 'all'
        self.search_query = ""

        # Notification Manager
        self.notification_mgr = NotificationManager(
            root=self,
            db=self.db,
            on_refresh_callback=self.refresh_all,
        )

        self._build_ui()
        self._start_clock()
        self.notification_mgr.start()

    def _seed_sample_data_if_empty(self) -> None:
        """Adds helpful sample reminders if the database is newly created."""
        stats = self.db.get_statistics()
        if stats["total"] == 0:
            today = date.today().strftime("%Y-%m-%d")
            self.db.add_reminder(
                title="Welcome to Calendar & Reminders!",
                date=today,
                time="09:00",
                category="General",
                description="Explore features: click any date, add reminders, and toggle completed status.",
                alarm_enabled=True,
            )
            self.db.add_reminder(
                title="Project Review Meeting",
                date=today,
                time="14:30",
                category="Work",
                description="Review upcoming sprints, deployment goals, and team roadmap.",
                alarm_enabled=True,
            )
            self.db.add_reminder(
                title="Gym & Workout Session",
                date=today,
                time="18:00",
                category="Personal",
                description="Evening workout and cardio session.",
                alarm_enabled=True,
            )

    def _build_ui(self) -> None:
        """Constructs layout: Header bar, Left (Calendar + Stats), Right (Reminders list)."""
        self.grid_columnconfigure(0, weight=0)  # Left panel fixed/flexible
        self.grid_columnconfigure(1, weight=1)  # Right panel expands
        self.grid_rowconfigure(1, weight=1)

        self._build_top_bar()
        self._build_left_panel()
        self._build_right_panel()

    def _build_top_bar(self) -> None:
        """Top application bar with title, live clock, search, theme switcher, and new reminder button."""
        top_bar = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=("gray88", "#0F172A"))
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        top_bar.grid_propagate(False)

        # App Brand & Logo
        brand_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        brand_frame.pack(side="left", padx=20, pady=12)

        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        if os.path.exists(logo_path):
            try:
                pil_logo = Image.open(logo_path)
                ctk_logo = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(34, 34))
                icon_lbl = ctk.CTkLabel(brand_frame, text="", image=ctk_logo)
                icon_lbl.pack(side="left", padx=(0, 10))
            except Exception:
                icon_lbl = ctk.CTkLabel(brand_frame, text="🔔", font=ctk.CTkFont(size=24))
                icon_lbl.pack(side="left", padx=(0, 8))
        else:
            icon_lbl = ctk.CTkLabel(brand_frame, text="🔔", font=ctk.CTkFont(size=24))
            icon_lbl.pack(side="left", padx=(0, 8))

        title_lbl = ctk.CTkLabel(
            brand_frame,
            text="Calenda",
            font=ctk.CTkFont(family=FONTS["family"], size=20, weight="bold"),
            text_color=("gray10", "#F8FAFC"),
        )
        title_lbl.pack(side="left")

        # Live Digital Clock & Date
        self.clock_lbl = ctk.CTkLabel(
            top_bar,
            text="",
            font=ctk.CTkFont(family=FONTS["family"], size=13, weight="bold"),
            text_color=("gray30", "#94A3B8"),
            fg_color=("gray80", "#1E293B"),
            corner_radius=8,
            padx=12,
            pady=4,
        )
        self.clock_lbl.pack(side="left", padx=20)

        # Right Action Buttons
        actions_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_frame.pack(side="right", padx=20, pady=12)

        # Test Alarm Button
        test_alarm_btn = ctk.CTkButton(
            actions_frame,
            text="🔔 Test Alarm",
            width=100,
            height=34,
            fg_color=("gray75", "#334155"),
            hover_color=("gray65", "#475569"),
            font=ctk.CTkFont(family=FONTS["family"], size=12),
            command=self._test_alarm,
        )
        test_alarm_btn.pack(side="left", padx=(0, 10))

        # Theme Switcher OptionMenu
        self.theme_menu = ctk.CTkOptionMenu(
            actions_frame,
            values=["Dark", "Light", "System"],
            width=90,
            height=34,
            font=ctk.CTkFont(family=FONTS["family"], size=12),
            command=self._change_theme,
        )
        self.theme_menu.set("Dark")
        self.theme_menu.pack(side="left", padx=(0, 12))

        # + New Reminder Button
        new_btn = ctk.CTkButton(
            actions_frame,
            text="＋ New Reminder",
            width=135,
            height=34,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=ctk.CTkFont(family=FONTS["family"], size=13, weight="bold"),
            command=self._open_new_reminder_dialog,
        )
        new_btn.pack(side="left")

    def _build_left_panel(self) -> None:
        """Left panel hosting calendar grid and statistics dashboard."""
        self.left_frame = ctk.CTkFrame(self, width=490, corner_radius=12, fg_color=("gray95", "#111827"))
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=16)
        self.left_frame.grid_propagate(False)

        # Calendar View Component
        self.calendar_view = CalendarView(
            parent=self.left_frame,
            on_date_selected=self._on_calendar_date_selected,
            get_month_reminders=self.db.get_reminders_for_month,
            fg_color="transparent",
        )
        self.calendar_view.pack(fill="both", expand=True, padx=6, pady=(6, 4))

        # Dashboard Summary Metrics
        self._build_stats_section()

    def _build_stats_section(self) -> None:
        """Bottom dashboard cards showing Total, Pending, Upcoming, Completed."""
        stats_frame = ctk.CTkFrame(self.left_frame, fg_color=("gray90", "#1E293B"), corner_radius=10)
        stats_frame.pack(fill="x", padx=14, pady=(4, 14))

        title_lbl = ctk.CTkLabel(
            stats_frame,
            text="📊 Summary Overview",
            font=ctk.CTkFont(family=FONTS["family"], size=13, weight="bold"),
            anchor="w",
        )
        title_lbl.pack(fill="x", padx=12, pady=(8, 6))

        cards_row = ctk.CTkFrame(stats_frame, fg_color="transparent")
        cards_row.pack(fill="x", padx=10, pady=(0, 10))
        cards_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_widgets = {}

        items = [
            ("total", "Total", "#3B82F6"),
            ("today_pending", "Today Due", "#EF4444"),
            ("upcoming", "Upcoming", "#F59E0B"),
            ("completed", "Done", "#10B981"),
        ]

        for idx, (key, label, col) in enumerate(items):
            box = ctk.CTkFrame(cards_row, fg_color=("gray85", "#0F172A"), corner_radius=8)
            box.grid(row=0, column=idx, padx=3, sticky="nsew")

            num_lbl = ctk.CTkLabel(
                box,
                text="0",
                font=ctk.CTkFont(family=FONTS["family"], size=16, weight="bold"),
                text_color=col,
            )
            num_lbl.pack(pady=(4, 0))

            txt_lbl = ctk.CTkLabel(
                box,
                text=label,
                font=ctk.CTkFont(family=FONTS["family"], size=10),
                text_color=("gray40", "gray70"),
            )
            txt_lbl.pack(pady=(0, 4))

            self.stat_widgets[key] = num_lbl

        self._refresh_stats()

    def _build_right_panel(self) -> None:
        """Right panel containing filters, search bar, and reminders cards list."""
        self.right_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray95", "#111827"))
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=16)

        # Header for reminders panel
        header_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(14, 8))

        self.list_title_lbl = ctk.CTkLabel(
            header_row,
            text="",
            font=ctk.CTkFont(family=FONTS["family"], size=18, weight="bold"),
            anchor="w",
        )
        self.list_title_lbl.pack(side="left", fill="x", expand=True)

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            header_row,
            placeholder_text="🔍 Search reminders...",
            width=200,
            height=32,
            font=ctk.CTkFont(family=FONTS["family"], size=12),
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", self._on_search_input)

        # Filter Segmented Tabs
        filters_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        filters_row.pack(fill="x", padx=16, pady=(0, 10))

        self.filter_buttons = {}
        filters = [
            ("date", "📅 Selected Date"),
            ("today", "⭐ Today"),
            ("upcoming", "🚀 Upcoming"),
            ("all", "📋 All Reminders"),
        ]

        for key, title in filters:
            btn = ctk.CTkButton(
                filters_row,
                text=title,
                height=30,
                corner_radius=8,
                fg_color="#3B82F6" if key == self.active_filter else ("gray85", "#1E293B"),
                hover_color=("gray75", "#334155"),
                text_color="white" if key == self.active_filter else ("gray20", "#94A3B8"),
                font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold" if key == self.active_filter else "normal"),
                command=lambda k=key: self._set_filter(k),
            )
            btn.pack(side="left", padx=(0, 8))
            self.filter_buttons[key] = btn

        # Scrollable container for reminders cards
        self.reminders_scroll = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        self.reminders_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        self._refresh_reminders_list()

    def _start_clock(self) -> None:
        """Updates the digital clock every second."""
        now = datetime.now()
        clock_str = now.strftime("%A, %b %d, %Y  •  %I:%M:%S %p")
        self.clock_lbl.configure(text=clock_str)
        self.after(1000, self._start_clock)

    def _on_calendar_date_selected(self, date_str: str) -> None:
        """Handles date selection on the calendar."""
        self.selected_date_str = date_str
        self._set_filter("date")

    def _set_filter(self, filter_key: str) -> None:
        """Switches active filter."""
        self.active_filter = filter_key
        # Update tab button styles
        for key, btn in self.filter_buttons.items():
            if key == filter_key:
                btn.configure(fg_color="#3B82F6", text_color="white")
            else:
                btn.configure(fg_color=("gray85", "#1E293B"), text_color=("gray20", "#94A3B8"))

        self._refresh_reminders_list()

    def _on_search_input(self, event=None) -> None:
        """Live filters reminders as user types."""
        self.search_query = self.search_entry.get().strip()
        self._refresh_reminders_list()

    def _refresh_stats(self) -> None:
        """Fetches stats from database and updates header cards."""
        stats = self.db.get_statistics()
        for key, widget in self.stat_widgets.items():
            widget.configure(text=str(stats.get(key, 0)))

    def _refresh_reminders_list(self) -> None:
        """Renders list of reminder cards based on current filter or search query."""
        # Clear existing list items
        for widget in self.reminders_scroll.winfo_children():
            widget.destroy()

        # Determine items to display
        if self.search_query:
            reminders = self.db.search_reminders(self.search_query)
            self.list_title_lbl.configure(text=f"Search Results: '{self.search_query}' ({len(reminders)})")
        elif self.active_filter == "date":
            reminders = self.db.get_reminders_by_date(self.selected_date_str)
            try:
                dt = datetime.strptime(self.selected_date_str, "%Y-%m-%d")
                friendly = dt.strftime("%A, %B %d, %Y")
            except Exception:
                friendly = self.selected_date_str
            self.list_title_lbl.configure(text=f"Reminders for {friendly}")
        elif self.active_filter == "today":
            today_str = date.today().strftime("%Y-%m-%d")
            reminders = self.db.get_reminders_by_date(today_str)
            self.list_title_lbl.configure(text=f"Today's Reminders ({len(reminders)})")
        elif self.active_filter == "upcoming":
            reminders = self.db.get_upcoming_reminders()
            self.list_title_lbl.configure(text=f"Upcoming Reminders ({len(reminders)})")
        else:  # all
            reminders = self.db.get_all_reminders()
            self.list_title_lbl.configure(text=f"All Reminders ({len(reminders)})")

        if not reminders:
            self._render_empty_state()
            return

        for rem in reminders:
            self._render_reminder_card(rem)

    def _render_empty_state(self) -> None:
        """Displays a clean empty-state placeholder when no reminders match."""
        empty_box = ctk.CTkFrame(self.reminders_scroll, fg_color="transparent")
        empty_box.pack(fill="both", expand=True, pady=60)

        icon_lbl = ctk.CTkLabel(
            empty_box,
            text="📅✨",
            font=ctk.CTkFont(size=42),
        )
        icon_lbl.pack(pady=(0, 10))

        msg_lbl = ctk.CTkLabel(
            empty_box,
            text="No reminders found",
            font=ctk.CTkFont(family=FONTS["family"], size=16, weight="bold"),
            text_color=("gray30", "gray80"),
        )
        msg_lbl.pack(pady=(0, 6))

        sub_lbl = ctk.CTkLabel(
            empty_box,
            text="Click '+ New Reminder' above to schedule an event or task.",
            font=ctk.CTkFont(family=FONTS["family"], size=13),
            text_color=("gray50", "gray60"),
        )
        sub_lbl.pack(pady=(0, 16))

        add_btn = ctk.CTkButton(
            empty_box,
            text="＋ Add Reminder for this Date",
            height=34,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
            command=self._open_new_reminder_dialog,
        )
        add_btn.pack()

    def _render_reminder_card(self, reminder: Dict[str, Any]) -> None:
        """Renders an individual card widget for a reminder."""
        is_completed = bool(reminder.get("completed", 0))
        cat_name = reminder.get("category", "General")
        cat_info = CATEGORIES.get(cat_name, CATEGORIES["General"])

        card_bg = ("gray90", "#1E293B") if not is_completed else ("gray85", "#161E2E")
        border_col = ("gray80", "#334155") if not is_completed else ("gray75", "#273549")

        card = ctk.CTkFrame(
            self.reminders_scroll,
            fg_color=card_bg,
            border_width=1,
            border_color=border_col,
            corner_radius=10,
        )
        card.pack(fill="x", pady=5)

        # Layout: Checkbox | Content (Category chip, time, title, notes) | Action buttons
        card.grid_columnconfigure(1, weight=1)

        # Completion Checkbox
        chk_var = ctk.BooleanVar(value=is_completed)
        chk = ctk.CTkCheckBox(
            card,
            text="",
            width=24,
            checkbox_width=22,
            checkbox_height=22,
            corner_radius=6,
            variable=chk_var,
            border_color=("gray60", "#475569"),
            fg_color="#10B981",
            hover_color="#059669",
            command=lambda r_id=reminder["id"]: self._toggle_completed(r_id),
        )
        chk.grid(row=0, column=0, rowspan=2, padx=(14, 8), pady=12, sticky="n")

        # Content Box
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=0, column=1, rowspan=2, sticky="nsew", pady=10)

        # Meta chips row: Category tag + Date + Time
        chips_row = ctk.CTkFrame(content, fg_color="transparent")
        chips_row.pack(fill="x", anchor="w")

        # Category Badge
        cat_badge = ctk.CTkLabel(
            chips_row,
            text=f"{cat_info['icon']} {cat_name}",
            font=ctk.CTkFont(family=FONTS["family"], size=11, weight="bold"),
            fg_color=cat_info["color"],
            text_color="white",
            corner_radius=6,
            padx=8,
            pady=1,
        )
        cat_badge.pack(side="left", padx=(0, 6))

        # Time Chip
        time_text = f"⏰ {reminder.get('time', '')}"
        time_lbl = ctk.CTkLabel(
            chips_row,
            text=time_text,
            font=ctk.CTkFont(family=FONTS["family"], size=11, weight="bold"),
            text_color=("gray30", "#CBD5E1"),
            fg_color=("gray80", "#334155"),
            corner_radius=6,
            padx=8,
            pady=1,
        )
        time_lbl.pack(side="left", padx=(0, 6))

        # Date Chip (useful when in Upcoming/All filter)
        if self.active_filter in ("upcoming", "all") or self.search_query:
            date_lbl = ctk.CTkLabel(
                chips_row,
                text=f"📅 {reminder.get('date', '')}",
                font=ctk.CTkFont(family=FONTS["family"], size=11),
                text_color=("gray40", "gray70"),
            )
            date_lbl.pack(side="left", padx=(0, 6))

        # Alarm indicator
        if reminder.get("alarm_enabled", 1):
            alarm_tag = ctk.CTkLabel(
                chips_row,
                text="🔔 Alert ON",
                font=ctk.CTkFont(family=FONTS["family"], size=10),
                text_color=("#2563EB", "#60A5FA"),
            )
            alarm_tag.pack(side="left")

        # Title
        title_font = ctk.CTkFont(family=FONTS["family"], size=14, weight="bold")
        title_color = ("gray40", "gray50") if is_completed else ("gray10", "#F8FAFC")
        title_text = reminder.get("title", "")
        if is_completed:
            title_text = f"✓ {title_text}"

        title_lbl = ctk.CTkLabel(
            content,
            text=title_text,
            font=title_font,
            text_color=title_color,
            anchor="w",
            wraplength=420,
            justify="left",
        )
        title_lbl.pack(fill="x", pady=(4, 2), anchor="w")

        # Description / Notes (if any)
        desc = reminder.get("description", "").strip()
        if desc:
            desc_color = ("gray50", "gray60") if is_completed else ("gray30", "#94A3B8")
            desc_lbl = ctk.CTkLabel(
                content,
                text=desc,
                font=ctk.CTkFont(family=FONTS["family"], size=11),
                text_color=desc_color,
                anchor="w",
                wraplength=420,
                justify="left",
            )
            desc_lbl.pack(fill="x", anchor="w")

        # Action Buttons on Right
        actions_box = ctk.CTkFrame(card, fg_color="transparent")
        actions_box.grid(row=0, column=2, padx=(8, 14), pady=12, sticky="e")

        edit_btn = ctk.CTkButton(
            actions_box,
            text="✏️",
            width=32,
            height=30,
            corner_radius=6,
            fg_color=("gray80", "#334155"),
            hover_color=("gray70", "#475569"),
            font=ctk.CTkFont(family=FONTS["family"], size=12),
            command=lambda r=reminder: self._open_edit_reminder_dialog(r),
        )
        edit_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            actions_box,
            text="🗑️",
            width=32,
            height=30,
            corner_radius=6,
            fg_color=("gray80", "#334155"),
            hover_color=("#FEE2E2", "#7F1D1D"),
            text_color=("gray10", "#EF4444"),
            font=ctk.CTkFont(family=FONTS["family"], size=12),
            command=lambda r_id=reminder["id"]: self._delete_reminder(r_id),
        )
        del_btn.pack(side="left", padx=2)

    def _open_new_reminder_dialog(self) -> None:
        """Opens modal dialog to create a new reminder."""
        ReminderDialog(
            parent=self,
            initial_date=self.selected_date_str,
            on_save_callback=self._handle_add_reminder,
        )

    def _open_edit_reminder_dialog(self, reminder: Dict[str, Any]) -> None:
        """Opens modal dialog to edit an existing reminder."""
        ReminderDialog(
            parent=self,
            reminder_data=reminder,
            on_save_callback=self._handle_update_reminder,
        )

    def _handle_add_reminder(self, data: Dict[str, Any]) -> None:
        """Saves new reminder into database and refreshes view."""
        self.db.add_reminder(
            title=data["title"],
            date=data["date"],
            time=data["time"],
            category=data["category"],
            description=data["description"],
            alarm_enabled=data["alarm_enabled"],
        )
        self.selected_date_str = data["date"]
        self.refresh_all()

    def _handle_update_reminder(self, data: Dict[str, Any]) -> None:
        """Updates reminder in database and refreshes view."""
        self.db.update_reminder(
            reminder_id=data["id"],
            title=data["title"],
            date=data["date"],
            time=data["time"],
            category=data["category"],
            description=data["description"],
            alarm_enabled=data["alarm_enabled"],
        )
        self.refresh_all()

    def _delete_reminder(self, reminder_id: int) -> None:
        """Prompts confirmation and deletes reminder."""
        if mb.askyesno("Delete Reminder", "Are you sure you want to delete this reminder?", parent=self):
            self.db.delete_reminder(reminder_id)
            self.refresh_all()

    def _toggle_completed(self, reminder_id: int) -> None:
        """Toggles completion status for a reminder."""
        self.db.toggle_completed(reminder_id)
        self.refresh_all()

    def _change_theme(self, mode: str) -> None:
        """Switches between Dark, Light, and System themes."""
        ctk.set_appearance_mode(mode)

    def _test_alarm(self) -> None:
        """Fires an instant test alert to preview the sound chime and popup window."""
        sample_reminder = {
            "id": -99,
            "title": "Test Reminder Alert",
            "date": date.today().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "category": "Urgent",
            "description": "This is a test notification verifying that audio chimes and popup alerts work properly!",
        }
        self.notification_mgr.trigger_alert(sample_reminder)

    def refresh_all(self) -> None:
        """Refreshes all components: calendar indicators, list, and metrics."""
        self.calendar_view.refresh()
        self._refresh_stats()
        self._refresh_reminders_list()

    def destroy(self) -> None:
        """Cleanup on application close."""
        self.notification_mgr.stop()
        super().destroy()
