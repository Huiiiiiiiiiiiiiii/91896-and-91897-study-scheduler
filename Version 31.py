"""
STUDY SCHEDULER
Author: Hui Su
Date: 2026-07-22
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta
import hashlib
import unittest

# ============================================
# CONSTANTS
# ============================================
MAX_HOURS_PER_DAY = 24
MIN_HOURS = 0
MAX_PLAN_DAYS = 30
MIN_USERNAME_LENGTH = 3
MIN_PASSWORD_LENGTH = 6
MIN_SUBJECT_NAME_LENGTH = 2
DATE_FORMAT = "%d/%m/%Y"

DEFAULT_SUBJECT_HOURS = 5
DEFAULT_PLAN_HOURS = 3
DEFAULT_WORK_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5
SECONDS_PER_MINUTE = 60
PLAN_UNIT_HOURS = 0.1
PLAN_SESSION_HOURS = 0.5
POMODORO_BAR_BLOCKS = 16
DAILY_PLAN_BAR_BLOCKS = 8
WEEKLY_PLAN_BAR_BLOCKS = 12
FAR_FUTURE_DAYS = 10_000

URGENT_DEADLINE_DAYS = 3
NEAR_DEADLINE_DAYS = 7
UPCOMING_DEADLINE_DAYS = 14
URGENT_DEADLINE_MULTIPLIER = 1.3
NEAR_DEADLINE_MULTIPLIER = 1.15
UPCOMING_DEADLINE_MULTIPLIER = 1.05

# Store data beside the script to avoid restricted save locations.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

APP_NAME = "StudyMate"

LIGHT_THEME = {
    "bg": "#f5f0fa",
    "frame_bg": "#ffffff",
    "card_bg": "#ffffff",
    "accent": "#6b46c1",
    "accent_light": "#9b6dff",
    "accent_dark": "#553c9a",
    "text": "#2d2d5e",
    "text_light": "#718096",
    "text_white": "#ffffff",
    "success": "#2e7d64",
    "delete": "#b91c1c",
    "warning": "#d69e2e",
    "chart_bar": "#6b46c1",
    "entry_bg": "#ffffff",
    "entry_fg": "#2d2d5e",
    "tab_fg": "#2d2d5e",
}

DARK_THEME = {
    "bg": "#1a1a2e",
    "frame_bg": "#16213e",
    "card_bg": "#16213e",
    "accent": "#7c3aed",
    "accent_light": "#a78bfa",
    "accent_dark": "#5b21b6",
    "text": "#e2e2e2",
    "text_light": "#a0a0b8",
    "text_white": "#ffffff",
    "success": "#34d399",
    "delete": "#f87171",
    "warning": "#fbbf24",
    "chart_bar": "#a78bfa",
    "entry_bg": "#2d2d5e",
    "entry_fg": "#e2e2e2",
    "tab_fg": "#e2e2e2",
}

COLORS = LIGHT_THEME.copy()

# Use a common cross-platform font.
FONT_FAMILY = "Arial"


def parse_number(
    value,
    field_name,
    *,
    minimum=None,
    maximum=None,
    integer=False,
    minimum_inclusive=True,
):
    """Convert and validate a numeric GUI input using clear user messages."""
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} is required.")

    try:
        number = int(text) if integer else float(text)
    except (TypeError, ValueError) as exc:
        expected = "a whole number" if integer else "a number"
        raise ValueError(f"{field_name} must be {expected}.") from exc

    if minimum is not None:
        below_minimum = (
            number < minimum
            if minimum_inclusive
            else number <= minimum
        )
        if below_minimum:
            wording = "at least" if minimum_inclusive else "greater than"
            raise ValueError(
                f"{field_name} must be {wording} {minimum:g}."
            )

    if maximum is not None and number > maximum:
        raise ValueError(
            f"{field_name} must be no more than {maximum:g}."
        )

    return number


def validate_deadline(deadline, field_name="Deadline"):
    """Return a valid deadline date and reject invalid or past dates."""
    try:
        deadline_date = datetime.strptime(deadline, DATE_FORMAT).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must use DD/MM/YYYY."
        ) from exc

    if deadline_date < datetime.now().date():
        raise ValueError(f"{field_name} cannot be in the past.")

    return deadline_date


def draw_logo(canvas, x, y, size=35, color="#6b46c1"):
    """Draw the StudyMate star-and-book logo on a Tkinter canvas."""
    star_points = [
        x, y - size * 0.7,
        x + size * 0.08, y - size * 0.45,
        x + size * 0.35, y - size * 0.45,
        x + size * 0.14, y - size * 0.28,
        x + size * 0.22, y - size * 0.05,
        x, y - size * 0.18,
        x - size * 0.22, y - size * 0.05,
        x - size * 0.14, y - size * 0.28,
        x - size * 0.35, y - size * 0.45,
        x - size * 0.08, y - size * 0.45,
    ]
    canvas.create_polygon(star_points, fill=color, outline="", tags="logo")
    canvas.create_polygon(
        x, y - size * 0.1,
        x - size * 0.3, y - size * 0.1,
        x - size * 0.3, y + size * 0.4,
        x, y + size * 0.4,
        fill="white", outline=color, width=2, tags="logo"
    )
    canvas.create_polygon(
        x, y - size * 0.1,
        x + size * 0.3, y - size * 0.1,
        x + size * 0.3, y + size * 0.4,
        x, y + size * 0.4,
        fill="white", outline=color, width=2, tags="logo"
    )
    canvas.create_line(
        x, y - size * 0.1, x, y + size * 0.4,
        fill=color, width=2, tags="logo",
    )
    for i in range(3):
        y_pos = y + size * 0.05 + i * size * 0.1
        canvas.create_line(
            x - size * 0.25, y_pos, x - size * 0.05, y_pos,
            fill=color, width=1.5, tags="logo",
        )
    for i in range(3):
        y_pos = y + size * 0.05 + i * size * 0.1
        canvas.create_line(
            x + size * 0.05, y_pos, x + size * 0.25, y_pos,
            fill=color, width=1.5, tags="logo",
        )


_BUTTON_STYLE_COUNTER = 0


class AppButton(ttk.Button):
    """A styled ttk button that renders consistently on macOS and Windows.

    macOS can ignore the background colour of classic ``tk.Button`` widgets,
    which may leave white text on a white system button.  This wrapper uses the
    cross-platform ``clam`` ttk theme and maps the options already used by the
    rest of the program onto a custom ttk style.
    """

    def __init__(
        self,
        master=None,
        *,
        text="",
        command=None,
        bg=None,
        fg=None,
        font=None,
        relief="flat",
        cursor="hand2",
        height=None,
        padx=12,
        pady=7,
        **kwargs,
    ):
        """Create a consistently styled cross-platform ttk button."""
        global _BUTTON_STYLE_COUNTER
        _BUTTON_STYLE_COUNTER += 1

        background = bg or COLORS["accent"]
        foreground = fg or "#ffffff"
        button_font = font or (FONT_FAMILY, 10, "bold")

        style = ttk.Style(master)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style_name = f"StudyMate{_BUTTON_STYLE_COUNTER}.TButton"
        style.configure(
            style_name,
            background=background,
            foreground=foreground,
            font=button_font,
            padding=(padx, pady),
            borderwidth=1,
            relief=relief,
            anchor="center",
        )
        style.map(
            style_name,
            background=[
                ("disabled", COLORS["text_light"]),
                ("pressed", COLORS["accent_dark"]),
                ("active", COLORS["accent_light"]),
            ],
            foreground=[
                ("disabled", "#e5e7eb"),
                ("pressed", "#ffffff"),
                ("active", "#ffffff"),
            ],
        )

        # ``height`` belongs to classic tk.Button, not ttk.Button.  Vertical
        # size is handled through the style padding above.
        super().__init__(
            master,
            text=text,
            command=command,
            style=style_name,
            cursor=cursor,
            **kwargs,
        )


class User:
    """Store one user account, study data, tasks, logs and planning logic."""
    PRIORITIES = ["High", "Medium", "Low"]
    PRIORITY_WEIGHTS = {"High": 1.5, "Medium": 1.0, "Low": 0.5}

    def __init__(self, username, password_hash):
        """Initialise a user account and its default study data."""
        self.username = username
        self.password_hash = password_hash
        self.subjects = {}
        self.logs = {}
        self.theme = "light"
        self.pomodoro_count = 0
        self.focus_time_today = 0
        self.work_minutes = DEFAULT_WORK_MINUTES
        self.break_minutes = DEFAULT_BREAK_MINUTES
        # Task storage.
        self.tasks = []
        self.next_task_id = 1

    def check_password(self, password):
        """Return whether the supplied password matches the stored hash."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return self.password_hash == password_hash

    @staticmethod
    def normalise_subject_name(name):
        """Return a consistently formatted subject name."""
        cleaned = " ".join(name.strip().split())
        return " ".join(
            word if word.isupper() else word.capitalize()
            for word in cleaned.split()
        )

    def add_subject(
        self,
        name,
        hours,
        priority="Medium",
        deadline=None,
        goal_hours=None,
        target_grade=None,
    ):
        """Validate and add a subject to the user subject dictionary."""
        raw_name = " ".join(name.strip().split())
        if len(raw_name) < MIN_SUBJECT_NAME_LENGTH:
            raise ValueError("Subject name must be at least 2 characters.")

        normalised_name = self.normalise_subject_name(raw_name)
        duplicate_exists = any(
            existing.casefold() == normalised_name.casefold()
            for existing in self.subjects
        )
        if duplicate_exists:
            raise ValueError(
                f"Subject '{normalised_name}' already exists. "
                "Please enter a different subject."
            )

        if not (MIN_HOURS <= hours <= MAX_HOURS_PER_DAY):
            raise ValueError(
                f"Hours must be between {MIN_HOURS} and {MAX_HOURS_PER_DAY}."
            )
        if priority not in self.PRIORITIES:
            raise ValueError("Invalid priority.")
        if deadline:
            validate_deadline(deadline)
        if goal_hours is not None and not (
            MIN_HOURS <= goal_hours <= MAX_HOURS_PER_DAY
        ):
            raise ValueError("Goal hours must be between 0 and 24.")

        self.subjects[normalised_name] = {
            "hours": hours,
            "priority": priority,
            "deadline": deadline,
            # Retained for compatibility with existing JSON data.  The user no
            # longer needs to enter a second, confusing hours value.
            "goal_hours": hours if goal_hours is None else goal_hours,
            "target_grade": (target_grade or "").strip(),
        }
        return normalised_name

    def delete_subject(self, name):
        """Delete a subject and clean up linked logs and tasks."""
        if name not in self.subjects:
            return False

        del self.subjects[name]

        # Remove orphaned log entries and detach tasks from the
        # deleted subject.
        for date in list(self.logs):
            self.logs[date].pop(name, None)
            if not self.logs[date]:
                del self.logs[date]
        for task in self.tasks:
            if task.get("subject") == name:
                task["subject"] = None
        return True

    def get_logged_hours_by_subject(self, start_date=None, end_date=None):
        """Return logged hours per subject, optionally limited to a date range.

        ``start_date`` and ``end_date`` should be ``datetime.date`` objects.
        Invalid legacy date entries are ignored rather than crashing the app.
        """
        totals = {name: 0.0 for name in self.subjects}
        for date_text, daily_log in self.logs.items():
            try:
                log_date = datetime.strptime(date_text, DATE_FORMAT).date()
            except (TypeError, ValueError):
                continue

            if start_date is not None and log_date < start_date:
                continue
            if end_date is not None and log_date > end_date:
                continue

            for subject, hours in daily_log.items():
                if subject in totals:
                    totals[subject] += float(hours)
        return totals

    def get_subject_weight(self, subject_data):
        """Return the planning weight from priority and deadline urgency."""
        weight = self.PRIORITY_WEIGHTS.get(subject_data["priority"], 1.0)
        if subject_data.get("deadline"):
            try:
                deadline_date = datetime.strptime(
                    subject_data["deadline"],
                    DATE_FORMAT,
                ).date()
                days_left = (deadline_date - datetime.now().date()).days
                if 0 <= days_left <= URGENT_DEADLINE_DAYS:
                    weight *= URGENT_DEADLINE_MULTIPLIER
                elif 0 <= days_left <= NEAR_DEADLINE_DAYS:
                    weight *= NEAR_DEADLINE_MULTIPLIER
                elif 0 <= days_left <= UPCOMING_DEADLINE_DAYS:
                    weight *= UPCOMING_DEADLINE_MULTIPLIER
            except ValueError:
                pass
        return weight

    def _allocate_with_weekly_caps(self, targets, capacity):
        """Allocate time without exceeding subject targets.

        Calculations use 0.1-hour units so displayed totals remain exact.
        Priority and deadline weights only change the distribution when the
        available capacity is lower than the combined target hours.
        """
        if capacity <= 0:
            raise ValueError("Available hours must be positive.")

        unit = PLAN_UNIT_HOURS
        target_units = {
            name: max(0, int(round(float(hours) / unit)))
            for name, hours in targets.items()
        }
        total_target_units = sum(target_units.values())
        if total_target_units == 0:
            return {name: 0.0 for name in targets}

        capacity_units = min(
            max(0, int(round(float(capacity) / unit))),
            total_target_units,
        )

        if capacity_units >= total_target_units:
            return {
                name: round(units * unit, 1)
                for name, units in target_units.items()
            }

        scores = {
            name: max(
                target_units[name]
                * self.get_subject_weight(self.subjects[name]),
                0.0001,
            )
            for name in target_units
        }

        # Capped weighted allocation (water-filling).
        allocated_float = {name: 0.0 for name in target_units}
        active = {name for name, units in target_units.items() if units > 0}
        remaining_capacity = float(capacity_units)

        while active and remaining_capacity > 1e-9:
            total_score = sum(scores[name] for name in active)
            if total_score <= 0:
                equal_share = remaining_capacity / len(active)
                proposed = {name: equal_share for name in active}
            else:
                proposed = {
                    name: remaining_capacity * scores[name] / total_score
                    for name in active
                }

            capped = []
            for name in active:
                room = target_units[name] - allocated_float[name]
                if proposed[name] >= room - 1e-9:
                    capped.append(name)

            if not capped:
                for name in active:
                    allocated_float[name] += proposed[name]
                remaining_capacity = 0.0
                break

            for name in capped:
                room = target_units[name] - allocated_float[name]
                allocated_float[name] += room
                remaining_capacity -= room
                active.remove(name)

        # Convert to exact integer 0.1-hour units using largest remainders.
        allocated_units = {
            name: min(target_units[name], int(allocated_float[name]))
            for name in target_units
        }
        leftover = capacity_units - sum(allocated_units.values())

        while leftover > 0:
            eligible = [
                name for name in target_units
                if allocated_units[name] < target_units[name]
            ]
            if not eligible:
                break
            eligible.sort(
                key=lambda name: (
                    allocated_float[name] - int(allocated_float[name]),
                    self.get_subject_weight(self.subjects[name]),
                    target_units[name] - allocated_units[name],
                ),
                reverse=True,
            )
            for name in eligible:
                if leftover <= 0:
                    break
                if allocated_units[name] < target_units[name]:
                    allocated_units[name] += 1
                    leftover -= 1

        return {
            name: round(units * unit, 1)
            for name, units in allocated_units.items()
        }

    def generate_daily_plan(self, available_hours):
        """Generate a one-day plan without exceeding weekly targets."""
        if not self.subjects:
            return {}
        if not (0 < available_hours <= MAX_HOURS_PER_DAY):
            raise ValueError(
                "Available study hours must be greater than 0 "
                "and no more than 24."
            )
        targets = {
            name: float(data["hours"])
            for name, data in self.subjects.items()
        }
        allocation = self._allocate_with_weekly_caps(
            targets,
            available_hours,
        )
        today = datetime.now().strftime(DATE_FORMAT)
        return {
            today: {
                name: hours
                for name, hours in allocation.items()
                if hours > 0
            }
        }

    def generate_weekly_schedule(self, max_hours_per_day, days=7):
        """Generate a schedule that respects weekly-hour targets.

        A subject entered as 2 weekly hours receives a total target of 2 hours
        across a seven-day plan, not 2 hours on every day. Periods longer or
        shorter than seven days scale the target proportionally.
        """
        if not self.subjects:
            return {}, {}
        if not (0 < max_hours_per_day <= MAX_HOURS_PER_DAY):
            raise ValueError(
                "Available hours per day must be greater than 0 "
                "and no more than 24."
            )
        if days < 1 or days > MAX_PLAN_DAYS:
            raise ValueError("Days must be between 1 and 30.")

        period_factor = days / 7.0
        desired_by_subject = {
            name: round(float(data["hours"]) * period_factor, 1)
            for name, data in self.subjects.items()
        }
        total_capacity = round(float(max_hours_per_day) * days, 1)
        scheduled_by_subject = self._allocate_with_weekly_caps(
            desired_by_subject,
            total_capacity,
        )

        # Spread scheduled totals across days while respecting the daily cap.
        unit = PLAN_UNIT_HOURS
        daily_capacity_units = max(
            1,
            int(round(max_hours_per_day / unit)),
        )
        day_remaining = [daily_capacity_units for _ in range(days)]
        day_allocations = [dict() for _ in range(days)]

        def deadline_days_left(subject_name):
            """Return days remaining until the subject deadline."""
            deadline = self.subjects[subject_name].get("deadline")
            if not deadline:
                return FAR_FUTURE_DAYS
            try:
                deadline_date = datetime.strptime(
                    deadline,
                    DATE_FORMAT,
                ).date()
                return max(
                    (deadline_date - datetime.now().date()).days,
                    0,
                )
            except ValueError:
                return FAR_FUTURE_DAYS

        ordered_subjects = sorted(
            scheduled_by_subject,
            key=lambda name: (
                -self.get_subject_weight(self.subjects[name]),
                deadline_days_left(name),
                name.casefold(),
            ),
        )

        for name in ordered_subjects:
            remaining_units = int(
                round(scheduled_by_subject[name] / unit)
            )
            while remaining_units > 0:
                all_available_days = [
                    index
                    for index, remaining in enumerate(day_remaining)
                    if remaining > 0
                ]
                if not all_available_days:
                    break

                # When a deadline falls inside the selected period, try to
                # place the subject's sessions on or before that date.  If
                # there is not enough capacity before the deadline, use later
                # days rather than dropping the remaining target entirely.
                latest_day = min(
                    deadline_days_left(name),
                    days - 1,
                )
                before_deadline = [
                    index
                    for index in all_available_days
                    if index <= latest_day
                ]
                available_days = before_deadline or all_available_days

                # Use the least-filled eligible day; ties favour earlier
                # dates. Plan practical sessions of up to 0.5h rather than
                # scattering 0.1h entries across every day.
                day_index = max(
                    available_days,
                    key=lambda index: (day_remaining[index], -index),
                )
                chunk_units = min(
                    int(round(PLAN_SESSION_HOURS / PLAN_UNIT_HOURS)),
                    remaining_units,
                    day_remaining[day_index],
                )
                day_allocations[day_index][name] = (
                    day_allocations[day_index].get(name, 0)
                    + chunk_units
                )
                day_remaining[day_index] -= chunk_units
                remaining_units -= chunk_units

        plan = {}
        today = datetime.now()
        for index in range(days):
            date_text = (
                today + timedelta(days=index)
            ).strftime(DATE_FORMAT)
            plan[date_text] = {
                name: round(units * unit, 1)
                for name, units in day_allocations[index].items()
                if units > 0
            }

        total_desired = round(sum(desired_by_subject.values()), 1)
        total_scheduled = round(sum(scheduled_by_subject.values()), 1)
        summary = {
            "days": days,
            "max_hours_per_day": round(float(max_hours_per_day), 1),
            "total_capacity": total_capacity,
            "desired_by_subject": desired_by_subject,
            "scheduled_by_subject": scheduled_by_subject,
            "total_desired": total_desired,
            "total_scheduled": total_scheduled,
            "unused_capacity": round(
                max(total_capacity - total_scheduled, 0.0),
                1,
            ),
            "shortfall": round(
                max(total_desired - total_scheduled, 0.0),
                1,
            ),
            "capacity_limited": total_capacity + 1e-9 < total_desired,
        }
        return plan, summary

    def generate_plan(self, available_hours, days=7):
        """Backward-compatible wrapper for older code and tests."""
        if days == 1:
            return self.generate_daily_plan(available_hours)
        plan, _summary = self.generate_weekly_schedule(
            available_hours,
            days,
        )
        return plan

    def log_study_time(self, date, subject, hours):
        """Validate and store study time for one subject and date."""
        if subject not in self.subjects:
            raise ValueError(f"Subject '{subject}' not found.")
        try:
            datetime.strptime(date, DATE_FORMAT)
        except ValueError as exc:
            raise ValueError("Invalid date format. Use DD/MM/YYYY.") from exc
        if not (0 < hours <= MAX_HOURS_PER_DAY):
            raise ValueError(
                "Logged hours must be greater than 0 and no more than 24."
            )
        if date not in self.logs:
            self.logs[date] = {}
        self.logs[date][subject] = self.logs[date].get(subject, 0) + hours
        return True

    def get_completion_rate(self, date, plan):
        """Return the completion ratio for a planned study date."""
        if date not in self.logs:
            return 0.0
        log = self.logs[date]
        total_planned = (
            sum(plan.get(date, {}).values())
            if plan.get(date)
            else 0
        )
        total_actual = sum(log.values())
        if total_planned == 0:
            return 1.0 if total_actual == 0 else 0.0
        return round(min(total_actual / total_planned, 1.0), 2)

    def get_goal_completion(self, subject_name):
        """Return the stored goal completion ratio for a subject."""
        if subject_name not in self.subjects:
            return 0
        data = self.subjects[subject_name]
        goal = data.get("goal_hours", data["hours"])
        actual = data["hours"]
        return round(min(actual / goal, 1.0), 2) if goal > 0 else 1.0

    # Task management methods.
    def add_task(self, title, subject=None, deadline=None, priority="Medium"):
        """Validate and append a new task to the user task list."""
        if not title or len(title.strip()) < 1:
            raise ValueError("Task title cannot be empty.")
        if subject and subject not in self.subjects:
            raise ValueError(f"Subject '{subject}' not found.")
        if deadline:
            validate_deadline(deadline, "Task deadline")

        task = {
            "id": self.next_task_id,
            "title": title.strip(),
            "subject": subject,
            "deadline": deadline,
            "priority": priority,
            "completed": False,
            "created_at": datetime.now().strftime(DATE_FORMAT)
        }
        self.tasks.append(task)
        self.next_task_id += 1
        return task

    def toggle_task(self, task_id):
        """Toggle the completed state of the task with the given ID."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["completed"] = not task["completed"]
                return True
        return False

    def delete_task(self, task_id):
        """Delete the task with the given ID if it exists."""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                del self.tasks[i]
                return True
        return False

    def get_task_count(self):
        """Return the total number of stored tasks."""
        return len(self.tasks)

    def get_completed_count(self):
        """Return the number of tasks marked as completed."""
        return sum(1 for t in self.tasks if t["completed"])

    def to_dict(self):
        """Convert the user object into JSON-serialisable data."""
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "subjects": self.subjects,
            "logs": self.logs,
            "theme": self.theme,
            "pomodoro_count": self.pomodoro_count,
            "focus_time_today": self.focus_time_today,
            "work_minutes": self.work_minutes,
            "break_minutes": self.break_minutes,
            "tasks": self.tasks,
            "next_task_id": self.next_task_id
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a User object from saved dictionary data."""
        user = cls(data["username"], data["password_hash"])
        user.subjects = data.get("subjects", {})
        user.logs = data.get("logs", {})
        user.theme = data.get("theme", "light")
        user.pomodoro_count = data.get("pomodoro_count", 0)
        user.focus_time_today = data.get("focus_time_today", 0)
        user.work_minutes = data.get("work_minutes", DEFAULT_WORK_MINUTES)
        user.break_minutes = data.get("break_minutes", DEFAULT_BREAK_MINUTES)
        user.tasks = data.get("tasks", [])
        user.next_task_id = data.get("next_task_id", 1)
        return user


class DataManager:
    """Load and save StudyMate user data in the local JSON file."""
    @staticmethod
    def load_users():
        """Load all saved users from the local JSON file."""
        if not os.path.exists(USERS_FILE):
            return {}
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                username: User.from_dict(user_data)
                for username, user_data in data.items()
            }
        except (json.JSONDecodeError, KeyError, OSError, TypeError):
            return {}

    @staticmethod
    def save_users(users):
        """Save all user data and report file-system errors to the user."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            data = {
                username: user.to_dict()
                for username, user in users.items()
            }
            with open(USERS_FILE, "w", encoding="utf-8") as file_handle:
                json.dump(data, file_handle, indent=4, ensure_ascii=False)
            return True
        except (OSError, TypeError, ValueError) as exc:
            messagebox.showerror(
                "Save Error",
                f"StudyMate could not save your data: {exc}",
            )
            return False


class AuthWindow:
    # Shared user data is loaded before the authentication window starts.
    """Manage account registration, login and transition to the main app."""
    users = {}

    def __init__(self):
        # Reference the shared class-level user dictionary.
        """Create the authentication window and load its initial interface."""
        self.users = AuthWindow.users
        self.current_user = None

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Login")
        self.root.geometry("400x550")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)

        self.setup_ui()
        self.show_login()

    def setup_ui(self):
        """Build the shared header and content area for authentication."""
        title_frame = tk.Frame(self.root, bg=COLORS["accent"], height=100)
        title_frame.pack(fill="x")

        logo_canvas = tk.Canvas(
            title_frame,
            width=60,
            height=60,
            bg=COLORS["accent"],
            highlightthickness=0
        )
        logo_canvas.pack(pady=(15, 0))
        draw_logo(logo_canvas, 30, 30, size=30, color="white")

        tk.Label(
            title_frame,
            text=APP_NAME,
            font=(FONT_FAMILY, 18, "bold"),
            fg=COLORS["text_white"],
            bg=COLORS["accent"]
        ).pack(pady=(2, 0))

        tk.Label(
            title_frame,
            text="Study Scheduler",
            font=(FONT_FAMILY, 9),
            fg=COLORS["text_white"],
            bg=COLORS["accent"]
        ).pack(pady=(0, 8))

        self.container = tk.Frame(self.root, bg=COLORS["bg"])
        self.container.pack(fill="both", expand=True, padx=30, pady=10)

    def clear_container(self):
        """Remove all widgets from the authentication content area."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        """Display the login form and its event bindings."""
        self.clear_container()

        tk.Label(
            self.container,
            text="Welcome Back!",
            font=(FONT_FAMILY, 18, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"]
        ).pack(pady=(10, 20))

        tk.Label(
            self.container,
            text="Username",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.login_username = tk.Entry(
            self.container,
            font=(FONT_FAMILY, 12),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.login_username.pack(fill="x", pady=(0, 15))

        tk.Label(
            self.container,
            text="Password",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.login_password = tk.Entry(
            self.container,
            font=(FONT_FAMILY, 12),
            show="●",
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.login_password.pack(fill="x", pady=(0, 20))
        self.login_password.bind("<Return>", lambda e: self.do_login())

        AppButton(
            self.container,
            text="LOGIN",
            command=self.do_login,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 12, "bold"),
            relief="solid",
            cursor="hand2",
            height=2
        ).pack(fill="x", pady=(0, 15))

        link = tk.Label(
            self.container,
            text="Don't have an account? Sign up",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["accent_light"],
            cursor="hand2"
        )
        link.pack()
        link.bind("<Button-1>", lambda e: self.show_signup())

    def show_signup(self):
        """Display the account-creation form and navigation link."""
        self.clear_container()

        tk.Label(
            self.container,
            text="Create Account",
            font=(FONT_FAMILY, 18, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"]
        ).pack(pady=(10, 20))

        tk.Label(
            self.container,
            text=f"Username (min {MIN_USERNAME_LENGTH} characters)",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.signup_username = tk.Entry(
            self.container,
            font=(FONT_FAMILY, 12),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.signup_username.pack(fill="x", pady=(0, 15))

        tk.Label(
            self.container,
            text=f"Password (min {MIN_PASSWORD_LENGTH} characters)",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.signup_password = tk.Entry(
            self.container,
            font=(FONT_FAMILY, 12),
            show="●",
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.signup_password.pack(fill="x", pady=(0, 15))

        tk.Label(
            self.container,
            text="Confirm Password",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.signup_confirm = tk.Entry(
            self.container,
            font=(FONT_FAMILY, 12),
            show="●",
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.signup_confirm.pack(fill="x", pady=(0, 20))
        self.signup_confirm.bind("<Return>", lambda e: self.do_signup())

        AppButton(
            self.container,
            text="CREATE ACCOUNT",
            command=self.do_signup,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 12, "bold"),
            relief="solid",
            cursor="hand2",
            height=2
        ).pack(fill="x", pady=(0, 15))

        link = tk.Label(
            self.container,
            text="Already have an account? Login",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["accent_light"],
            cursor="hand2"
        )
        link.pack()
        link.bind("<Button-1>", lambda e: self.show_login())

    def do_login(self):
        """Validate login details and open the authenticated application."""
        username = self.login_username.get().strip()
        password = self.login_password.get()

        if not username or not password:
            messagebox.showerror(
                "Error",
                "Please enter username and password.",
            )
            return
        if username not in self.users:
            messagebox.showerror("Error", "User not found.")
            return

        user = self.users[username]
        if not user.check_password(password):
            messagebox.showerror("Error", "Incorrect password.")
            return

        global COLORS
        if user.theme == "dark":
            COLORS = DARK_THEME.copy()
        else:
            COLORS = LIGHT_THEME.copy()

        self.current_user = user
        self.root.destroy()
        self.open_main_app()

    def do_signup(self):
        """Validate registration details and create a new user account."""
        username = self.signup_username.get().strip()
        password = self.signup_password.get()
        confirm = self.signup_confirm.get()

        if len(username) < MIN_USERNAME_LENGTH:
            messagebox.showerror(
                "Error",
                f"Username must be at least "
                f"{MIN_USERNAME_LENGTH} characters.",
            )
            return
        if username in self.users:
            messagebox.showerror("Error", "Username already exists.")
            return
        if len(password) < MIN_PASSWORD_LENGTH:
            messagebox.showerror(
                "Error",
                f"Password must be at least "
                f"{MIN_PASSWORD_LENGTH} characters.",
            )
            return
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.users[username] = User(username, password_hash)
        DataManager.save_users(self.users)

        messagebox.showinfo(
            "Success",
            f"Account '{username}' created successfully! Please login.",
        )
        self.show_login()

    def open_main_app(self):
        """Create and run the main StudyMate window for the current user."""
        app = MainApp(self.current_user)
        app.run()

    def run(self):
        """Start the Tkinter event loop for the authentication window."""
        self.root.mainloop()


class MainApp:
    """Build the StudyMate GUI and connect user actions to program logic."""
    def __init__(self, user):
        """Initialise application state, the main window and all tabs."""
        self.user = user
        self.pomodoro_running = False
        self.pomodoro_remaining = self.user.work_minutes * SECONDS_PER_MINUTE
        self.pomodoro_is_work = True
        self.pomodoro_timer_id = None

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - {user.username}")
        self.root.geometry("950x850")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(850, 750)

        # Create the theme variable after the Tk root so it has the
        # correct master.
        self.theme_var = tk.BooleanVar(
            master=self.root,
            value=(self.user.theme == "dark"),
        )

        self.apply_ttk_style()
        self.setup_ui()

        self.root.after(100, self.update_display)

    def apply_ttk_style(self):
        """Apply shared ttk styles for tabs, inputs and tables."""
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TNotebook.Tab",
            foreground=COLORS["tab_fg"],
            background=COLORS["frame_bg"],
            font=(FONT_FAMILY, 10),
            padding=(12, 7),
        )
        style.map(
            "TNotebook.Tab",
            foreground=[("selected", COLORS["accent"])],
            background=[("selected", COLORS["card_bg"])],
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["entry_bg"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["accent"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["entry_bg"])],
            foreground=[("readonly", COLORS["text"])],
        )
        style.configure(
            "TSpinbox",
            fieldbackground=COLORS["entry_bg"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["accent"],
        )
        style.configure(
            "Treeview",
            background=COLORS["entry_bg"],
            fieldbackground=COLORS["entry_bg"],
            foreground=COLORS["text"],
            rowheight=28,
            font=(FONT_FAMILY, 10),
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["accent"],
            foreground="#ffffff",
            font=(FONT_FAMILY, 10, "bold"),
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["accent_light"])],
            foreground=[("selected", "#ffffff")],
        )

    def create_card(self, parent, title):
        """Create and return a reusable labelled card container."""
        card = tk.Frame(parent, bg=COLORS["card_bg"], relief="ridge", bd=1)
        card.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Label(
            card,
            text=title,
            font=(FONT_FAMILY, 12, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["card_bg"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        content = tk.Frame(card, bg=COLORS["card_bg"])
        content.pack(fill="both", expand=True, padx=10, pady=5)
        return content

    def setup_ui(self):
        """Build the title bar, notebook and main application tabs."""
        title_bar = tk.Frame(self.root, bg=COLORS["accent"], height=55)
        title_bar.pack(fill="x")

        logo_canvas = tk.Canvas(
            title_bar,
            width=35,
            height=35,
            bg=COLORS["accent"],
            highlightthickness=0
        )
        logo_canvas.pack(side="left", padx=(15, 5), pady=10)
        draw_logo(logo_canvas, 17, 17, size=22, color="white")

        tk.Label(
            title_bar,
            text=f"{APP_NAME} — {self.user.username}",
            font=(FONT_FAMILY, 16, "bold"),
            fg=COLORS["text_white"],
            bg=COLORS["accent"]
        ).pack(side="left", pady=10)

        # Use the shared AppButton style for consistent buttons.
        AppButton(
            title_bar,
            text="Logout",
            command=self.logout,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 10),
            relief="solid",
            cursor="hand2"
        ).pack(side="right", padx=20, pady=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.dashboard_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.setup_dashboard()

        self.plan_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.plan_frame, text="Plan")
        self.setup_plan_tab()

        self.progress_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.progress_frame, text="Progress")
        self.setup_progress_tab()

        self.focus_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.focus_frame, text="Focus")
        self.setup_focus_tab()

        # Tasks tab.
        self.tasks_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.tasks_frame, text="Tasks")
        self.setup_tasks_tab()

        self.settings_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()

    # ==========================================
    # DASHBOARD
    # ==========================================
    def setup_dashboard(self):
        """Build the subject-management controls and subject table."""
        frame = self.dashboard_frame

        self.deadline_frame = tk.Frame(frame, bg=COLORS["bg"])
        self.deadline_frame.pack(fill="x", padx=10, pady=(10, 0))

        self.deadline_label = tk.Label(
            self.deadline_frame,
            text="",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            wraplength=820,
            justify="left",
        )
        self.deadline_label.pack(anchor="w")

        top_frame = tk.Frame(frame, bg=COLORS["bg"])
        top_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = tk.Frame(top_frame, bg=COLORS["bg"])
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        add_card = self.create_card(left_frame, "Add Subject")

        tk.Label(
            add_card,
            text="Subject Name:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(5, 0))
        self.name_entry = tk.Entry(
            add_card,
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.name_entry.pack(fill="x", pady=(0, 10))

        tk.Label(
            add_card,
            text="Weekly target hours (per 7 days):",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(5, 0))
        self.hours_var = tk.StringVar(value=str(DEFAULT_SUBJECT_HOURS))
        self.hours_entry = ttk.Spinbox(
            add_card,
            from_=0,
            to=24,
            increment=0.5,
            textvariable=self.hours_var,
            width=12,
            font=(FONT_FAMILY, 11),
        )
        self.hours_entry.pack(fill="x", pady=(0, 10))

        tk.Label(
            add_card,
            text="Priority:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(5, 0))
        self.priority_var = tk.StringVar(value="Medium")
        priority_menu = ttk.Combobox(
            add_card,
            textvariable=self.priority_var,
            values=User.PRIORITIES,
            state="readonly",
            font=(FONT_FAMILY, 11),
        )
        priority_menu.pack(fill="x", pady=(0, 10))

        tk.Label(
            add_card,
            text="Deadline (DD/MM/YYYY, optional):",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(5, 0))
        self.deadline_entry = tk.Entry(
            add_card,
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.deadline_entry.pack(fill="x", pady=(0, 10))

        tk.Label(
            add_card,
            text="Target Grade (optional):",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
        ).pack(anchor="w", pady=(5, 0))
        self.grade_entry = tk.Entry(
            add_card,
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.grade_entry.pack(fill="x", pady=(0, 8))

        tk.Label(
            add_card,
            text=(
                "Weekly target hours are the total you want to "
                "study in a 7-day period. "
                "Priority and nearby deadlines matter when "
                "available time is limited."
            ),
            bg=COLORS["card_bg"],
            fg=COLORS["text_light"],
            font=(FONT_FAMILY, 9),
            wraplength=250,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        AppButton(
            add_card,
            text="Add Subject",
            command=self.add_subject,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 11, "bold"),
        ).pack(fill="x")

        right_frame = tk.Frame(top_frame, bg=COLORS["bg"])
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        list_card = self.create_card(right_frame, "My Subjects")

        subject_columns = (
            "Subject",
            "Weekly Hours",
            "Priority",
            "Deadline",
            "Target Grade",
        )
        self.subject_tree = ttk.Treeview(
            list_card,
            columns=subject_columns,
            show="headings",
            height=14,
        )
        for column in subject_columns:
            self.subject_tree.heading(column, text=column)
        self.subject_tree.column("Subject", width=170, anchor="w")
        self.subject_tree.column("Weekly Hours", width=100, anchor="center")
        self.subject_tree.column("Priority", width=90, anchor="center")
        self.subject_tree.column("Deadline", width=110, anchor="center")
        self.subject_tree.column("Target Grade", width=100, anchor="center")

        subject_scrollbar = ttk.Scrollbar(
            list_card,
            orient="vertical",
            command=self.subject_tree.yview,
        )
        self.subject_tree.configure(yscrollcommand=subject_scrollbar.set)
        self.subject_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 0),
            pady=5,
        )
        subject_scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)

        btn_frame = tk.Frame(right_frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", pady=(0, 5))
        AppButton(
            btn_frame,
            text="Delete Selected Subject",
            command=self.delete_subject,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 10),
        ).pack(side="left", padx=5)
        AppButton(
            btn_frame,
            text="Clear All Subjects",
            command=self.clear_all_subjects,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 10),
        ).pack(side="left", padx=5)

    def add_subject(self):
        """Read dashboard inputs and add a validated subject."""
        name = self.name_entry.get().strip()
        hours_str = self.hours_var.get().strip()
        priority = self.priority_var.get()
        deadline = self.deadline_entry.get().strip() or None
        grade = self.grade_entry.get().strip()

        try:
            hours = parse_number(
                hours_str,
                "Weekly Target Hours",
                minimum=MIN_HOURS,
                maximum=MAX_HOURS_PER_DAY,
            )
            saved_name = self.user.add_subject(
                name,
                hours,
                priority,
                deadline,
                goal_hours=None,
                target_grade=grade,
            )
            DataManager.save_users(AuthWindow.users)
            self.update_display()
            self.name_entry.delete(0, tk.END)
            self.hours_var.set(str(DEFAULT_SUBJECT_HOURS))
            self.priority_var.set("Medium")
            self.deadline_entry.delete(0, tk.END)
            self.grade_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Added '{saved_name}'")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def update_deadline_alert(self):
        """Refresh the dashboard message for upcoming deadlines."""
        if not self.user.subjects:
            self.deadline_label.config(text="", bg=COLORS["bg"])
            return

        upcoming = []
        today = datetime.now()

        for name, data in self.user.subjects.items():
            if data.get("deadline"):
                try:
                    deadline_date = datetime.strptime(
                        data["deadline"],
                        DATE_FORMAT,
                    )
                    days_left = (deadline_date - today).days
                    if 0 <= days_left <= NEAR_DEADLINE_DAYS:
                        upcoming.append((name, days_left))
                    elif days_left < 0:
                        upcoming.append((name, -1))
                except ValueError:
                    pass

        if not upcoming:
            self.deadline_label.config(
                text="✅ No upcoming deadlines in the next 7 days.",
                fg=COLORS["success"],
                bg=COLORS["bg"]
            )
            return

        upcoming.sort(key=lambda x: x[1])
        messages = []
        for name, days_left in upcoming:
            if days_left < 0:
                messages.append(f"⚠️ {name} - OVERDUE!")
            elif days_left == 0:
                messages.append(f"🔴 {name} - DUE TODAY!")
            elif days_left <= 3:
                messages.append(f"🔴 {name} - due in {days_left} day(s)")
            else:
                messages.append(f"🟡 {name} - due in {days_left} day(s)")

        alert_text = "📅 Upcoming Deadlines: " + " | ".join(messages)
        self.deadline_label.config(
            text=alert_text,
            fg=COLORS["delete"],
            bg=COLORS["bg"],
        )

    def update_display(self):
        """Refresh all data-driven views after user data changes."""
        self.plan_display.config(fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.weekly_plan_display.config(
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.chart_canvas.config(bg=COLORS["entry_bg"])

        self.update_deadline_alert()

        for item in self.subject_tree.get_children():
            self.subject_tree.delete(item)
        if not self.user.subjects:
            self.subject_tree.insert(
                "",
                "end",
                values=("No subjects yet", "", "", "", ""),
                tags=("placeholder",),
            )
        else:
            for name, data in self.user.subjects.items():
                self.subject_tree.insert(
                    "",
                    "end",
                    values=(
                        name,
                        f"{data['hours']:g}",
                        data["priority"],
                        data.get("deadline") or "-",
                        data.get("target_grade") or "-",
                    ),
                )
        self.subject_tree.tag_configure(
            "placeholder",
            foreground=COLORS["text_light"],
        )

        self.update_progress_tab()
        self.update_stats()
        self.update_pomodoro_stats()
        self.update_tasks_display()

    def delete_subject(self):
        """Delete the currently selected subject after confirmation."""
        selected = self.subject_tree.selection()
        if not selected or not self.user.subjects:
            messagebox.showwarning(
                "No Selection",
                "Select a subject from the table first.",
            )
            return
        values = self.subject_tree.item(selected[0], "values")
        if not values or values[0] not in self.user.subjects:
            messagebox.showwarning(
                "No Selection",
                "Select a valid subject first.",
            )
            return
        subject_name = values[0]
        if messagebox.askyesno("Confirm", f"Delete '{subject_name}'?"):
            self.user.delete_subject(subject_name)
            DataManager.save_users(AuthWindow.users)
            self.update_display()

    def clear_all_subjects(self):
        """Clear all subjects, study logs and task subject links."""
        if not self.user.subjects:
            messagebox.showinfo("Info", "No subjects to clear.")
            return
        if messagebox.askyesno(
            "Confirm",
            "Delete ALL subjects and their study logs?",
        ):
            self.user.subjects = {}
            self.user.logs = {}
            for task in self.user.tasks:
                task["subject"] = None
            DataManager.save_users(AuthWindow.users)
            self.update_display()

    # ==========================================
    # PLAN TAB
    # ==========================================
    def setup_plan_tab(self):
        """Build daily and weekly planning controls and output areas."""
        frame = self.plan_frame

        explanation = tk.Label(
            frame,
            text=(
                "How allocation works: weekly target hours are totals "
                "for each 7-day period, "
                "not hours repeated every day. The weekly planner "
                "will not schedule "
                "more than those targets. Priority and deadlines "
                "decide which hours "
                "are protected when capacity is limited, and urgent "
                "sessions are placed "
                "before their deadlines where possible. Use the scrollbars "
                "to view longer plans."
            ),
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["text_light"],
            justify="left",
            wraplength=820,
        )
        explanation.pack(fill="x", padx=15, pady=(10, 0))

        daily_card = self.create_card(frame, "Generate Today's Plan")
        row = tk.Frame(daily_card, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=5)
        tk.Label(
            row,
            text="Available study hours today:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left")
        self.daily_hours_var = tk.StringVar(value=str(DEFAULT_PLAN_HOURS))
        self.daily_hours_spin = ttk.Spinbox(
            row,
            from_=0.5,
            to=24,
            increment=0.5,
            textvariable=self.daily_hours_var,
            width=8,
            font=(FONT_FAMILY, 11),
        )
        self.daily_hours_spin.pack(side="left", padx=10)
        AppButton(
            row,
            text="Generate Today's Plan",
            command=self.generate_today_plan,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 10, "bold"),
        ).pack(side="left", padx=10)

        daily_output_frame = tk.Frame(daily_card, bg=COLORS["card_bg"])
        daily_output_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.plan_display = tk.Text(
            daily_output_frame,
            height=8,
            font=(FONT_FAMILY, 10),
            bg=COLORS["entry_bg"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            wrap="word",
        )
        daily_scrollbar = ttk.Scrollbar(
            daily_output_frame,
            orient="vertical",
            command=self.plan_display.yview,
        )
        self.plan_display.configure(yscrollcommand=daily_scrollbar.set)
        self.plan_display.pack(side="left", fill="both", expand=True)
        daily_scrollbar.pack(side="right", fill="y")

        weekly_card = self.create_card(frame, "Generate Weekly Plan")
        control_frame = tk.Frame(weekly_card, bg=COLORS["card_bg"])
        control_frame.pack(fill="x", pady=5)

        tk.Label(
            control_frame,
            text="Maximum available hours per day:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left")
        self.weekly_hours_var = tk.StringVar(value=str(DEFAULT_PLAN_HOURS))
        self.weekly_hours_spin = ttk.Spinbox(
            control_frame,
            from_=0.5,
            to=24,
            increment=0.5,
            textvariable=self.weekly_hours_var,
            width=7,
            font=(FONT_FAMILY, 11),
        )
        self.weekly_hours_spin.pack(side="left", padx=(8, 15))

        tk.Label(
            control_frame,
            text="Number of days:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left")
        self.days_var = tk.StringVar(value="7")
        self.days_spin = ttk.Spinbox(
            control_frame,
            from_=1,
            to=MAX_PLAN_DAYS,
            increment=1,
            textvariable=self.days_var,
            width=5,
            font=(FONT_FAMILY, 11),
        )
        self.days_spin.pack(side="left", padx=(8, 15))

        AppButton(
            control_frame,
            text="Generate Weekly Plan",
            command=self.generate_weekly_plan,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 10, "bold"),
        ).pack(side="left", padx=5)
        AppButton(
            control_frame,
            text="Export Report",
            command=self.export_report,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 10, "bold"),
        ).pack(side="left", padx=5)

        weekly_output_frame = tk.Frame(weekly_card, bg=COLORS["card_bg"])
        weekly_output_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.weekly_plan_display = tk.Text(
            weekly_output_frame,
            height=12,
            font=(FONT_FAMILY, 10),
            bg=COLORS["entry_bg"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            wrap="word",
        )
        weekly_scrollbar = ttk.Scrollbar(
            weekly_output_frame,
            orient="vertical",
            command=self.weekly_plan_display.yview,
        )
        self.weekly_plan_display.configure(yscrollcommand=weekly_scrollbar.set)
        self.weekly_plan_display.pack(side="left", fill="both", expand=True)
        weekly_scrollbar.pack(side="right", fill="y")

    def generate_today_plan(self):
        """Validate daily capacity and display the generated plan."""
        avail_str = self.daily_hours_var.get().strip()
        try:
            available = parse_number(
                avail_str,
                "Available study hours today",
                minimum=0,
                maximum=MAX_HOURS_PER_DAY,
                minimum_inclusive=False,
            )
            plan = self.user.generate_daily_plan(available)
            if not plan:
                self.plan_display.delete(1.0, tk.END)
                self.plan_display.insert(
                    tk.END,
                    "No subjects added yet.",
                )
                return

            today = datetime.now().strftime(DATE_FORMAT)
            today_plan = plan.get(today, {})
            scheduled = round(sum(today_plan.values()), 1)
            unused = round(max(available - scheduled, 0.0), 1)

            self.plan_display.delete(1.0, tk.END)
            self.plan_display.insert(tk.END, "=" * 45 + "\n")
            self.plan_display.insert(
                tk.END,
                "       TODAY'S STUDY PLAN\n",
            )
            self.plan_display.insert(tk.END, "=" * 45 + "\n")
            self.plan_display.insert(
                tk.END,
                f"Available today: {available:g}h | "
                f"Scheduled: {scheduled:g}h | "
                f"Unused: {unused:g}h\n\n",
            )

            if not today_plan:
                self.plan_display.insert(
                    tk.END,
                    "No study time was scheduled.\n",
                )
            for name, hours in today_plan.items():
                bar_length = min(int(hours * 2), DAILY_PLAN_BAR_BLOCKS)
                bar = (
                    "█" * bar_length
                    + "░" * (DAILY_PLAN_BAR_BLOCKS - bar_length)
                )
                self.plan_display.insert(tk.END, f"  {name}\n")
                self.plan_display.insert(
                    tk.END,
                    f"  {bar} {hours:g} hour(s)\n\n",
                )
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def generate_weekly_plan(self):
        """Validate weekly inputs and display the generated schedule."""
        try:
            avail_str = self.weekly_hours_var.get().strip()
            max_hours_per_day = parse_number(
                avail_str,
                "Maximum available hours per day",
                minimum=0,
                maximum=MAX_HOURS_PER_DAY,
                minimum_inclusive=False,
            )
            days = parse_number(
                self.days_var.get(),
                "Number of days",
                minimum=1,
                maximum=MAX_PLAN_DAYS,
                integer=True,
            )

            plan, summary = self.user.generate_weekly_schedule(
                max_hours_per_day,
                days,
            )
            if not plan:
                self.weekly_plan_display.delete(1.0, tk.END)
                self.weekly_plan_display.insert(
                    tk.END,
                    "No subjects added yet.",
                )
                return

            self.weekly_plan_display.delete(1.0, tk.END)
            self.weekly_plan_display.insert(
                tk.END,
                "=" * 58 + "\n",
            )
            self.weekly_plan_display.insert(
                tk.END,
                "              MULTI-DAY STUDY PLAN\n",
            )
            self.weekly_plan_display.insert(
                tk.END,
                "=" * 58 + "\n",
            )
            self.weekly_plan_display.insert(
                tk.END,
                f"Period: {days} day(s) | Maximum capacity: "
                f"{summary['max_hours_per_day']:g}h/day × {days} = "
                f"{summary['total_capacity']:g}h\n",
            )
            self.weekly_plan_display.insert(
                tk.END,
                f"Target hours for this period: "
                f"{summary['total_desired']:g}h | "
                f"Scheduled: {summary['total_scheduled']:g}h | "
                f"Unused capacity: {summary['unused_capacity']:g}h\n",
            )
            if summary["capacity_limited"]:
                self.weekly_plan_display.insert(
                    tk.END,
                    f"Capacity is {summary['shortfall']:g}h below "
                    "the combined targets. Priority and deadline urgency "
                    "were used to protect the most important hours.\n",
                )
            else:
                self.weekly_plan_display.insert(
                    tk.END,
                    "All target hours fit within the available capacity.\n",
                )

            self.weekly_plan_display.insert(
                tk.END,
                "\nSUBJECT TOTALS\n",
            )
            self.weekly_plan_display.insert(
                tk.END,
                "-" * 58 + "\n",
            )
            for name in summary["desired_by_subject"]:
                desired = summary["desired_by_subject"][name]
                scheduled = summary["scheduled_by_subject"].get(
                    name,
                    0.0,
                )
                self.weekly_plan_display.insert(
                    tk.END,
                    f"{name}: {scheduled:g}h scheduled / "
                    f"{desired:g}h target\n",
                )

            self.weekly_plan_display.insert(
                tk.END,
                "\nDAILY SCHEDULE\n",
            )
            self.weekly_plan_display.insert(
                tk.END,
                "-" * 58 + "\n",
            )
            for date, daily_plan in plan.items():
                date_obj = datetime.strptime(date, DATE_FORMAT)
                day_name = date_obj.strftime("%A")
                daily_total = round(sum(daily_plan.values()), 1)
                self.weekly_plan_display.insert(
                    tk.END,
                    f"{day_name} ({date}) — {daily_total:g}h\n",
                )
                if not daily_plan:
                    self.weekly_plan_display.insert(
                        tk.END,
                        "   No study scheduled\n",
                    )
                else:
                    for name, hours in daily_plan.items():
                        bar_length = min(
                            int(hours * 4),
                            WEEKLY_PLAN_BAR_BLOCKS,
                        )
                        bar = (
                            "█" * bar_length
                            + "░" * (WEEKLY_PLAN_BAR_BLOCKS - bar_length)
                        )
                        self.weekly_plan_display.insert(
                            tk.END,
                            f"   {name}: {bar} {hours:g}h\n",
                        )
                self.weekly_plan_display.insert(tk.END, "\n")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def export_report(self):
        """Generate the weekly plan and save it as a text report."""
        try:
            avail_str = self.weekly_hours_var.get().strip()
            max_hours_per_day = parse_number(
                avail_str,
                "Maximum available hours per day",
                minimum=0,
                maximum=MAX_HOURS_PER_DAY,
                minimum_inclusive=False,
            )
            days = parse_number(
                self.days_var.get(),
                "Number of days",
                minimum=1,
                maximum=MAX_PLAN_DAYS,
                integer=True,
            )
            plan, summary = self.user.generate_weekly_schedule(
                max_hours_per_day,
                days,
            )

            if not plan:
                messagebox.showerror(
                    "Error",
                    "No subjects added yet.",
                )
                return

            from pathlib import Path
            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                desktop = Path.cwd()
            filename = desktop / (
                "study_plan_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            with open(filename, "w", encoding="utf-8") as f:
                f.write("=" * 58 + "\n")
                f.write(f"STUDY PLAN - {self.user.username}\n")
                f.write(
                    "Generated: "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                )
                f.write("=" * 58 + "\n\n")
                f.write(
                    f"Period: {days} day(s)\n"
                    f"Maximum capacity: "
                    f"{summary['max_hours_per_day']:g}h/day "
                    f"({summary['total_capacity']:g}h total)\n"
                    f"Target hours: {summary['total_desired']:g}h\n"
                    f"Scheduled hours: "
                    f"{summary['total_scheduled']:g}h\n"
                    f"Unused capacity: "
                    f"{summary['unused_capacity']:g}h\n"
                    f"Shortfall: {summary['shortfall']:g}h\n\n"
                )

                f.write("SUBJECT TOTALS\n")
                f.write("-" * 58 + "\n")
                for name in summary["desired_by_subject"]:
                    desired = summary["desired_by_subject"][name]
                    scheduled = summary["scheduled_by_subject"].get(
                        name,
                        0.0,
                    )
                    f.write(
                        f"{name}: {scheduled:g}h / "
                        f"{desired:g}h target\n"
                    )

                f.write("\nDAILY SCHEDULE\n")
                f.write("-" * 58 + "\n")
                for date, daily_plan in plan.items():
                    daily_total = round(sum(daily_plan.values()), 1)
                    f.write(f"{date} — {daily_total:g}h\n")
                    if not daily_plan:
                        f.write("  No study scheduled\n")
                    else:
                        for name, hours in daily_plan.items():
                            f.write(f"  {name}: {hours:g}h\n")
                    f.write("\n")

            messagebox.showinfo(
                "Success",
                f"Report saved to {filename}",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==========================================
    # PROGRESS TAB
    # ==========================================
    def setup_progress_tab(self):
        """Build study-log controls, progress table and comparison chart."""
        frame = self.progress_frame

        explanation = tk.Label(
            frame,
            text=(
                "Use this page after studying: record the time you "
                "actually completed. "
                "StudyMate compares this week's logged time with "
                "the desired weekly "
                "hours entered on the Dashboard."
            ),
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["text_light"],
            justify="left",
            wraplength=820,
        )
        explanation.pack(fill="x", padx=15, pady=(10, 0))

        log_card = self.create_card(frame, "Log Actual Study Time")
        row = tk.Frame(log_card, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=5)

        tk.Label(
            row,
            text="Date:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left")
        self.log_date_entry = tk.Entry(
            row,
            width=12,
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.log_date_entry.pack(side="left", padx=5)
        self.log_date_entry.insert(0, datetime.now().strftime(DATE_FORMAT))

        tk.Label(
            row,
            text="Subject:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left", padx=(10, 0))
        self.log_subject_var = tk.StringVar()
        self.log_subject_menu = ttk.Combobox(
            row,
            textvariable=self.log_subject_var,
            values=list(self.user.subjects.keys()),
            state="readonly",
            width=15,
        )
        self.log_subject_menu.pack(side="left", padx=5)

        tk.Label(
            row,
            text="Hours completed:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left", padx=(10, 0))
        self.log_hours_var = tk.StringVar(value="0.5")
        self.log_hours_spin = ttk.Spinbox(
            row,
            from_=0.25,
            to=24,
            increment=0.25,
            textvariable=self.log_hours_var,
            width=7,
            font=(FONT_FAMILY, 11),
        )
        self.log_hours_spin.pack(side="left", padx=5)

        AppButton(
            row,
            text="Log Time",
            command=self.log_study_time,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 10, "bold"),
        ).pack(side="left", padx=10)

        summary_card = self.create_card(frame, "This Week's Progress")
        self.week_range_label = tk.Label(
            summary_card,
            text="",
            font=(FONT_FAMILY, 10, "bold"),
            bg=COLORS["card_bg"],
            fg=COLORS["accent"],
            anchor="w",
        )
        self.week_range_label.pack(fill="x", pady=(0, 4))

        self.overall_progress_label = tk.Label(
            summary_card,
            text="",
            font=(FONT_FAMILY, 10),
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            anchor="w",
            justify="left",
        )
        self.overall_progress_label.pack(fill="x", pady=(0, 8))

        progress_table_frame = tk.Frame(summary_card, bg=COLORS["card_bg"])
        progress_table_frame.pack(fill="both", expand=True)
        progress_columns = (
            "Subject",
            "Desired This Week",
            "Logged This Week",
            "Remaining",
            "Completion",
        )
        self.progress_tree = ttk.Treeview(
            progress_table_frame,
            columns=progress_columns,
            show="headings",
            height=6,
        )
        for column in progress_columns:
            self.progress_tree.heading(column, text=column)
        self.progress_tree.column("Subject", width=170, anchor="w")
        self.progress_tree.column(
            "Desired This Week",
            width=125,
            anchor="center",
        )
        self.progress_tree.column(
            "Logged This Week",
            width=120,
            anchor="center",
        )
        self.progress_tree.column("Remaining", width=90, anchor="center")
        self.progress_tree.column("Completion", width=90, anchor="center")

        progress_scrollbar = ttk.Scrollbar(
            progress_table_frame,
            orient="vertical",
            command=self.progress_tree.yview,
        )
        self.progress_tree.configure(yscrollcommand=progress_scrollbar.set)
        self.progress_tree.pack(side="left", fill="both", expand=True)
        progress_scrollbar.pack(side="right", fill="y")

        chart_card = self.create_card(frame, "Desired vs Logged This Week")
        legend = tk.Frame(chart_card, bg=COLORS["card_bg"])
        legend.pack(fill="x", pady=(0, 3))
        tk.Label(
            legend,
            text="■ Desired weekly hours",
            fg=COLORS["accent_light"],
            bg=COLORS["card_bg"],
            font=(FONT_FAMILY, 9),
        ).pack(side="left", padx=(0, 15))
        tk.Label(
            legend,
            text="■ Logged this week",
            fg=COLORS["accent"],
            bg=COLORS["card_bg"],
            font=(FONT_FAMILY, 9),
        ).pack(side="left")

        self.chart_canvas = tk.Canvas(
            chart_card,
            height=190,
            bg=COLORS["entry_bg"],
            relief="flat",
            bd=0,
        )
        self.chart_canvas.pack(fill="both", expand=True, pady=(2, 0))

    def update_progress_tab(self):
        """Refresh the subject choices available for study logging."""
        subjects = list(self.user.subjects.keys())
        self.log_subject_menu["values"] = subjects
        if not subjects:
            self.log_subject_var.set("")
        elif self.log_subject_var.get() not in subjects:
            self.log_subject_var.set(subjects[0])

    def log_study_time(self):
        """Validate progress inputs and save a study-time entry."""
        date = self.log_date_entry.get().strip()
        subject = self.log_subject_var.get()
        hours_str = self.log_hours_var.get().strip()

        if not subject:
            messagebox.showerror("Error", "Please select a subject.")
            return

        try:
            hours = parse_number(
                hours_str,
                "Hours completed",
                minimum=0,
                maximum=MAX_HOURS_PER_DAY,
                minimum_inclusive=False,
            )
            self.user.log_study_time(date, subject, hours)
            DataManager.save_users(AuthWindow.users)
            self.log_hours_var.set("0.5")
            self.update_stats()
            messagebox.showinfo(
                "Success",
                f"Logged {hours:g}h for {subject} on {date}",
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def update_stats(self):
        """Recalculate and display the current week progress summary."""
        for item in self.progress_tree.get_children():
            self.progress_tree.delete(item)

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        self.week_range_label.config(
            text=(
                f"Current week: {week_start.strftime(DATE_FORMAT)} "
                f"to {week_end.strftime(DATE_FORMAT)}"
            )
        )

        if not self.user.subjects:
            self.overall_progress_label.config(
                text="Add subjects on the Dashboard, then log study time here."
            )
            self.progress_tree.insert(
                "",
                "end",
                values=("No subjects yet", "", "", "", ""),
                tags=("placeholder",),
            )
            self.progress_tree.tag_configure(
                "placeholder",
                foreground=COLORS["text_light"],
            )
            self.draw_chart({}, {})
            return

        planned_by_subject = {
            name: float(data["hours"])
            for name, data in self.user.subjects.items()
        }
        logged_by_subject = self.user.get_logged_hours_by_subject(
            start_date=week_start,
            end_date=week_end,
        )

        total_planned = sum(planned_by_subject.values())
        total_logged = sum(logged_by_subject.values())
        total_remaining = max(total_planned - total_logged, 0.0)
        completion = (
            total_logged / total_planned * 100
            if total_planned
            else 0.0
        )

        self.overall_progress_label.config(
            text=(
                f"Desired: {total_planned:.1f}h   |   "
                f"Logged: {total_logged:.1f}h   |   "
                f"Remaining: {total_remaining:.1f}h   |   "
                f"Completion: {completion:.0f}%"
            )
        )

        for name, planned in planned_by_subject.items():
            logged = logged_by_subject.get(name, 0.0)
            remaining = max(planned - logged, 0.0)
            subject_completion = (logged / planned * 100) if planned else 0.0
            self.progress_tree.insert(
                "",
                "end",
                values=(
                    name,
                    f"{planned:.1f}h",
                    f"{logged:.1f}h",
                    f"{remaining:.1f}h",
                    f"{subject_completion:.0f}%",
                ),
            )

        self.draw_chart(planned_by_subject, logged_by_subject)

    def draw_chart(self, planned_by_subject, logged_by_subject):
        """Draw desired and logged weekly hours on the progress canvas."""
        canvas = self.chart_canvas
        canvas.delete("all")

        if not planned_by_subject:
            canvas.create_text(
                280,
                90,
                text="Add subjects and log study time to see a comparison.",
                fill=COLORS["text_light"],
                font=(FONT_FAMILY, 10),
            )
            return

        width = canvas.winfo_width() if canvas.winfo_width() > 100 else 800
        height = canvas.winfo_height() if canvas.winfo_height() > 50 else 190
        names = list(planned_by_subject.keys())
        num_items = len(names)
        max_value = max(
            [1.0]
            + list(planned_by_subject.values())
            + list(logged_by_subject.values())
        )

        left_margin = 35
        right_margin = 20
        top_margin = 20
        bottom_margin = 35
        chart_height = max(height - top_margin - bottom_margin, 40)
        available_width = max(width - left_margin - right_margin, 120)
        group_width = available_width / max(num_items, 1)
        bar_width = max(min(group_width * 0.28, 32), 10)

        baseline = height - bottom_margin
        canvas.create_line(
            left_margin,
            baseline,
            width - right_margin,
            baseline,
            fill=COLORS["text_light"],
        )

        for index, name in enumerate(names):
            group_center = left_margin + group_width * (index + 0.5)
            planned = planned_by_subject[name]
            logged = logged_by_subject.get(name, 0.0)
            planned_height = (planned / max_value) * chart_height
            logged_height = (logged / max_value) * chart_height

            planned_x1 = group_center - bar_width - 2
            planned_x2 = group_center - 2
            logged_x1 = group_center + 2
            logged_x2 = group_center + bar_width + 2

            canvas.create_rectangle(
                planned_x1,
                baseline - planned_height,
                planned_x2,
                baseline,
                fill=COLORS["accent_light"],
                outline="",
            )
            canvas.create_rectangle(
                logged_x1,
                baseline - logged_height,
                logged_x2,
                baseline,
                fill=COLORS["accent"],
                outline="",
            )

            canvas.create_text(
                (planned_x1 + planned_x2) / 2,
                baseline - planned_height - 8,
                text=f"{planned:.1f}",
                font=(FONT_FAMILY, 8),
                fill=COLORS["text"],
            )
            canvas.create_text(
                (logged_x1 + logged_x2) / 2,
                baseline - logged_height - 8,
                text=f"{logged:.1f}",
                font=(FONT_FAMILY, 8),
                fill=COLORS["text"],
            )

            display_name = name[:9] + ".." if len(name) > 11 else name
            canvas.create_text(
                group_center,
                baseline + 14,
                text=display_name,
                font=(FONT_FAMILY, 8),
                fill=COLORS["text"],
            )

    # ==========================================
    # FOCUS TAB
    # ==========================================
    def setup_focus_tab(self):
        """Build Pomodoro settings, controls, timer and focus statistics."""
        frame = self.focus_frame

        timer_card = self.create_card(frame, "Pomodoro Timer")

        settings_row = tk.Frame(timer_card, bg=COLORS["card_bg"])
        settings_row.pack(pady=10)

        tk.Label(
            settings_row,
            text="Work (min):",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left", padx=5)
        self.work_min_entry = tk.Entry(
            settings_row,
            width=5,
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.work_min_entry.pack(side="left", padx=5)
        self.work_min_entry.insert(0, str(self.user.work_minutes))

        tk.Label(
            settings_row,
            text="Break (min):",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left", padx=10)
        self.break_min_entry = tk.Entry(
            settings_row,
            width=5,
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.break_min_entry.pack(side="left", padx=5)
        self.break_min_entry.insert(0, str(self.user.break_minutes))

        AppButton(
            settings_row,
            text="Apply",
            command=self.apply_timer_settings,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 10, "bold"),
            relief="solid",
            cursor="hand2"
        ).pack(side="left", padx=10)

        self.timer_label = tk.Label(
            timer_card,
            text=f"{self.user.work_minutes:02d}:00",
            font=(FONT_FAMILY, 64, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["card_bg"]
        )
        self.timer_label.pack(pady=10)

        self.timer_status = tk.Label(
            timer_card,
            text="Work Time",
            font=(FONT_FAMILY, 14),
            fg=COLORS["text"],
            bg=COLORS["card_bg"]
        )
        self.timer_status.pack(pady=5)

        self.progress_label = tk.Label(
            timer_card,
            text="████████░░░░░░░░░░",
            font=(FONT_FAMILY, 14),
            fg=COLORS["accent"],
            bg=COLORS["card_bg"]
        )
        self.progress_label.pack(pady=5)

        btn_row = tk.Frame(timer_card, bg=COLORS["card_bg"])
        btn_row.pack(pady=15)

        self.start_btn = AppButton(
            btn_row,
            text="Start",
            command=self.start_pomodoro,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 11, "bold"),
            relief="solid",
            cursor="hand2",
            padx=20,
            pady=5
        )
        self.start_btn.pack(side="left", padx=5)

        self.pause_btn = AppButton(
            btn_row,
            text="Pause",
            command=self.pause_pomodoro,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 11, "bold"),
            relief="solid",
            cursor="hand2",
            padx=20,
            pady=5
        )
        self.pause_btn.pack(side="left", padx=5)
        self.pause_btn.config(state="disabled")

        self.reset_btn = AppButton(
            btn_row,
            text="Reset",
            command=self.reset_pomodoro,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 11, "bold"),
            relief="solid",
            cursor="hand2",
            padx=20,
            pady=5
        )
        self.reset_btn.pack(side="left", padx=5)

        stats_card = self.create_card(frame, "Focus Stats")

        row = tk.Frame(stats_card, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=5)
        tk.Label(
            row,
            text="Pomodoros Today:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left")
        self.pomodoro_count_label = tk.Label(
            row,
            text="0",
            bg=COLORS["card_bg"],
            fg=COLORS["accent"],
            font=(FONT_FAMILY, 14, "bold"),
        )
        self.pomodoro_count_label.pack(side="left", padx=10)

        row2 = tk.Frame(stats_card, bg=COLORS["card_bg"])
        row2.pack(fill="x", pady=5)
        tk.Label(
            row2,
            text="Focus Time Today:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 11),
        ).pack(side="left")
        self.focus_time_label = tk.Label(
            row2,
            text="0 min",
            bg=COLORS["card_bg"],
            fg=COLORS["accent"],
            font=(FONT_FAMILY, 14, "bold"),
        )
        self.focus_time_label.pack(side="left", padx=10)

    def apply_timer_settings(self):
        """Validate and apply Pomodoro work and break durations."""
        try:
            work = parse_number(
                self.work_min_entry.get(),
                "Work minutes",
                minimum=0,
                integer=True,
                minimum_inclusive=False,
            )
            break_min = parse_number(
                self.break_min_entry.get(),
                "Break minutes",
                minimum=0,
                integer=True,
            )
            self.user.work_minutes = work
            self.user.break_minutes = break_min
            self.pomodoro_remaining = work * SECONDS_PER_MINUTE
            self.pomodoro_is_work = True
            self.timer_label.config(text=f"{work:02d}:00")
            self.timer_status.config(text="Work Time")
            self.progress_label.config(text="████████░░░░░░░░░░")
            DataManager.save_users(AuthWindow.users)
            messagebox.showinfo(
                "Success",
                f"Timer set: {work} min work, {break_min} min break",
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def update_pomodoro_stats(self):
        """Refresh the displayed Pomodoro count and focus minutes."""
        self.pomodoro_count_label.config(text=str(self.user.pomodoro_count))
        self.focus_time_label.config(text=f"{self.user.focus_time_today} min")

    def start_pomodoro(self):
        """Start or resume the Pomodoro countdown."""
        if self.pomodoro_remaining <= 0:
            self.reset_pomodoro()
        self.pomodoro_running = True
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.update_pomodoro()

    def pause_pomodoro(self):
        """Pause the Pomodoro countdown and cancel its scheduled callback."""
        self.pomodoro_running = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        if self.pomodoro_timer_id:
            self.root.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None

    def reset_pomodoro(self):
        """Reset the Pomodoro timer to the configured work duration."""
        self.pomodoro_running = False
        self.pomodoro_is_work = True
        self.pomodoro_remaining = self.user.work_minutes * SECONDS_PER_MINUTE
        if self.pomodoro_timer_id:
            self.root.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.timer_label.config(text=f"{self.user.work_minutes:02d}:00")
        self.timer_status.config(text="Work Time")
        self.progress_label.config(text="████████░░░░░░░░░░")

    def update_pomodoro(self):
        """Advance the Pomodoro countdown by one second."""
        if not self.pomodoro_running:
            return
        if self.pomodoro_remaining <= 0:
            self.timer_complete()
            return
        self.pomodoro_remaining -= 1
        self.update_timer_display()
        self.pomodoro_timer_id = self.root.after(1000, self.update_pomodoro)

    def update_timer_display(self):
        """Refresh the timer text and horizontal progress indicator."""
        mins = self.pomodoro_remaining // SECONDS_PER_MINUTE
        secs = self.pomodoro_remaining % SECONDS_PER_MINUTE
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
        total = (
            self.user.work_minutes * SECONDS_PER_MINUTE
            if self.pomodoro_is_work
            else self.user.break_minutes * SECONDS_PER_MINUTE
        )
        if total <= 0:
            return
        progress = (total - self.pomodoro_remaining) / total
        filled = int(progress * POMODORO_BAR_BLOCKS)
        bar = "█" * filled + "░" * (POMODORO_BAR_BLOCKS - filled)
        self.progress_label.config(text=bar)

    def timer_complete(self):
        """Handle the transition between completed work and break sessions."""
        self.pomodoro_running = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")

        if self.pomodoro_is_work:
            self.user.pomodoro_count += 1
            self.user.focus_time_today += self.user.work_minutes
            DataManager.save_users(AuthWindow.users)
            self.update_pomodoro_stats()
            messagebox.showinfo(
                "Timer Complete",
                f"Work session complete! Take a "
                f"{self.user.break_minutes} minute break.",
            )
            self.pomodoro_is_work = False
            self.pomodoro_remaining = (
                self.user.break_minutes * SECONDS_PER_MINUTE
            )
            self.timer_status.config(text="Break Time")
        else:
            messagebox.showinfo(
                "Break Complete",
                "Break is over! Time to focus again.",
            )
            self.pomodoro_is_work = True
            self.pomodoro_remaining = (
                self.user.work_minutes * SECONDS_PER_MINUTE
            )
            self.timer_status.config(text="Work Time")

        self.update_timer_display()
        self.progress_label.config(text="████████░░░░░░░░░░")
        self.pomodoro_timer_id = None

    # ==========================================
    # TASKS TAB
    # ==========================================
    def setup_tasks_tab(self):
        """Build task-entry controls, task actions and the task table."""
        frame = self.tasks_frame

        # Task entry area.
        add_card = self.create_card(frame, "Add Task")

        row1 = tk.Frame(add_card, bg=COLORS["card_bg"])
        row1.pack(fill="x", pady=2)
        tk.Label(
            row1,
            text="Task Title:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 10),
        ).pack(side="left", padx=5)
        self.task_title_entry = tk.Entry(
            row1,
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
            width=25,
        )
        self.task_title_entry.pack(side="left", padx=5)

        row2 = tk.Frame(add_card, bg=COLORS["card_bg"])
        row2.pack(fill="x", pady=2)
        tk.Label(
            row2,
            text="Subject:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 10),
        ).pack(side="left", padx=5)
        self.task_subject_var = tk.StringVar()
        self.task_subject_menu = ttk.Combobox(
            row2,
            textvariable=self.task_subject_var,
            values=list(self.user.subjects.keys()),
            state="readonly",
            width=15
        )
        self.task_subject_menu.pack(side="left", padx=5)
        tk.Label(
            row2,
            text="(optional)",
            bg=COLORS["card_bg"],
            fg=COLORS["text_light"],
            font=(FONT_FAMILY, 9),
        ).pack(side="left")

        row3 = tk.Frame(add_card, bg=COLORS["card_bg"])
        row3.pack(fill="x", pady=2)
        tk.Label(
            row3,
            text="Priority:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 10),
        ).pack(side="left", padx=5)
        self.task_priority_var = tk.StringVar(value="Medium")
        task_priority_menu = ttk.Combobox(
            row3,
            textvariable=self.task_priority_var,
            values=User.PRIORITIES,
            state="readonly",
            width=8
        )
        task_priority_menu.pack(side="left", padx=5)

        tk.Label(
            row3,
            text="Deadline (DD/MM/YYYY):",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 10),
        ).pack(side="left", padx=(15, 5))
        self.task_deadline_entry = tk.Entry(
            row3,
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
            width=12,
        )
        self.task_deadline_entry.pack(side="left", padx=5)

        AppButton(
            add_card,
            text="Add Task",
            command=self.add_task,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 10, "bold"),
            relief="solid",
            cursor="hand2",
            height=1
        ).pack(pady=10)

        # Task list displayed in a Treeview table.
        list_card = self.create_card(frame, "My Tasks")

        # Task summary.
        stats_row = tk.Frame(list_card, bg=COLORS["card_bg"])
        stats_row.pack(fill="x", padx=5, pady=5)
        self.task_stats_label = tk.Label(
            stats_row,
            text="",
            font=(FONT_FAMILY, 9),
            bg=COLORS["card_bg"],
            fg=COLORS["text_light"]
        )
        self.task_stats_label.pack(side="left")

        tk.Label(
            stats_row,
            text=(
                "Select a task, then use the buttons below "
                "(or double-click to change status)."
            ),
            font=(FONT_FAMILY, 9),
            bg=COLORS["card_bg"],
            fg=COLORS["text_light"],
        ).pack(side="right")

        task_controls = tk.Frame(list_card, bg=COLORS["card_bg"])
        task_controls.pack(fill="x", padx=5, pady=(0, 4))
        AppButton(
            task_controls,
            text="Mark Complete / Incomplete",
            command=self.toggle_selected_task,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 9),
            padx=8,
            pady=5,
        ).pack(side="left", padx=3)
        AppButton(
            task_controls,
            text="Delete Selected",
            command=self.delete_selected_task,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 9),
            padx=8,
            pady=5,
        ).pack(side="left", padx=3)
        AppButton(
            task_controls,
            text="Clear Completed",
            command=self.clear_completed_tasks,
            bg=COLORS["accent"],
            fg="#ffffff",
            font=(FONT_FAMILY, 9),
            padx=8,
            pady=5,
        ).pack(side="left", padx=3)

        # Use a Treeview so task fields stay under labelled columns.
        columns = ("Date", "Subject", "Task", "Status")
        self.task_tree = ttk.Treeview(
            list_card,
            columns=columns,
            show="headings",
            height=10
        )

        # Define column headings.
        self.task_tree.heading("Date", text="Date")
        self.task_tree.heading("Subject", text="Subject")
        self.task_tree.heading("Task", text="Task")
        self.task_tree.heading("Status", text="Status")

        # Set column widths.
        self.task_tree.column("Date", width=100, anchor="center")
        self.task_tree.column("Subject", width=100, anchor="center")
        self.task_tree.column("Task", width=280, anchor="w")
        self.task_tree.column("Status", width=80, anchor="center")

        # Add a vertical scrollbar for longer task lists.
        scrollbar = ttk.Scrollbar(
            list_card,
            orient="vertical",
            command=self.task_tree.yview,
        )
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        self.task_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5,
            pady=5,
        )
        scrollbar.pack(side="right", fill="y", pady=5)

        # Double-clicking a row toggles the task status.
        self.task_tree.bind("<Double-1>", self.on_task_double_click)

    def add_task(self):
        """Read task inputs, add a validated task and refresh the table."""
        title = self.task_title_entry.get().strip()
        subject = self.task_subject_var.get() or None
        priority = self.task_priority_var.get()
        deadline = self.task_deadline_entry.get().strip() or None

        try:
            self.user.add_task(title, subject, deadline, priority)
            DataManager.save_users(AuthWindow.users)
            self.update_tasks_display()
            self.task_title_entry.delete(0, tk.END)
            self.task_deadline_entry.delete(0, tk.END)
            messagebox.showinfo("Success", "Task added!")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def get_selected_task_id(self):
        """Return the selected task ID or warn when none is selected."""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a task first.")
            return None
        return int(self.task_tree.item(selected[0], "text"))

    def toggle_selected_task(self):
        """Toggle the completion state of the selected task."""
        task_id = self.get_selected_task_id()
        if task_id is None:
            return
        self.user.toggle_task(task_id)
        DataManager.save_users(AuthWindow.users)
        self.update_tasks_display()

    def delete_selected_task(self):
        """Delete the selected task after user confirmation."""
        task_id = self.get_selected_task_id()
        if task_id is None:
            return
        if messagebox.askyesno("Confirm", "Delete the selected task?"):
            self.user.delete_task(task_id)
            DataManager.save_users(AuthWindow.users)
            self.update_tasks_display()

    def on_task_double_click(self, event):
        """Toggle the selected task status after a double-click."""
        selected = self.task_tree.selection()
        if not selected:
            return

        # Read the task ID stored on the selected row.
        item = selected[0]
        task_id = int(self.task_tree.item(item, "text"))
        self.user.toggle_task(task_id)
        DataManager.save_users(AuthWindow.users)
        self.update_tasks_display()

    def update_tasks_display(self):
        # Clear the current Treeview rows.
        """Refresh task rows, ordering, statistics and completed styling."""
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # Refresh the subject choices.
        self.task_subject_menu["values"] = list(self.user.subjects.keys())

        # Refresh task statistics.
        total = self.user.get_task_count()
        completed = self.user.get_completed_count()
        self.task_stats_label.config(
            text=(
                f"Total: {total}  |  Completed: {completed}  |  "
                f"Pending: {total - completed}"
            )
        )

        if not self.user.tasks:
            self.task_tree.insert(
                "",
                "end",
                text="0",
                values=("-", "-", "No tasks yet", "-"),
                tags=("placeholder",),
            )
            self.task_tree.tag_configure(
                "placeholder",
                foreground=COLORS["text_light"],
            )
            return

        # Show incomplete tasks before completed tasks.
        tasks = sorted(
            self.user.tasks,
            key=lambda task: (task["completed"], task["id"]),
        )

        for task in tasks:
            status = "Done" if task["completed"] else "Pending"
            subject = task.get("subject") or "-"
            deadline = task.get("deadline") or "-"

            # Store the task ID in the Treeview item text.
            item = self.task_tree.insert(
                "",
                "end",
                text=str(task["id"]),
                values=(
                deadline,
                subject,
                task["title"],
                status
            ))

            # Display completed tasks using the lighter text style.
            if task["completed"]:
                self.task_tree.item(item, tags=("completed",))

        # Configure the completed-task style.
        self.task_tree.tag_configure(
            "completed",
            foreground=COLORS["text_light"],
        )

    def clear_completed_tasks(self):
        """Delete all completed tasks after confirmation."""
        if not self.user.tasks:
            messagebox.showinfo("Info", "No tasks to clear.")
            return

        completed = [t for t in self.user.tasks if t["completed"]]
        if not completed:
            messagebox.showinfo("Info", "No completed tasks.")
            return

        if messagebox.askyesno(
            "Confirm",
            f"Delete {len(completed)} completed task(s)?",
        ):
            self.user.tasks = [
                task
                for task in self.user.tasks
                if not task["completed"]
            ]
            DataManager.save_users(AuthWindow.users)
            self.update_tasks_display()
            messagebox.showinfo("Success", "Completed tasks cleared.")

    # ==========================================
    # SETTINGS TAB
    # ==========================================
    def setup_settings_tab(self):
        """Build theme, password and data-management settings controls."""
        frame = self.settings_frame

        theme_card = self.create_card(frame, "Appearance")
        theme_check = tk.Checkbutton(
            theme_card,
            text="Dark Mode",
            variable=self.theme_var,
            command=self.toggle_theme,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            selectcolor=COLORS["card_bg"]
        )
        theme_check.pack(anchor="w", pady=5)

        pw_card = self.create_card(frame, "Change Password")
        tk.Label(
            pw_card,
            text="Current Password:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 10),
        ).pack(anchor="w", pady=(5, 0))
        self.old_pw_entry = tk.Entry(
            pw_card,
            show="●",
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.old_pw_entry.pack(fill="x", pady=(0, 10))

        tk.Label(
            pw_card,
            text=f"New Password (min {MIN_PASSWORD_LENGTH}):",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 10),
        ).pack(anchor="w", pady=(5, 0))
        self.new_pw_entry = tk.Entry(
            pw_card,
            show="●",
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.new_pw_entry.pack(fill="x", pady=(0, 10))

        tk.Label(
            pw_card,
            text="Confirm New Password:",
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=(FONT_FAMILY, 10),
        ).pack(anchor="w", pady=(5, 0))
        self.confirm_pw_entry = tk.Entry(
            pw_card,
            show="●",
            font=(FONT_FAMILY, 11),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"],
        )
        self.confirm_pw_entry.pack(fill="x", pady=(0, 15))

        AppButton(
            pw_card,
            text="Change Password",
            command=self.change_password,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 11, "bold"),
            relief="solid",
            cursor="hand2"
        ).pack(fill="x")

        data_card = self.create_card(frame, "Data Management")

        AppButton(
            data_card,
            text="Clear All Study Data",
            command=self.clear_data,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 11),
            relief="solid",
            cursor="hand2"
        ).pack(fill="x", pady=5)

        delete_card = self.create_card(frame, "Danger Zone")
        tk.Label(
            delete_card,
            text="Delete your account and all data permanently.",
            fg=COLORS["delete"],
            bg=COLORS["card_bg"],
            font=(FONT_FAMILY, 10)
        ).pack(anchor="w", pady=(5, 10))

        AppButton(
            delete_card,
            text="Delete Account",
            command=self.delete_account,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 11, "bold"),
            relief="solid",
            cursor="hand2"
        ).pack(fill="x", pady=(0, 5))

    # ==========================================
    # THEME TOGGLE
    # ==========================================
    def toggle_theme(self):
        """Switch between light and dark themes and save the preference."""
        global COLORS
        if self.theme_var.get():
            COLORS = DARK_THEME.copy()
            self.user.theme = "dark"
        else:
            COLORS = LIGHT_THEME.copy()
            self.user.theme = "light"

        DataManager.save_users(AuthWindow.users)
        self.refresh_ui()

    def refresh_ui(self):
        """Rebuild all tabs so the selected theme is applied consistently."""
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        self.dashboard_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.setup_dashboard()

        self.plan_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.plan_frame, text="Plan")
        self.setup_plan_tab()

        self.progress_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.progress_frame, text="Progress")
        self.setup_progress_tab()

        self.focus_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.focus_frame, text="Focus")
        self.setup_focus_tab()

        self.tasks_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.tasks_frame, text="Tasks")
        self.setup_tasks_tab()

        self.settings_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()

        self.apply_ttk_style()
        self.root.after(100, self.update_display)

    def change_password(self):
        """Validate and save a replacement account password."""
        old = self.old_pw_entry.get()
        new = self.new_pw_entry.get()
        confirm = self.confirm_pw_entry.get()

        if not self.user.check_password(old):
            messagebox.showerror("Error", "Current password is incorrect.")
            return
        if len(new) < MIN_PASSWORD_LENGTH:
            messagebox.showerror(
                "Error",
                f"New password must be at least "
                f"{MIN_PASSWORD_LENGTH} characters.",
            )
            return
        if new != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        self.user.password_hash = hashlib.sha256(new.encode()).hexdigest()
        DataManager.save_users(AuthWindow.users)
        self.old_pw_entry.delete(0, tk.END)
        self.new_pw_entry.delete(0, tk.END)
        self.confirm_pw_entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Password changed successfully!")

    def clear_data(self):
        """Clear the current user study data after confirmation."""
        if (
            not self.user.subjects
            and not self.user.logs
            and not self.user.tasks
        ):
            messagebox.showinfo("Info", "No data to clear.")
            return
        if messagebox.askyesno(
            "Confirm",
            "Delete ALL subjects, logs, and tasks?",
        ):
            self.user.subjects = {}
            self.user.logs = {}
            self.user.tasks = []
            self.user.next_task_id = 1
            self.user.pomodoro_count = 0
            self.user.focus_time_today = 0
            DataManager.save_users(AuthWindow.users)
            self.update_display()
            messagebox.showinfo("Success", "Data cleared.")

    def delete_account(self):
        """Delete the current account and return to authentication."""
        if messagebox.askyesno(
            "Confirm",
            "Delete your account permanently? This cannot be undone.",
        ):
            username = self.user.username
            del AuthWindow.users[username]
            DataManager.save_users(AuthWindow.users)
            messagebox.showinfo("Goodbye", "Your account has been deleted.")
            self.logout()

    def logout(self):
        """Close the main window and return to the login window."""
        self.root.destroy()
        auth = AuthWindow()
        auth.run()

    def run(self):
        """Start the Tkinter event loop for the main application."""
        self.root.mainloop()


class TestStudyScheduler(unittest.TestCase):
    """Regression tests for StudyMate data, planning and validation logic."""
    def setUp(self):
        """Create a fresh test user before each unit test."""
        password_hash = hashlib.sha256("password".encode()).hexdigest()
        self.user = User("testuser", password_hash)

    def test_add_subject_valid_and_capitalised(self):
        """Verify valid subject names are normalised and stored."""
        deadline = (datetime.now() + timedelta(days=30)).strftime(DATE_FORMAT)
        saved_name = self.user.add_subject(
            "digital technology",
            5,
            "High",
            deadline,
            None,
            "A",
        )
        self.assertEqual(saved_name, "Digital Technology")
        self.assertIn("Digital Technology", self.user.subjects)

    def test_add_subject_invalid_name(self):
        """Verify an empty subject name is rejected."""
        with self.assertRaises(ValueError):
            self.user.add_subject("", 5)

    def test_duplicate_subject_case_insensitive(self):
        """Verify differently cased duplicate subjects are rejected."""
        self.user.add_subject("Maths", 5)
        with self.assertRaises(ValueError):
            self.user.add_subject("maths", 4)

    def test_generate_plan(self):
        """Verify a daily plan is generated for stored subjects."""
        self.user.add_subject("Math", 10)
        self.user.add_subject("English", 10)
        plan = self.user.generate_plan(3, days=1)
        date = datetime.now().strftime(DATE_FORMAT)
        self.assertIn(date, plan)
        self.assertEqual(plan[date]["Math"], 1.5)

    def test_priority_weighted_plan(self):
        """Verify limited daily capacity follows priority weighting."""
        self.user.add_subject("Maths", 4, "High")
        self.user.add_subject("English", 4, "Medium")
        self.user.add_subject("Art", 4, "Low")
        plan = self.user.generate_plan(6, days=1)
        date = datetime.now().strftime(DATE_FORMAT)
        self.assertEqual(
            plan[date],
            {"Maths": 3.0, "English": 2.0, "Art": 1.0},
        )

    def test_weekly_plan_respects_seven_day_target(self):
        """Verify a seven-day plan does not repeat weekly targets daily."""
        self.user.add_subject("Maths", 2, "Medium")
        plan, summary = self.user.generate_weekly_schedule(4, days=7)
        total = sum(
            day.get("Maths", 0)
            for day in plan.values()
        )
        self.assertEqual(total, 2.0)
        self.assertEqual(summary["total_scheduled"], 2.0)
        self.assertEqual(summary["unused_capacity"], 26.0)

    def test_weekly_plan_scales_target_for_two_weeks(self):
        """Verify weekly targets scale correctly across fourteen days."""
        self.user.add_subject("Maths", 2, "Medium")
        plan, summary = self.user.generate_weekly_schedule(1, days=14)
        total = sum(
            day.get("Maths", 0)
            for day in plan.values()
        )
        self.assertEqual(total, 4.0)
        self.assertEqual(summary["total_desired"], 4.0)

    def test_weekly_plan_places_urgent_subject_before_deadline(self):
        """Verify urgent study time is scheduled before its deadline."""
        deadline = (
            datetime.now() + timedelta(days=1)
        ).strftime(DATE_FORMAT)
        self.user.add_subject("Maths", 1, "Medium", deadline)
        plan, _summary = self.user.generate_weekly_schedule(1, days=7)
        dates = list(plan.keys())
        scheduled_after_deadline = sum(
            plan[date].get("Maths", 0)
            for date in dates[2:]
        )
        self.assertEqual(scheduled_after_deadline, 0)

    def test_weekly_plan_uses_priority_when_capacity_is_limited(self):
        """Verify weekly allocation uses priority when capacity is limited."""
        self.user.add_subject("Maths", 4, "High")
        self.user.add_subject("English", 4, "Medium")
        self.user.add_subject("Art", 4, "Low")
        _plan, summary = self.user.generate_weekly_schedule(
            6 / 7,
            days=7,
        )
        self.assertEqual(
            summary["scheduled_by_subject"],
            {"Maths": 3.0, "English": 2.0, "Art": 1.0},
        )

    def test_log_time_validates_date(self):
        """Verify invalid study-log date formats are rejected."""
        self.user.add_subject("Maths", 5)
        with self.assertRaises(ValueError):
            self.user.log_study_time("2026-08-15", "Maths", 1)

    def test_add_subject_rejects_past_deadline(self):
        """Verify subject deadlines in the past are rejected."""
        past_deadline = (
            datetime.now() - timedelta(days=1)
        ).strftime(DATE_FORMAT)
        with self.assertRaisesRegex(ValueError, "cannot be in the past"):
            self.user.add_subject("Maths", 5, deadline=past_deadline)

    def test_daily_plan_rejects_more_than_24_hours(self):
        """Verify daily plan capacity above 24 hours is rejected."""
        self.user.add_subject("Maths", 5)
        with self.assertRaises(ValueError):
            self.user.generate_daily_plan(25)

    def test_weekly_plan_rejects_more_than_24_hours_per_day(self):
        """Verify weekly daily capacity above 24 hours is rejected."""
        self.user.add_subject("Maths", 5)
        with self.assertRaises(ValueError):
            self.user.generate_weekly_schedule(25, days=7)

    def test_logged_hours_by_subject(self):
        """Verify study logs are totalled correctly by subject."""
        self.user.add_subject("Maths", 5)
        self.user.log_study_time("15/08/2026", "Maths", 1.5)
        self.user.log_study_time("16/08/2026", "Maths", 0.5)
        self.assertEqual(self.user.get_logged_hours_by_subject()["Maths"], 2.0)

    def test_add_task(self):
        """Verify a valid task is added to the task list."""
        self.user.add_subject("Math", 5)
        deadline = (datetime.now() + timedelta(days=7)).strftime(DATE_FORMAT)
        self.user.add_task("Test task", "Math", deadline, "High")
        self.assertEqual(len(self.user.tasks), 1)
        self.assertEqual(self.user.tasks[0]["title"], "Test task")

    def test_toggle_task(self):
        """Verify a task completion state can be toggled."""
        self.user.add_subject("Math", 5)
        self.user.add_task("Test task", "Math")
        task_id = self.user.tasks[0]["id"]
        self.user.toggle_task(task_id)
        self.assertTrue(self.user.tasks[0]["completed"])

    def test_delete_subject_detaches_task(self):
        """Verify deleting a subject detaches linked tasks safely."""
        self.user.add_subject("Math", 5)
        self.user.add_task("Test task", "Math")
        self.user.delete_subject("Math")
        self.assertIsNone(self.user.tasks[0]["subject"])


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main(argv=["first-arg-is-ignored"])
    else:
        # Load saved users before starting the authentication window.
        AuthWindow.users = DataManager.load_users()
        auth = AuthWindow()
        auth.run()



