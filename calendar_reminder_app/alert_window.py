"""
Alert popup window module for Calendar and Reminder App.
Displays a top-level alert with audio notification when a reminder is triggered.
"""

import customtkinter as ctk
from typing import Dict, Any, Callable, Optional
from theme_config import CATEGORIES, FONTS, play_chime_sound


class ReminderAlertWindow(ctk.CTkToplevel):
    """Modern popup alert for active reminders with audio chime and snooze options."""

    def __init__(
        self,
        parent: ctk.CTk,
        reminder: Dict[str, Any],
        on_dismiss: Optional[Callable[[int], None]] = None,
        on_snooze: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[int], None]] = None,
    ):
        super().__init__(parent)
        self.reminder = reminder
        self.on_dismiss = on_dismiss
        self.on_snooze = on_snooze
        self.on_complete = on_complete

        self.title("🔔 Reminder Notification")
        self.geometry("460x360")
        self.minsize(420, 320)
        self.resizable(False, False)

        # Ensure window stays on top and grabs focus
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()

        self._center_window()
        self._build_ui()

        # Play chime
        play_chime_sound()

    def _center_window(self) -> None:
        """Centers the alert window on the screen."""
        self.update_idletasks()
        width = 460
        height = 360
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2) - 50
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        """Constructs the alert window UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        cat_name = self.reminder.get("category", "General")
        cat_info = CATEGORIES.get(cat_name, CATEGORIES["General"])

        # Header card
        header_frame = ctk.CTkFrame(self, fg_color=("gray85", "#1E293B"), corner_radius=0, height=75)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)

        bell_label = ctk.CTkLabel(
            header_frame,
            text="🔔 REMINDER ALERT",
            font=ctk.CTkFont(family=FONTS["family"], size=16, weight="bold"),
            text_color=cat_info["color"],
        )
        bell_label.pack(side="left", padx=20, pady=20)

        time_badge = ctk.CTkLabel(
            header_frame,
            text=f"⏰ {self.reminder.get('time', '--:--')}",
            font=ctk.CTkFont(family=FONTS["family"], size=14, weight="bold"),
            fg_color=("gray75", "#334155"),
            corner_radius=8,
            padx=12,
            pady=4,
        )
        time_badge.pack(side="right", padx=20, pady=20)

        # Content card
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=16)

        # Category and Date chip
        chips_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        chips_frame.pack(fill="x", anchor="w", pady=(0, 8))

        cat_badge = ctk.CTkLabel(
            chips_frame,
            text=f"{cat_info['icon']} {cat_name}",
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
            fg_color=cat_info["color"],
            text_color="white",
            corner_radius=6,
            padx=10,
            pady=2,
        )
        cat_badge.pack(side="left")

        date_lbl = ctk.CTkLabel(
            chips_frame,
            text=f"📅 {self.reminder.get('date', '')}",
            font=ctk.CTkFont(family=FONTS["family"], size=12),
            text_color=("gray40", "gray70"),
        )
        date_lbl.pack(side="left", padx=(10, 0))

        # Title
        title_lbl = ctk.CTkLabel(
            content_frame,
            text=self.reminder.get("title", "Untitled Reminder"),
            font=ctk.CTkFont(family=FONTS["family"], size=18, weight="bold"),
            anchor="w",
            wraplength=410,
            justify="left",
        )
        title_lbl.pack(fill="x", pady=(4, 8), anchor="w")

        # Description / notes
        desc = self.reminder.get("description", "").strip()
        if desc:
            desc_textbox = ctk.CTkTextbox(
                content_frame,
                height=70,
                wrap="word",
                font=ctk.CTkFont(family=FONTS["family"], size=12),
                fg_color=("gray90", "#0F172A"),
                border_width=1,
                border_color=("gray80", "#334155"),
            )
            desc_textbox.insert("1.0", desc)
            desc_textbox.configure(state="disabled")
            desc_textbox.pack(fill="both", expand=True, pady=(0, 10))
        else:
            spacer = ctk.CTkLabel(content_frame, text="", height=40)
            spacer.pack(fill="x")

        # Action Buttons footer
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 18))
        btn_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        dismiss_btn = ctk.CTkButton(
            btn_frame,
            text="Dismiss",
            fg_color=("gray70", "#334155"),
            hover_color=("gray60", "#475569"),
            font=ctk.CTkFont(family=FONTS["family"], size=12),
            command=self._handle_dismiss,
        )
        dismiss_btn.grid(row=0, column=0, padx=4, sticky="ew")

        snooze5_btn = ctk.CTkButton(
            btn_frame,
            text="Snooze 5m",
            fg_color=("gray80", "#1E293B"),
            hover_color=("gray70", "#334155"),
            text_color=("gray10", "#E2E8F0"),
            border_width=1,
            border_color=("gray60", "#475569"),
            font=ctk.CTkFont(family=FONTS["family"], size=12),
            command=lambda: self._handle_snooze(5),
        )
        snooze5_btn.grid(row=0, column=1, padx=4, sticky="ew")

        snooze15_btn = ctk.CTkButton(
            btn_frame,
            text="Snooze 15m",
            fg_color=("gray80", "#1E293B"),
            hover_color=("gray70", "#334155"),
            text_color=("gray10", "#E2E8F0"),
            border_width=1,
            border_color=("gray60", "#475569"),
            font=ctk.CTkFont(family=FONTS["family"], size=12),
            command=lambda: self._handle_snooze(15),
        )
        snooze15_btn.grid(row=0, column=2, padx=4, sticky="ew")

        done_btn = ctk.CTkButton(
            btn_frame,
            text="✓ Mark Done",
            fg_color="#10B981",
            hover_color="#059669",
            text_color="white",
            font=ctk.CTkFont(family=FONTS["family"], size=12, weight="bold"),
            command=self._handle_complete,
        )
        done_btn.grid(row=0, column=3, padx=4, sticky="ew")

    def _handle_dismiss(self) -> None:
        if self.on_dismiss:
            self.on_dismiss(self.reminder["id"])
        self.destroy()

    def _handle_snooze(self, minutes: int) -> None:
        if self.on_snooze:
            self.on_snooze(self.reminder["id"], minutes)
        self.destroy()

    def _handle_complete(self) -> None:
        if self.on_complete:
            self.on_complete(self.reminder["id"])
        self.destroy()
