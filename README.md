# Bloomboard
#### Video Demo: <https://youtu.be/Yu3plZ6rTco>
#### Description:

Bloomboard is a web-based study productivity website built for students who want to organize their academic life in one place. It allows users to manage their tasks, track their subjects, schedule events on a calendar, and visualize their study activity through a heatmap. The app was built using Python with Flask as the backend framework, SQLite as the database, and HTML/CSS with Jinja2 templating for the frontend.

## Why Bloomboard?

As a Pharmacy student, it can be hard to keep track of everything — assignments, subjects, deadlines, and study habits. Most productivity tools are either too complex or not designed with students in mind. Bloomboard was designed to be simple, visual, and friendly, with a soft floral aesthetic that makes studying feel a little less stressful.

## Features

Bloomboard includes the following core features:

- **User Authentication** — Students can create an account and securely log in
- **Task Management** — Add, view, and manage study tasks
- **Subject Tracking** — Organize tasks and activity by subject
- **Calendar** — Schedule and view events by month with custom monthly background images
- **Heatmap** — A GitHub-style heatmap that visualizes study activity over the year
- **Responsive Design** — Clean and consistent UI across all pages

## Files

### `app.py`
This is the heart of the application. It contains all the Flask routes and the logic that powers every page. This includes user registration and login with password hashing, session management, task creation and retrieval, subject management, calendar event handling, and the heatmap data generation. All database interactions happen through this file using SQLite.

### `BloomBoard.db`
This is the SQLite database that stores all of the app's data. It contains tables for users, tasks, subjects, and calendar events. Every time a user registers, logs a task, adds a subject, or creates a calendar event, the data is stored here.

### `requirements.txt`
This file lists all the Python dependencies needed to run Bloomboard. It includes Flask and any other libraries used in the project. Anyone wanting to run the app locally can install everything with `pip install -r requirements.txt`.

### `static/style.css`
This file contains all the styling for the entire application. It uses the Poppins font from Google Fonts and a warm, earthy color palette centered around greens and beiges. Each page has its own body class for custom backgrounds. The floral pattern is reused across multiple pages to keep the aesthetic consistent, while the calendar page uses unique monthly background images.

### `static/floral.png`
The main decorative background image used across the dashboard, tasks, subjects, and heatmap pages. It gives Bloomboard its signature soft floral look.

### `static/like.png`
An icon used within the UI for visual decoration.

### `static/months/`
A folder containing 12 background images, one for each month of the year (Jan.png, 2feb.png, march.png, etc.). These are dynamically applied to the calendar page based on the current month, making the calendar feel seasonal and personal.

### `templates/layout.html`
The base HTML template that all other pages extend using Jinja2. It contains the navigation bar with links to all sections of the app, flash message display, and a `body_class` block that allows individual pages to apply their own background styles. Having a shared layout ensures consistency across the app without repeating code.

### `templates/login.html`
The login page where returning users enter their username and password to access their account. It extends the layout and uses the `login-page` body class for a custom background. Error messages are displayed in red if login fails.

### `templates/register.html`
The registration page where new users create an account by entering a username, password, and password confirmation. Like the login page, it uses the `login-page` body class and displays errors if the inputs are invalid or the username is already taken.

### `templates/dashboard.html`
The main page users land on after logging in. It displays a welcome message and an overview of the user's stats, giving a quick summary of their productivity at a glance.

### `templates/tasks.html`
The tasks page where users can add new study tasks and view their existing ones. Tasks are displayed in a clean list format and are tied to the logged-in user's account.

### `templates/subjects.html`
The subjects page allows users to create and manage their academic subjects. Subjects are displayed as tabs, making it easy to filter and organize tasks by subject.

### `templates/calendar.html`
The calendar page lets users add events with a date, time, and title. The background image changes based on the current month using the images stored in `static/months/`, making the experience feel dynamic and visually engaging.

### `templates/heatmap.html`
The heatmap page displays a grid of colored cells representing study activity across the entire year, inspired by GitHub's contribution graph. The intensity of the color reflects how much activity was logged on that day, giving users a visual overview of their consistency over time.

## Design Choices

One major design decision was using Flask over a more complex framework like Django. Since this is a student project with a focused set of features, Flask's simplicity made it easier to build and understand every part of the app. It also aligns well with what was taught in CS50.

For the database, SQLite was chosen for its simplicity and because it requires no external setup, making the app easy to run locally without configuring a separate database server.

The floral aesthetic was a deliberate choice to make the app feel warm and personal rather than cold and corporate. Most productivity tools use very minimal or dark designs — Bloomboard was designed to feel more like a personal journal than a work tool.

The `body_class` block in `layout.html` was introduced to allow each page to have its own background without duplicating the entire layout. This kept the code clean and made it easy to add or change backgrounds per page.

## How to Run

1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `flask run`
3. Open your browser and go to `http://127.0.0.1:5000`
