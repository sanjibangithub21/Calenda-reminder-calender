"""
Theme and style configuration for Calendar and Reminder App.
Provides consistent color palettes, typography, categories, and sound alerts.
"""

import sys
import threading

# Category Metadata: Color codes, icons, and descriptions
CATEGORIES = {
    "Work": {
        "color": "#E83848",         # Logo calendar coral red
        "badge_bg": "#7F1D1D",
        "badge_text": "#FCA5A5",
        "icon": "💼",
    },
    "Personal": {
        "color": "#10B981",         # Emerald green
        "badge_bg": "#064E3B",
        "badge_text": "#6EE7B7",
        "icon": "🏠",
    },
    "Meeting": {
        "color": "#8B5CF6",         # Violet
        "badge_bg": "#4C1D95",
        "badge_text": "#C4B5FD",
        "icon": "👥",
    },
    "Urgent": {
        "color": "#EF4444",         # Red
        "badge_bg": "#7F1D1D",
        "badge_text": "#FCA5A5",
        "icon": "🚨",
    },
    "General": {
        "color": "#F59E0B",         # Amber
        "badge_bg": "#78350F",
        "badge_text": "#FDE68A",
        "icon": "📌",
    },
}

DEFAULT_CATEGORY = "General"

FONTS = {
    "family": "Segoe UI" if sys.platform == "win32" else "Helvetica",
    "title_size": 22,
    "header_size": 16,
    "body_size": 13,
    "caption_size": 11,
}


def play_chime_sound() -> None:
    """Plays a pleasant melodic reminder chime asynchronously."""
    def _play():
        try:
            if sys.platform == "win32":
                import winsound
                # Harmonious double chime
                winsound.Beep(784, 120)  # G5
                winsound.Beep(1046, 220) # C6
            else:
                # Fallback terminal bell or silence
                sys.stdout.write("\a")
                sys.stdout.flush()
        except Exception:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

    threading.Thread(target=_play, daemon=True).start()
