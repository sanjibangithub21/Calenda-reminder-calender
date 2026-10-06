"""
Monthly Calendar View Component for Calendar and Reminder App.
Renders an interactive monthly grid with day navigation, reminders badges, and date selection.
"""

import calendar
import customtkinter as ctk
from datetime import datetime, date
from typing import Dict, List, Any, Callable, Optional
from theme_config import FONTS, CATEGORIES


class CalendarView(ctk.CTkFrame):
    """Interactive monthly calendar view with reminder indicators and navigation."""

    WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(
        self,
        parent: Any,
        on_date_selected: Optional[Callable[[str], None]] = None,
        get_month_reminders: Optional[Callable[[int, int], Dict[str, List[Dict[str, Any]]]]] = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.on_date_selected = on_date_selected
        self.get_month_reminders = get_month_reminders

        today = datetime.now()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_date_str = today.strftime("%Y-%m-%d")

        self.day_buttons: Dict[int, ctk.CTkFrame] = {}

        self._build_header()
        self._build_weekday_headers()
        self._build_grid_container()
        self.render_calendar()

    def _build_header(self) -> None:
        """Top navigation bar: Prev Month, Month & Year label, Next Month, Today button."""
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=16, pady=(14, 10))

        # Previous month button
        self.prev_btn = ctk.CTkButton(
            self.header_frame,
            text="◀",
            width=36,
            height=34,
            corner_radius=8,
            fg_color=("gray85", "#1E293B"),
            hover_color=("gray75", "#334155"),
            text_color=("gray10", "#F8FAFC"),
            font=ctk.CTkFont(family=FONTS["family"], size=13),
            command=self.prev_month,
        )
        self.prev_btn.pack(side="left", padx=(0, 6))

        # Next month button
        self.next_btn = ctk.CTkButton(
            self.header_frame,
            text="▶",
            width=36,
            height=34,
            corner_radius=8,
            fg_color=("gray85", "#1E293B"),
            hover_color=("gray75", "#334155"),
            text_color=("gray10", "#F8FAFC"),
            font=ctk.CTkFont(family=FONTS["family"], size=13),
            command=self.next_month,
        )
        self.next_btn.pack(side="left", padx=(0, 12))

        # Month and Year Label
        self.month_label = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=ctk.CTkFont(family=FONTS["family"], size=18, weight="bold"),
            anchor="w",
        )
        self.month_label.pack(side="left", expand=True, fill="x")

        # Today Quick Button
        self.today_btn = ctk.CTkButton(
            self.header_frame,
            text="Today",
            width=65,
            height=34,
            corner_radius=8,
            fg_color=("gray80", "#334155"),
            hover_color=("gray70", "#475569"),
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
            command=self.go_to_today,
        )
        self.today_btn.pack(side="right")

    def _build_weekday_headers(self) -> None:
        """Renders weekday names: Mon, Tue, Wed, Thu, Fri, Sat, Sun."""
        self.weekday_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.weekday_frame.pack(fill="x", padx=16, pady=(4, 6))

        for col, day_name in enumerate(self.WEEKDAYS):
            self.weekday_frame.grid_columnconfigure(col, weight=1, uniform="weekdays")
            is_weekend = col in (5, 6)
            text_color = ("#EF4444", "#F87171") if is_weekend else ("gray40", "gray70")
            lbl = ctk.CTkLabel(
                self.weekday_frame,
                text=day_name,
                font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
                text_color=text_color,
            )
            lbl.grid(row=0, column=col, sticky="nsew", pady=2)

    def _build_grid_container(self) -> None:
        """Frame hosting the 7x6 date grid."""
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        for col in range(7):
            self.grid_frame.grid_columnconfigure(col, weight=1, uniform="days")

    def render_calendar(self) -> None:
        """Re-draws all day cells for current month and year."""
        # Clear existing grid cells
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.day_buttons.clear()

        # Update Month Label
        month_name = calendar.month_name[self.current_month]
        self.month_label.configure(text=f"{month_name} {self.current_year}")

        # Fetch month's reminders from database
        reminders_by_date = {}
        if self.get_month_reminders:
            reminders_by_date = self.get_month_reminders(self.current_year, self.current_month)

        # Generate weeks matrix
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        today_date = date.today()

        for row_idx, week in enumerate(cal):
            self.grid_frame.grid_rowconfigure(row_idx, weight=1)
            for col_idx, day_num in enumerate(week):
                if day_num == 0:
                    # Empty filler cell
                    spacer = ctk.CTkFrame(
                        self.grid_frame,
                        fg_color="transparent",
                        corner_radius=8,
                    )
                    spacer.grid(row=row_idx, column=col_idx, padx=3, pady=3, sticky="nsew")
                    continue

                date_str = f"{self.current_year:04d}-{self.current_month:02d}-{day_num:02d}"
                is_today = (
                    self.current_year == today_date.year
                    and self.current_month == today_date.month
                    and day_num == today_date.day
                )
                is_selected = (date_str == self.selected_date_str)
                reminders_on_day = reminders_by_date.get(date_str, [])
                reminder_count = len(reminders_on_day)

                cell = self._create_day_cell(
                    parent=self.grid_frame,
                    day_num=day_num,
                    date_str=date_str,
                    is_today=is_today,
                    is_selected=is_selected,
                    reminders=reminders_on_day,
                )
                cell.grid(row=row_idx, column=col_idx, padx=3, pady=3, sticky="nsew")
                self.day_buttons[day_num] = cell

    def _create_day_cell(
        self,
        parent: Any,
        day_num: int,
        date_str: str,
        is_today: bool,
        is_selected: bool,
        reminders: List[Dict[str, Any]],
    ) -> ctk.CTkFrame:
        """Creates a modern interactive cell representing a single day."""
        # Dynamic styling based on status
        border_width = 2 if (is_selected or is_today) else 1
        if is_selected:
            fg_color = ("#DBEAFE", "#1E3A8A")  # Soft blue highlight
            border_color = "#3B82F6"
        elif is_today:
            fg_color = ("#FEF3C7", "#3B2A05")  # Soft amber highlight
            border_color = "#F59E0B"
        else:
            fg_color = ("gray92", "#1E293B")
            border_color = ("gray80", "#334155")

        cell = ctk.CTkFrame(
            parent,
            fg_color=fg_color,
            border_width=border_width,
            border_color=border_color,
            corner_radius=10,
            cursor="hand2",
        )

        # Day Number Header
        header_sub = ctk.CTkFrame(cell, fg_color="transparent")
        header_sub.pack(fill="x", padx=6, pady=(4, 2))

        num_color = "#2563EB" if is_selected else ("#D97706" if is_today else ("gray15", "gray90"))
        day_lbl = ctk.CTkLabel(
            header_sub,
            text=str(day_num),
            font=ctk.CTkFont(family=FONTS["family"], size=13, weight="bold" if (is_today or is_selected) else "normal"),
            text_color=num_color,
        )
        day_lbl.pack(side="left")

        # Today marker tag
        if is_today:
            today_badge = ctk.CTkLabel(
                header_sub,
                text="TODAY",
                font=ctk.CTkFont(family=FONTS["family"], size=9, weight="bold"),
                text_color="#F59E0B",
            )
            today_badge.pack(side="right")

        # Reminder badge / dot indicators
        badge_frame = ctk.CTkFrame(cell, fg_color="transparent")
        badge_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        count = len(reminders)
        if count > 0:
            # Check uncompleted count
            pending_count = sum(1 for r in reminders if not r.get("completed", 0))

            badge_text = f"● {count} event{'s' if count > 1 else ''}"
            badge_color = "#EF4444" if pending_count > 0 else "#10B981"
            badge_bg = ("#FEE2E2", "#450A0A") if pending_count > 0 else ("#D1FAE5", "#064E3B")

            badge_lbl = ctk.CTkLabel(
                badge_frame,
                text=badge_text,
                font=ctk.CTkFont(family=FONTS["family"], size=10, weight="bold"),
                text_color=badge_color,
                fg_color=badge_bg,
                corner_radius=6,
                height=18,
                padx=6,
            )
            badge_lbl.pack(anchor="center", pady=(4, 0))

            # Bind clicks to inner elements too
            badge_lbl.bind("<Button-1>", lambda e, d=date_str: self.select_date(d))

        # Bind click handlers to cell and inner labels
        cell.bind("<Button-1>", lambda e, d=date_str: self.select_date(d))
        day_lbl.bind("<Button-1>", lambda e, d=date_str: self.select_date(d))
        header_sub.bind("<Button-1>", lambda e, d=date_str: self.select_date(d))
        badge_frame.bind("<Button-1>", lambda e, d=date_str: self.select_date(d))

        return cell

    def select_date(self, date_str: str) -> None:
        """Selects a date and notifies listeners."""
        self.selected_date_str = date_str
        self.render_calendar()
        if self.on_date_selected:
            self.on_date_selected(date_str)

    def prev_month(self) -> None:
        """Navigates to previous month."""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.render_calendar()

    def next_month(self) -> None:
        """Navigates to next month."""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.render_calendar()

    def go_to_today(self) -> None:
        """Jumps directly to today's date and selects it."""
        today = date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.select_date(today.strftime("%Y-%m-%d"))

    def refresh(self) -> None:
        """Refreshes the calendar display."""
        self.render_calendar()
