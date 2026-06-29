# Bloomboard — Design Document

## Overview

Bloomboard is a Flask-based web application designed to help students manage their academic life in one place. This document explains the technical decisions behind how the app was built, how the database was structured, and why certain approaches were chosen over alternatives.

## Application Structure — `app.py`

All Flask routes and backend logic live in a single `app.py` file. This was a deliberate decision rather than splitting the app into multiple modules or using Flask Blueprints. Since Bloomboard is a focused, single-developer project with a limited number of routes, keeping everything in one file made it easier to follow the flow of the application from top to bottom without jumping between files. For a larger production app with many contributors, splitting routes into Blueprints would make more sense — but for this scope, a single file kept things simple and readable, which aligns with the philosophy taught throughout CS50.

Flask was chosen over Django for similar reasons. Django comes with a lot of built-in structure and features that would have been unnecessary overhead for a project of this scale. Flask gives full control over exactly what gets included, making it easier to understand every line of the codebase. This also made debugging more straightforward since there was no "magic" happening behind the scenes.

## Database Design

The database, `BloomBoard.db`, is a SQLite file containing four tables: `users`, `tasks`, `subjects`, and `events`. SQLite was chosen because it requires no external server setup — the database is just a file that lives alongside the rest of the project, making it easy to run locally without any configuration.

The `users` table stores each user's ID, username, and hashed password. Passwords are never stored in plain text — they are hashed using Werkzeug's `generate_password_hash` before being saved, and verified on login using `check_password_hash`. This is the standard and safest approach for handling passwords in a Flask application.

The `tasks` table stores each task with a reference to the `user_id` of whoever created it, along with the task name, associated subject, and the date it was added. Storing the date of task creation was an important design decision — it is what powers the heatmap, since activity is measured by how many tasks were added on each given day.

The `subjects` table simply stores subject names tied to a `user_id`, allowing each user to have their own independent list of subjects. The `events` table stores calendar events with a title, date, and time, also tied to a `user_id` so that each user only sees their own events.

## Session Management and Authentication

Flask's built-in `session` object is used to manage user login state. When a user logs in successfully, their `user_id` is stored in the session. Every protected route checks for the presence of `session["user_id"]` before rendering — if it is missing, the user is redirected to the login page. This is the same pattern used in CS50's Finance problem set, and it proved to be reliable and easy to reason about.

A `secret_key` is set in the Flask app configuration to ensure that session cookies are signed and cannot be tampered with by the client. Without this, a malicious user could potentially forge a session cookie and impersonate another user.

## Heatmap Implementation

The heatmap was the most technically challenging feature to build. The goal was to display a full year of study activity as a grid of colored cells — similar to GitHub's contribution graph — where the color intensity of each cell reflects how many tasks were added on that day.

The backend generates this data by querying the `tasks` table and counting the number of tasks grouped by date for the logged-in user. This produces a dictionary where each key is a date string and each value is the task count for that day. This dictionary is then passed to the `heatmap.html` template via Flask.

The frontend challenge was constructing the grid itself. A full year has 365 or 366 days, and they need to be arranged into 7-row columns representing weeks, starting from the correct day of the week. This required calculating the starting weekday of January 1st and padding the beginning of the grid with empty cells so the days aligned correctly to Monday–Sunday columns. Getting this alignment right took considerable debugging — off-by-one errors in the padding logic caused days to appear on the wrong weekday, which broke the visual layout entirely.

Color intensity is applied using CSS classes that correspond to different activity levels. A day with zero tasks gets the lightest shade, while days with progressively more tasks get darker shades of green, giving an at-a-glance view of study consistency across the year.

## Calendar and Monthly Backgrounds

The calendar page allows users to add events with a title, date, and time. Events are stored in the `events` table and retrieved filtered by the logged-in user, then displayed on the page organized by date.

A small but meaningful design detail is that the calendar's background image changes based on the current month. Twelve images are stored in `static/months/`, and `app.py` passes the current month number to the template, which uses it to select the correct image dynamically via Jinja2. This was implemented using Python's `datetime` module to get the current month, then mapping it to the corresponding filename. It is a simple feature but it makes the app feel much more personal and alive compared to a static background.

## Frontend and Styling

All styling is handled in a single `static/style.css` file. Rather than using a CSS framework like Bootstrap, the styles were written from scratch to maintain full control over the visual design. The Poppins font was imported from Google Fonts to give the app a clean, modern look, and the color palette is built around warm greens and beiges to complement the floral aesthetic.

The `body_class` block in `layout.html` was introduced to allow each page to apply a unique background without duplicating the entire layout template. Each child template sets its own `body_class`, which gets injected into the `<body>` tag of the shared layout. This kept the code DRY (Don't Repeat Yourself) and made it easy to update or change backgrounds on a per-page basis without touching the layout itself.

## Conclusion

Every technical decision in Bloomboard was made with simplicity, clarity, and the student experience in mind. Flask and SQLite kept the stack approachable without sacrificing functionality. The heatmap required the most problem-solving, particularly around the grid alignment logic. Overall, building Bloomboard reinforced how much thoughtful design — both visual and technical — goes into even a relatively small web application.
