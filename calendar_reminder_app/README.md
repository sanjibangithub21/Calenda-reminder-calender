# 🗓️ Calenda – Modern Calendar & Reminder Studio

A modern, feature-rich calendar and reminder application built with **Python**. Includes both an ultra-sleek **Web Application** running locally in your browser and a native **CustomTkinter Desktop GUI**. Designed with curated dark/light themes, interactive monthly calendar grid, category tagging, Web Audio alarm chimes, and automatic pop-up alerts.

---

## ✨ Features

- **Interactive Monthly Calendar Grid**:
  - Full monthly view with day-of-week headers (Mon–Sun).
  - Highlighted **Current Day** and **Selected Date**.
  - **Dynamic Reminder Indicators**: Dates with scheduled reminders display badges (`● N events`).
  - Quick month-to-month navigation (`◀`, `▶`) and a one-click **"Today"** jump button.

- **Comprehensive Reminder Management**:
  - Create reminders with Title, Date (YYYY-MM-DD), Time (24h picker), Category, and Notes.
  - Pre-fills with selected calendar date or quick buttons (*Today*, *Tomorrow*).
  - Edit or delete reminders at any time.
  - Interactive **Checkboxes** to mark items completed (with strikethrough styling).

- **Categorization & Color-Coding**:
  - 💼 **Work** (`#3B82F6` Blue)
  - 🏠 **Personal** (`#10B981` Emerald)
  - 👥 **Meeting** (`#8B5CF6` Violet)
  - 🚨 **Urgent** (`#EF4444` Red)
  - 📌 **General** (`#F59E0B` Amber)

- **Audible Chimes & Pop-up Notifications**:
  - Periodic background engine monitors upcoming reminders.
  - When a reminder is due, it plays a melodic two-tone chime and pops up an **Alert Window** on top of all windows.
  - Quick action controls on alerts:
    - **✓ Mark Done**: Instantly marks the reminder completed.
    - **⏰ Snooze 5m / 15m**: Pushes the alarm forward.
    - **✕ Dismiss**: Acknowledges and dismisses the alert.
  - **"🔔 Test Alarm"** button on the toolbar lets you test sound & popup alerts anytime.

- **Dashboard Metrics & Search**:
  - Real-time statistics counters: *Total*, *Today Due*, *Upcoming*, and *Done*.
  - Live digital clock and date in the top bar.
  - Instant search bar to filter reminders by title, notes, or category keyword.
  - Quick filters: *Selected Date*, *Today*, *Upcoming*, and *All Reminders*.

- **Persistent Storage**:
  - Backed by local SQLite database (`reminders.db`) with indexes for high performance and zero external database setup.

- **Theme Switching**:
  - Seamless toggle between **Dark**, **Light**, and **System** themes.

---

## 📁 Project Structure

```
calendar_reminder_app/
├── main.py                  # Entry point for running the application
├── app.py                   # Main window orchestrating layout and state
├── calendar_view.py         # CustomTkinter interactive monthly calendar grid
├── reminder_dialog.py       # Add/Edit reminder modal dialog
├── alert_window.py          # Pop-up alert window with snooze & sound chime
├── notification_manager.py  # Background reminder checker & alarm scheduler
├── database.py              # SQLite persistence layer and CRUD queries
├── theme_config.py          # Category definitions, colors, fonts, and audio player
├── requirements.txt         # Project dependencies
└── README.md                # Documentation and user guide
```

---

## 🚀 How to Run

### Option 1: Modern Web Application (In Your Browser)
Run the web server:
```powershell
python "C:\Users\SANJIBAN\.gemini\antigravity-ide\scratch\calendar_reminder_app\web_app.py"
```
Then visit **[http://localhost:5000](http://localhost:5000)** in your browser (Google Chrome, Microsoft Edge, Firefox, Brave, etc.).

### Option 2: Standalone Desktop GUI (Tkinter)
Launch the native desktop window:
```powershell
python "C:\Users\SANJIBAN\.gemini\antigravity-ide\scratch\calendar_reminder_app\main.py"
```

---

## 🔔 How Notifications Work
The application runs an asynchronous polling loop every 3 seconds that queries `database.py` for any uncompleted reminders whose scheduled date and time match or have passed the current moment. When triggered:
1. An audio chime plays through Windows system audio (`winsound`).
2. A topmost popup dialog appears with snooze and completion buttons.
3. The database updates the `notified` flag to avoid repeated alerts for the same event.
