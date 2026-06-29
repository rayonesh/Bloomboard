import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, timedelta

# Configure application
app = Flask(__name__)

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure database
db = SQL("sqlite:///BloomBoard.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# ──────────────────────────────────────────────
#  AUTH
# ──────────────────────────────────────────────

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username     = request.form.get("username")
        password     = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return render_template("register.html", error="Must provide username")
        if not password:
            return render_template("register.html", error="Must provide password")
        if not confirmation:
            return render_template("register.html", error="Must confirm password")
        if password != confirmation:
            return render_template("register.html", error="Passwords do not match")

        try:
            db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                username, generate_password_hash(password)
            )
        except ValueError:
            return render_template("register.html", error="Username already exists")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]
        session["username"] = username

        flash("Account created!")
        return redirect("/dashboard")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return render_template("login.html", error="Must provide username")
        if not password:
            return render_template("login.html", error="Must provide password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return render_template("login.html", error="Invalid username and/or password")

        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        return redirect("/dashboard")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ──────────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect("/login")

    user_id = session["user_id"]

    # Total completions ever
    total = db.execute(
        "SELECT COUNT(*) AS cnt FROM completions WHERE user_id = ?", user_id
    )[0]["cnt"]

    # Current streak — count consecutive days going back from today
    today = date.today()
    streak = 0
    check = today
    while True:
        row = db.execute(
            "SELECT COUNT(*) AS cnt FROM completions WHERE user_id = ? AND completed_date = ?",
            user_id, check.isoformat()
        )
        if row[0]["cnt"] > 0:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    # Tasks belonging to this user
    tasks = db.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC", user_id
    )

    # Which tasks were completed today
    completed_today = db.execute(
        "SELECT task_id FROM completions WHERE user_id = ? AND completed_date = ?",
        user_id, today.isoformat()
    )
    completed_ids = {r["task_id"] for r in completed_today}

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total=total,
        streak=streak,
        completed_ids=completed_ids,
        username=session["username"]
    )


# ──────────────────────────────────────────────
#  TASKS
# ──────────────────────────────────────────────
@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if not session.get("user_id"):
        return redirect("/login")

    if request.method == "POST":
        name = request.form.get("task_name")
        subject_id = request.form.get("subject_id") or None
        if name:
            db.execute(
                "INSERT INTO tasks (user_id, name, subject_id) VALUES (?, ?, ?)",
                session["user_id"], name.strip(), subject_id
            )
            flash("Task added!")
        return redirect(request.referrer or "/tasks")

    # Get active subject from URL param
    active_subject = request.args.get("subject", type=int)

    if active_subject:
        user_tasks = db.execute(
            """SELECT tasks.*, subjects.name AS subject_name
               FROM tasks
               LEFT JOIN subjects ON tasks.subject_id = subjects.id
               WHERE tasks.user_id = ? AND tasks.subject_id = ?
               ORDER BY tasks.created_at DESC""",
            session["user_id"], active_subject
        )
    else:
        user_tasks = db.execute(
            """SELECT tasks.*, subjects.name AS subject_name
               FROM tasks
               LEFT JOIN subjects ON tasks.subject_id = subjects.id
               WHERE tasks.user_id = ?
               ORDER BY tasks.created_at DESC""",
            session["user_id"]
        )

    user_subjects = db.execute(
        "SELECT * FROM subjects WHERE user_id = ? ORDER BY name ASC",
        session["user_id"]
    )

    return render_template(
        "tasks.html",
        tasks=user_tasks,
        subjects=user_subjects,
        active_subject=active_subject
    )

@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if not session.get("user_id"):
        return redirect("/login")

    db.execute(
        "DELETE FROM completions WHERE task_id = ? AND user_id = ?",
        task_id, session["user_id"]
    )
    db.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        task_id, session["user_id"]
    )
    flash("Task deleted.")
    return redirect("/tasks")


# ──────────────────────────────────────────────
#  COMPLETE A TASK
# ──────────────────────────────────────────────

@app.route("/complete/<int:task_id>", methods=["POST"])
def complete(task_id):
    if not session.get("user_id"):
        return redirect("/login")

    today = date.today().isoformat()
    user_id = session["user_id"]

    # Prevent duplicate completion for same task on same day
    existing = db.execute(
        "SELECT id FROM completions WHERE user_id = ? AND task_id = ? AND completed_date = ?",
        user_id, task_id, today
    )

    if not existing:
        db.execute(
            "INSERT INTO completions (user_id, task_id, completed_date) VALUES (?, ?, ?)",
            user_id, task_id, today
        )
        flash("Task marked complete!")
    else:
        flash("Already completed today.")

    return redirect("/dashboard")


# ──────────────────────────────────────────────
#  HEATMAP
# ──────────────────────────────────────────────
@app.route("/heatmap")
def heatmap():
    if not session.get("user_id"):
        return redirect("/login")

    user_id = session["user_id"]
    today = date.today()

    # Get the year the user registered
    user = db.execute("SELECT created_at FROM users WHERE id = ?", user_id)[0]
    join_year = int(user["created_at"][:4])

    # Get selected year from URL, default to current year
    selected_year = request.args.get("year", type=int, default=today.year)
    selected_year = max(join_year, min(selected_year, today.year))

    year_start = date(selected_year, 1, 1)
    year_end = date(selected_year, 12, 31) if selected_year < today.year else today

    rows = db.execute(
        """SELECT completed_date, COUNT(*) AS cnt
           FROM completions
           WHERE user_id = ? AND completed_date >= ? AND completed_date <= ?
           GROUP BY completed_date""",
        user_id, year_start.isoformat(), year_end.isoformat()
    )

    activity = {r["completed_date"]: r["cnt"] for r in rows}

    total_this_year = db.execute(
        """SELECT COUNT(*) AS cnt FROM completions
           WHERE user_id = ? AND completed_date >= ? AND completed_date <= ?""",
        user_id, year_start.isoformat(), year_end.isoformat()
    )[0]["cnt"]

    cal_grid = []
    for m in range(1, 13):
        month_weeks = []
        for week in range(4):
            week_days = []
            for dow in range(7):
                day_num = week * 7 + dow + 1
                try:
                    d = date(selected_year, m, day_num)
                    week_days.append(d)
                except ValueError:
                    week_days.append(None)
            month_weeks.append(week_days)
        cal_grid.append(month_weeks)

    # Available years from join year to current year
    available_years = list(range(join_year, today.year + 1))

    return render_template(
        "heatmap.html",
        activity=activity,
        today_date=today,
        year_start=year_start,
        timedelta=timedelta,
        username=session["username"],
        cal_grid=cal_grid,
        total_this_year=total_this_year,
        selected_year=selected_year,
        available_years=available_years
    )
# ──────────────────────────────────────────────
#  SUBJECTS
# ──────────────────────────────────────────────
@app.route("/subjects", methods=["GET", "POST"])
def subjects():
    if not session.get("user_id"):
        return redirect("/login")

    if request.method == "POST":
        name = request.form.get("subject_name")
        if name:
            db.execute(
                "INSERT INTO subjects (user_id, name) VALUES (?, ?)",
                session["user_id"], name.strip()
            )
            flash("Subject added!")
        return redirect("/subjects")

    user_subjects = db.execute(
        "SELECT * FROM subjects WHERE user_id = ? ORDER BY name ASC",
        session["user_id"]
    )

    # Fetch tasks for each subject
    for subject in user_subjects:
        subject["tasks"] = db.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND subject_id = ?",
            session["user_id"], subject["id"]
        )

    return render_template("subjects.html", subjects=user_subjects)

@app.route("/subjects/delete/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    if not session.get("user_id"):
        return redirect("/login")

    # Unassign tasks under this subject rather than deleting them
    db.execute(
        "UPDATE tasks SET subject_id = NULL WHERE subject_id = ? AND user_id = ?",
        subject_id, session["user_id"]
    )
    db.execute(
        "DELETE FROM subjects WHERE id = ? AND user_id = ?",
        subject_id, session["user_id"]
    )
    flash("Subject deleted.")
    return redirect("/subjects")

# ──────────────────────────────────────────────
#  CALENDAR
# ──────────────────────────────────────────────

@app.route("/calendar", methods=["GET", "POST"])
def calendar():
    if not session.get("user_id"):
        return redirect("/login")

    user_id = session["user_id"]

    if request.method == "POST":
        title       = request.form.get("title")
        event_date  = request.form.get("event_date")
        event_time  = request.form.get("event_time") or None
        subject_id  = request.form.get("subject_id") or None
        description = request.form.get("description") or None

        if title and event_date:
            db.execute(
                "INSERT INTO events (user_id, subject_id, title, description, event_date, event_time) VALUES (?, ?, ?, ?, ?, ?)",
                user_id, subject_id, title.strip(), description, event_date, event_time
            )
            flash("Event added!")
        return redirect("/calendar")

    # Get month/year from query param, default to today
    today = date.today()
    month = request.args.get("month", type=int, default=today.month)
    year  = request.args.get("year",  type=int, default=today.year)

    # Clamp month
    if month < 1: month, year = 12, year - 1
    if month > 12: month, year = 1, year + 1

    # All events for this month
    month_str = f"{year}-{month:02d}"
    events = db.execute(
        """SELECT events.*, subjects.name AS subject_name
           FROM events
           LEFT JOIN subjects ON events.subject_id = subjects.id
           WHERE events.user_id = ? AND events.event_date LIKE ?
           ORDER BY events.event_date, events.event_time""",
        user_id, f"{month_str}%"
    )

    # Group events by date
    events_by_date = {}
    for e in events:
        events_by_date.setdefault(e["event_date"], []).append(e)

    subjects = db.execute(
        "SELECT * FROM subjects WHERE user_id = ? ORDER BY name ASC", user_id
    )

    import calendar as cal
    cal_matrix = cal.monthcalendar(year, month)
    month_name = date(year, month, 1).strftime("%B %Y")

    # Prev / next month
    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year  = year if month < 12 else year + 1

    return render_template(
        "calendar.html",
        cal_matrix=cal_matrix,
        month_name=month_name,
        month=month, year=year,
        today=today,
        events_by_date=events_by_date,
        subjects=subjects,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year
    )


@app.route("/events/delete/<int:event_id>", methods=["POST"])
def delete_event(event_id):
    if not session.get("user_id"):
        return redirect("/login")
    db.execute(
        "DELETE FROM events WHERE id = ? AND user_id = ?",
        event_id, session["user_id"]
    )
    flash("Event deleted.")
    return redirect("/calendar")
