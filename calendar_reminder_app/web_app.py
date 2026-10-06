"""
Flask Web Application for Calendar and Reminder App.
Serves modern web interface and provides RESTful APIs for reminders,
calendar grid data, background alerts, and search.
"""

import os
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify
from database import ReminderDatabase

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


@app.after_request
def add_no_cache_headers(response):
    """Prevents browser caching during active development so changes reflect instantly."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Initialize database
db = ReminderDatabase()

# Seed default reminders if empty
stats = db.get_statistics()
if stats["total"] == 0:
    today_str = date.today().strftime("%Y-%m-%d")
    db.add_reminder(
        title="Welcome to Calenda!",
        date=today_str,
        time="09:00",
        category="General",
        description="Explore features: click calendar dates, toggle dark/light theme, and test alarms.",
        alarm_enabled=True,
    )
    db.add_reminder(
        title="Quarterly Strategy Sync",
        date=today_str,
        time="14:30",
        category="Work",
        description="Review team priorities, delivery roadmaps, and next month milestones.",
        alarm_enabled=True,
    )
    db.add_reminder(
        title="Evening Fitness Workout",
        date=today_str,
        time="18:00",
        category="Personal",
        description="Cardio run and stretching session.",
        alarm_enabled=True,
    )


@app.route("/")
def index():
    """Serves the main single-page web app."""
    return render_template("index.html")


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Returns dashboard metrics."""
    return jsonify(db.get_statistics())


@app.route("/api/reminders/month", methods=["GET"])
def get_month_reminders():
    """Returns all reminders in a specific month, grouped by date."""
    now = datetime.now()
    year = request.args.get("year", default=now.year, type=int)
    month = request.args.get("month", default=now.month, type=int)
    data = db.get_reminders_for_month(year, month)
    return jsonify(data)


@app.route("/api/reminders", methods=["GET"])
def get_reminders():
    """Retrieves reminders filtered by date, filter type, or search term."""
    q = request.args.get("q", "").strip()
    filter_type = request.args.get("filter", "date")
    date_str = request.args.get("date", date.today().strftime("%Y-%m-%d"))

    if q:
        items = db.search_reminders(q)
    elif filter_type == "today":
        items = db.get_reminders_by_date(date.today().strftime("%Y-%m-%d"))
    elif filter_type == "upcoming":
        items = db.get_upcoming_reminders(limit=50)
    elif filter_type == "all":
        items = db.get_all_reminders(limit=200)
    else:  # filter_type == 'date'
        items = db.get_reminders_by_date(date_str)

    return jsonify(items)


@app.route("/api/reminders/due", methods=["GET"])
def get_due_reminders():
    """Returns reminders that are currently due and unnotified."""
    due = db.get_due_reminders()
    return jsonify(due)


@app.route("/api/reminders", methods=["POST"])
def add_reminder():
    """Creates a new reminder."""
    data = request.get_json(force=True)
    title = data.get("title", "").strip()
    date_val = data.get("date", "").strip()
    time_val = data.get("time", "").strip()
    category = data.get("category", "General")
    description = data.get("description", "").strip()
    alarm_enabled = bool(data.get("alarm_enabled", True))

    if not title or not date_val or not time_val:
        return jsonify({"error": "Title, date, and time are required."}), 400

    new_id = db.add_reminder(
        title=title,
        date=date_val,
        time=time_val,
        category=category,
        description=description,
        alarm_enabled=alarm_enabled,
    )
    return jsonify({"success": True, "id": new_id}), 201


@app.route("/api/reminders/<int:reminder_id>", methods=["PUT"])
def update_reminder(reminder_id):
    """Updates an existing reminder."""
    data = request.get_json(force=True)
    title = data.get("title", "").strip()
    date_val = data.get("date", "").strip()
    time_val = data.get("time", "").strip()
    category = data.get("category", "General")
    description = data.get("description", "").strip()
    alarm_enabled = bool(data.get("alarm_enabled", True))

    if not title or not date_val or not time_val:
        return jsonify({"error": "Title, date, and time are required."}), 400

    success = db.update_reminder(
        reminder_id=reminder_id,
        title=title,
        date=date_val,
        time=time_val,
        category=category,
        description=description,
        alarm_enabled=alarm_enabled,
    )
    return jsonify({"success": success})


@app.route("/api/reminders/<int:reminder_id>", methods=["DELETE"])
def delete_reminder(reminder_id):
    """Deletes a reminder by ID."""
    success = db.delete_reminder(reminder_id)
    return jsonify({"success": success})


@app.route("/api/reminders/<string:reminder_id>/toggle", methods=["POST"])
def toggle_completed(reminder_id):
    """Toggles completed status."""
    if str(reminder_id).startswith("test-"):
        return jsonify({"success": True, "completed": True})
    try:
        new_status = db.toggle_completed(int(reminder_id))
        return jsonify({"success": True, "completed": new_status})
    except ValueError:
        return jsonify({"error": "Invalid reminder ID"}), 400


@app.route("/api/reminders/<string:reminder_id>/snooze", methods=["POST"])
def snooze_reminder(reminder_id):
    """Snoozes reminder by specified minutes (default 5)."""
    if str(reminder_id).startswith("test-"):
        return jsonify({"success": True})
    data = request.get_json(silent=True) or {}
    minutes = int(data.get("minutes", 5))
    try:
        res = db.snooze_reminder(int(reminder_id), minutes)
        return jsonify({"success": bool(res), "new_time": res})
    except ValueError:
        return jsonify({"error": "Invalid reminder ID"}), 400


@app.route("/api/reminders/<string:reminder_id>/notify", methods=["POST"])
def mark_notified(reminder_id):
    """Marks reminder as notified."""
    if str(reminder_id).startswith("test-"):
        return jsonify({"success": True})
    try:
        db.mark_notified(int(reminder_id))
        return jsonify({"success": True})
    except ValueError:
        return jsonify({"error": "Invalid reminder ID"}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Calendar & Reminder Web Server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
