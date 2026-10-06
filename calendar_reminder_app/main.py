"""
Calendar and Reminder App
Main Entry Point
"""

import sys
import os

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import CalendarReminderApp


def main():
    """Starts the Calendar and Reminder desktop application."""
    app = CalendarReminderApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
