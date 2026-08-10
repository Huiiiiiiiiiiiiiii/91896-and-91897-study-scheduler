"""
STUDY SCHEDULER - AS91896 Excellence Level
Author: Hui Su
Date: 2026-07-22
Description: A multi-user desktop application for planning study time.
             Features: login/signup, subject management, priority system,
             deadlines, daily/weekly planning, progress tracking,
             statistics charts, report export, dark/light theme toggle,
             study goals, and pomodoro timer.
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
DATE_FORMAT = "%Y-%m-%d"
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Light theme (default)
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
    "high_priority": "#e53e3e",
    "medium_priority": "#d69e2e",
    "low_priority": "#38a169",
    "chart_bar": "#6b46c1",
    "chart_bg": "#edf2f7",
    "entry_bg": "#ffffff",
    "entry_fg": "#2d2d5e",
    "tab_fg": "#2d2d5e",
}

# Dark theme
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
    "high_priority": "#f87171",
    "medium_priority": "#fbbf24",
    "low_priority": "#34d399",
    "chart_bar": "#a78bfa",
    "chart_bg": "#2d2d5e",
    "entry_bg": "#2d2d5e",
    "entry_fg": "#e2e2e2",
    "tab_fg": "#e2e2e2",
}

# Start with light theme
COLORS = LIGHT_THEME.copy()


# ============================================
# USER CLASS
# ============================================
class User:
    """Represents a user with their subjects and progress data."""
    
    PRIORITIES = ["High", "Medium", "Low"]
    PRIORITY_WEIGHTS = {"High": 1.5, "Medium": 1.0, "Low": 0.5}
    
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash
        self.subjects = {}  # name -> {"hours": float, "priority": str, "deadline": str, "goal_hours": float, "target_grade": str}
        self.logs = {}      # date -> {subject_name: hours_studied}
        self.theme = "light"  # "light" or "dark"
        self.pomodoro_count = 0
        self.focus_time_today = 0
    
    def check_password(self, password):
        """Verify password against stored hash."""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def add_subject(self, name, hours, priority="Medium", deadline=None, goal_hours=None, target_grade=None):
        """Add or update a subject."""
        if not name or len(name.strip()) < 2:
            raise ValueError("Subject name must be at least 2 characters.")
        if not (MIN_HOURS <= hours <= MAX_HOURS_PER_DAY):
            raise ValueError(f"Hours must be between {MIN_HOURS} and {MAX_HOURS_PER_DAY}.")
        if priority not in self.PRIORITIES:
            raise ValueError("Invalid priority.")
        if deadline:
            try:
                datetime.strptime(deadline, DATE_FORMAT)
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        if goal_hours is not None and (goal_hours < 0 or goal_hours > MAX_HOURS_PER_DAY):
            raise ValueError("Goal hours must be between 0 and 24.")
        
        self.subjects[name] = {
            "hours": hours,
            "priority": priority,
            "deadline": deadline,
            "goal_hours": goal_hours or hours,
            "target_grade": target_grade or ""
        }
        return True
    
    def delete_subject(self, name):
        """Delete a subject."""
        if name in self.subjects:
            del self.subjects[name]
            return True
        return False
    
    def get_subject_weight(self, subject_data):
        """Calculate weight based on priority and deadline."""
        weight = self.PRIORITY_WEIGHTS.get(subject_data["priority"], 1.0)
        
        if subject_data.get("deadline"):
            try:
                deadline_date = datetime.strptime(subject_data["deadline"], DATE_FORMAT)
                days_left = (deadline_date - datetime.now()).days
                if 0 <= days_left <= 3:
                    weight *= 1.3
                elif 0 <= days_left <= 7:
                    weight *= 1.15
                elif 0 <= days_left <= 14:
                    weight *= 1.05
            except ValueError:
                pass
        return weight
    
    def generate_plan(self, available_hours, days=7):
        """
        Generate a study plan for N days.
        Returns a dict with date -> {subject: hours}.
        """
        if not self.subjects:
            return {}
        
        if available_hours <= 0:
            raise ValueError("Available hours must be positive.")
        
        # Calculate weighted totals
        weighted_total = 0
        weighted_subjects = {}
        for name, data in self.subjects.items():
            weight = self.get_subject_weight(data)
            weighted_hours = data["hours"] * weight
            weighted_subjects[name] = weighted_hours
            weighted_total += weighted_hours
        
        if weighted_total == 0:
            return {}
        
        # Daily plan (same each day)
        daily_plan = {}
        for name, weighted_hours in weighted_subjects.items():
            daily_plan[name] = round((weighted_hours / weighted_total) * available_hours, 1)
        
        # Generate N days
        plan = {}
        today = datetime.now()
        for i in range(days):
            date_str = (today + timedelta(days=i)).strftime(DATE_FORMAT)
            plan[date_str] = daily_plan.copy()
        
        return plan
    
    def log_study_time(self, date, subject, hours):
        """Log actual study time for a subject on a given date."""
        if subject not in self.subjects:
            raise ValueError(f"Subject '{subject}' not found.")
        if hours < 0:
            raise ValueError("Hours cannot be negative.")
        
        if date not in self.logs:
            self.logs[date] = {}
        self.logs[date][subject] = self.logs[date].get(subject, 0) + hours
        return True
    
    def get_completion_rate(self, date, plan):
        """Calculate completion rate for a given date."""
        if date not in self.logs:
            return 0.0
        
        log = self.logs[date]
        total_planned = sum(plan.get(date, {}).values()) if plan.get(date) else 0
        total_actual = sum(log.values())
        
        if total_planned == 0:
            return 1.0 if total_actual == 0 else 0.0
        
        return round(min(total_actual / total_planned, 1.0), 2)
    
    def get_goal_completion(self, subject_name):
        """Calculate goal completion for a subject."""
        if subject_name not in self.subjects:
            return 0
        data = self.subjects[subject_name]
        goal = data.get("goal_hours", data["hours"])
        actual = data["hours"]
        return round(min(actual / goal, 1.0), 2) if goal > 0 else 1.0
    
    def to_dict(self):
        """Convert user to dictionary for JSON storage."""
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "subjects": self.subjects,
            "logs": self.logs,
            "theme": self.theme,
            "pomodoro_count": self.pomodoro_count,
            "focus_time_today": self.focus_time_today
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create User from dictionary."""
        user = cls(data["username"], data["password_hash"])
        user.subjects = data.get("subjects", {})
        user.logs = data.get("logs", {})
        user.theme = data.get("theme", "light")
        user.pomodoro_count = data.get("pomodoro_count", 0)
        user.focus_time_today = data.get("focus_time_today", 0)
        return user


# ============================================
# DATA MANAGER
# ============================================
class DataManager:
    """Handles loading and saving user data."""
    
    @staticmethod
    def load_users():
        """Load all users from JSON file."""
        if not os.path.exists(USERS_FILE):
            return {}
        
        try:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
            return {username: User.from_dict(user_data) for username, user_data in data.items()}
        except (json.JSONDecodeError, KeyError):
            return {}
    
    @staticmethod
    def save_users(users):
        """Save all users to JSON file."""
        os.makedirs(DATA_DIR, exist_ok=True)
        data = {username: user.to_dict() for username, user in users.items()}
        with open(USERS_FILE, "w") as f:
            json.dump(data, f, indent=4)


# ============================================
# LOGIN/SIGNUP WINDOW
# ============================================
class AuthWindow:
    """Handles login and signup."""
    
    def __init__(self):
        self.users = DataManager.load_users()
        self.current_user = None
        
        self.root = tk.Tk()
        self.root.title("Study Scheduler - Login")
        self.root.geometry("400x500")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)
        
        self.setup_ui()
        self.show_login()
    
    def setup_ui(self):
        """Setup the UI container."""
        # Title
        title_frame = tk.Frame(self.root, bg=COLORS["accent"], height=80)
        title_frame.pack(fill="x")
        tk.Label(
            title_frame,
            text="STUDY SCHEDULER",
            font=("Helvetica", 20, "bold"),
            fg=COLORS["text_white"],
            bg=COLORS["accent"]
        ).pack(pady=25)
        
        # Main container
        self.container = tk.Frame(self.root, bg=COLORS["bg"])
        self.container.pack(fill="both", expand=True, padx=30, pady=20)
    
    def clear_container(self):
        """Clear all widgets in container."""
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def show_login(self):
        """Show login form."""
        self.clear_container()
        
        tk.Label(
            self.container,
            text="Welcome Back!",
            font=("Helvetica", 18, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"]
        ).pack(pady=(10, 20))
        
        # Username
        tk.Label(
            self.container,
            text="Username",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.login_username = tk.Entry(
            self.container,
            font=("Helvetica", 12),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.login_username.pack(fill="x", pady=(0, 15))
        
        # Password
        tk.Label(
            self.container,
            text="Password",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.login_password = tk.Entry(
            self.container,
            font=("Helvetica", 12),
            show="●",
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.login_password.pack(fill="x", pady=(0, 20))
        self.login_password.bind("<Return>", lambda e: self.do_login())
        
        # Login button
        tk.Button(
            self.container,
            text="LOGIN",
            command=self.do_login,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=("Helvetica", 12, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        ).pack(fill="x", pady=(0, 15))
        
        # Signup link
        link = tk.Label(
            self.container,
            text="Don't have an account? Sign up",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            fg=COLORS["accent_light"],
            cursor="hand2"
        )
        link.pack()
        link.bind("<Button-1>", lambda e: self.show_signup())
    
    def show_signup(self):
        """Show signup form."""
        self.clear_container()
        
        tk.Label(
            self.container,
            text="Create Account",
            font=("Helvetica", 18, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["text"]
        ).pack(pady=(10, 20))
        
        # Username
        tk.Label(
            self.container,
            text="Username (min 3 characters)",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.signup_username = tk.Entry(
            self.container,
            font=("Helvetica", 12),
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.signup_username.pack(fill="x", pady=(0, 15))
        
        # Password
        tk.Label(
            self.container,
            text="Password (min 6 characters)",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.signup_password = tk.Entry(
            self.container,
            font=("Helvetica", 12),
            show="●",
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.signup_password.pack(fill="x", pady=(0, 15))
        
        # Confirm password
        tk.Label(
            self.container,
            text="Confirm Password",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.signup_confirm = tk.Entry(
            self.container,
            font=("Helvetica", 12),
            show="●",
            fg=COLORS["text"],
            bg=COLORS["entry_bg"]
        )
        self.signup_confirm.pack(fill="x", pady=(0, 20))
        self.signup_confirm.bind("<Return>", lambda e: self.do_signup())
        
        # Signup button
        tk.Button(
            self.container,
            text="CREATE ACCOUNT",
            command=self.do_signup,
            bg=COLORS["success"],
            fg=COLORS["text_white"],
            font=("Helvetica", 12, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        ).pack(fill="x", pady=(0, 15))
        
        # Login link
        link = tk.Label(
            self.container,
            text="Already have an account? Login",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            fg=COLORS["accent_light"],
            cursor="hand2"
        )
        link.pack()
        link.bind("<Button-1>", lambda e: self.show_login())
    
    def do_login(self):
        """Handle login action."""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password.")
            return
        
        if username not in self.users:
            messagebox.showerror("Error", "User not found.")
            return
        
        user = self.users[username]
        if not user.check_password(password):
            messagebox.showerror("Error", "Incorrect password.")
            return
        
        # Apply user's saved theme
        global COLORS
        if user.theme == "dark":
            COLORS = DARK_THEME.copy()
        else:
            COLORS = LIGHT_THEME.copy()
        
        self.current_user = user
        self.root.destroy()
        self.open_main_app()
    
    def do_signup(self):
        """Handle signup action."""
        username = self.signup_username.get().strip()
        password = self.signup_password.get()
        confirm = self.signup_confirm.get()
        
        if len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters.")
            return
        
        if username in self.users:
            messagebox.showerror("Error", "Username already exists.")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters.")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        
        # Create new user
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.users[username] = User(username, password_hash)
        DataManager.save_users(self.users)
        
        messagebox.showinfo("Success", "Account created! Please login.")
        self.show_login()
    
    def open_main_app(self):
        """Open the main application window."""
        app = MainApp(self.current_user)
        app.run()
    
    def run(self):
        """Start the auth window."""
        self.root.mainloop()


# ============================================
# MAIN APPLICATION WINDOW
# ============================================
class MainApp:
    """Main application window with all features."""
    
    def __init__(self, user):
        self.user = user
        self.pomodoro_running = False
        self.pomodoro_remaining = 25 * 60  # 25 minutes in seconds
        self.pomodoro_is_work = True
        self.pomodoro_timer_id = None
        
        self.root = tk.Tk()
        self.root.title(f"Study Scheduler - {user.username}")
        self.root.geometry("950x850")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(850, 750)
        
        # Apply theme to ttk
        self.apply_ttk_style()
        
        self.setup_ui()
        self.update_display()
    
    def apply_ttk_style(self):
        """Apply theme to ttk widgets."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Tab text color
        style.configure('TNotebook.Tab', foreground=COLORS["tab_fg"], font=('Helvetica', 10))
        style.map('TNotebook.Tab', foreground=[('selected', COLORS["accent"])])
        
        # Combobox
        style.configure('TCombobox', fieldbackground=COLORS["entry_bg"], foreground=COLORS["text"])
        style.map('TCombobox', fieldbackground=[('readonly', COLORS["entry_bg"])])
        
        # Entry
        style.configure('TEntry', fieldbackground=COLORS["entry_bg"], foreground=COLORS["text"])
    
    def setup_ui(self):
        """Build all UI components."""
        # Title bar with user info
        title_bar = tk.Frame(self.root, bg=COLORS["accent"], height=50)
        title_bar.pack(fill="x")
        
        tk.Label(
            title_bar,
            text=f"STUDY SCHEDULER — {self.user.username}",
            font=("Helvetica", 16, "bold"),
            fg=COLORS["text_white"],
            bg=COLORS["accent"]
        ).pack(side="left", padx=20, pady=10)
        
        tk.Button(
            title_bar,
            text="Logout",
            command=self.logout,
            bg=COLORS["accent_dark"],
            fg=COLORS["text_white"],
            font=("Helvetica", 10),
            relief="flat",
            cursor="hand2"
        ).pack(side="right", padx=20, pady=8)
        
        # Main content in notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Dashboard
        self.dashboard_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.setup_dashboard()
        
        # Tab 2: Plan
        self.plan_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.plan_frame, text="Plan")
        self.setup_plan_tab()
        
        # Tab 3: Progress
        self.progress_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.progress_frame, text="Progress")
        self.setup_progress_tab()
        
        # Tab 4: Focus (NEW - Pomodoro Timer)
        self.focus_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.focus_frame, text="Focus")
        self.setup_focus_tab()
        
        # Tab 5: Settings
        self.settings_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()
    
    # ==========================================
    # DASHBOARD TAB
    # ==========================================
    def setup_dashboard(self):
        """Setup the dashboard tab."""
        frame = self.dashboard_frame
        
        top_frame = tk.Frame(frame, bg=COLORS["bg"])
        top_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left column - Add subject
        left_frame = tk.Frame(top_frame, bg=COLORS["bg"])
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        add_card = self.create_card(left_frame, "Add Subject")
        
        # Subject name
        tk.Label(add_card, text="Subject Name:", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.name_entry = tk.Entry(add_card, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        # Hours
        tk.Label(add_card, text="Weekly Hours (0-24):", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.hours_entry = tk.Entry(add_card, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.hours_entry.pack(fill="x", pady=(0, 10))
        
        # Priority
        tk.Label(add_card, text="Priority:", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.priority_var = tk.StringVar(value="Medium")
        priority_menu = ttk.Combobox(
            add_card,
            textvariable=self.priority_var,
            values=User.PRIORITIES,
            state="readonly",
            font=("Helvetica", 11)
        )
        priority_menu.pack(fill="x", pady=(0, 10))
        
        # Deadline
        tk.Label(add_card, text="Deadline (YYYY-MM-DD, optional):", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.deadline_entry = tk.Entry(add_card, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.deadline_entry.pack(fill="x", pady=(0, 10))
        
        # Goal Hours (NEW)
        tk.Label(add_card, text="Goal Hours (target per week):", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.goal_entry = tk.Entry(add_card, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.goal_entry.pack(fill="x", pady=(0, 10))
        self.goal_entry.insert(0, "5")
        
        # Target Grade (NEW)
        tk.Label(add_card, text="Target Grade (optional):", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.grade_entry = tk.Entry(add_card, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.grade_entry.pack(fill="x", pady=(0, 15))
        
        tk.Button(
            add_card,
            text="Add Subject",
            command=self.add_subject,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        ).pack(fill="x")
        
        # Right column - Subject list
        right_frame = tk.Frame(top_frame, bg=COLORS["bg"])
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        list_card = self.create_card(right_frame, "My Subjects")
        self.subject_list = tk.Text(
            list_card,
            height=14,
            font=("Courier New", 10),
            bg=COLORS["entry_bg"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.subject_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.subject_list.bind("<Button-1>", lambda e: self.select_subject())
        
        btn_frame = tk.Frame(list_card, bg=COLORS["card_bg"])
        btn_frame.pack(fill="x", pady=(0, 5))
        tk.Button(
            btn_frame,
            text="Delete Selected Subject",
            command=self.delete_subject,
            bg=COLORS["delete"],
            fg=COLORS["text_white"],
            font=("Helvetica", 10),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="Clear All Subjects",
            command=self.clear_all_subjects,
            bg=COLORS["text_light"],
            fg=COLORS["text_white"],
            font=("Helvetica", 10),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        # Plan generation section
        plan_card = self.create_card(frame, "Generate Daily Plan")
        row = tk.Frame(plan_card, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=5)
        
        tk.Label(row, text="Hours per day:", bg=COLORS["card_bg"], fg=COLORS["text"], font=("Helvetica", 11)).pack(side="left")
        self.avail_entry = tk.Entry(row, width=10, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.avail_entry.pack(side="left", padx=10)
        self.avail_entry.insert(0, "3")
        
        tk.Button(
            row,
            text="Generate Today's Plan",
            command=self.generate_today_plan,
            bg=COLORS["success"],
            fg=COLORS["text_white"],
            font=("Helvetica", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        self.plan_display = tk.Text(
            plan_card,
            height=8,
            font=("Courier New", 10),
            bg=COLORS["entry_bg"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.plan_display.pack(fill="both", expand=True, pady=(10, 0))
    
    def create_card(self, parent, title):
        """Create a card-style frame."""
        card = tk.Frame(parent, bg=COLORS["card_bg"], relief="ridge", bd=1)
        card.pack(fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(
            card,
            text=title,
            font=("Helvetica", 12, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["card_bg"]
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        content = tk.Frame(card, bg=COLORS["card_bg"])
        content.pack(fill="both", expand=True, padx=10, pady=5)
        return content
    
    def add_subject(self):
        """Add a subject from the input fields."""
        name = self.name_entry.get().strip()
        hours_str = self.hours_entry.get().strip()
        priority = self.priority_var.get()
        deadline = self.deadline_entry.get().strip() or None
        goal_str = self.goal_entry.get().strip()
        grade = self.grade_entry.get().strip()
        
        try:
            hours = float(hours_str)
            goal_hours = float(goal_str) if goal_str else hours
            self.user.add_subject(name, hours, priority, deadline, goal_hours, grade)
            DataManager.save_users(AuthWindow.users)
            self.update_display()
            self.name_entry.delete(0, tk.END)
            self.hours_entry.delete(0, tk.END)
            self.deadline_entry.delete(0, tk.END)
            self.goal_entry.delete(0, tk.END)
            self.goal_entry.insert(0, "5")
            self.grade_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Added '{name}'")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def update_display(self):
        """Refresh the subject list and plan display."""
        self.subject_list.delete(1.0, tk.END)
        if not self.user.subjects:
            self.subject_list.insert(tk.END, "No subjects yet. Add one above!")
            return
        
        for name, data in self.user.subjects.items():
            goal_hours = data.get("goal_hours", data["hours"])
            grade = data.get("target_grade", "")
            goal_str = f"Goal: {goal_hours}h" if goal_hours else ""
            grade_str = f"Target: {grade}" if grade else ""
            deadline_str = f"Due: {data['deadline']}" if data.get("deadline") else ""
            self.subject_list.insert(
                tk.END,
                f"{name}  {data['hours']}h/wk  [{data['priority']}]  {goal_str} {grade_str} {deadline_str}\n"
            )
        
        self.update_plan_tab()
        self.update_progress_tab()
    
    def select_subject(self):
        """Handle subject selection for deletion."""
        try:
            selection = self.subject_list.tag_ranges(tk.SEL)
            if selection:
                selected = self.subject_list.get(tk.SEL_FIRST, tk.SEL_LAST)
                name = selected.split()[0]
                self.selected_subject = name
        except Exception:
            pass
    
    def delete_subject(self):
        """Delete the selected subject."""
        if hasattr(self, 'selected_subject') and self.selected_subject:
            if messagebox.askyesno("Confirm", f"Delete '{self.selected_subject}'?"):
                self.user.delete_subject(self.selected_subject)
                DataManager.save_users(AuthWindow.users)
                self.update_display()
                self.selected_subject = None
        else:
            messagebox.showwarning("No Selection", "Click on a subject to select it.")
    
    def clear_all_subjects(self):
        """Clear all subjects."""
        if not self.user.subjects:
            messagebox.showinfo("Info", "No subjects to clear.")
            return
        
        if messagebox.askyesno("Confirm", "Delete ALL subjects?"):
            self.user.subjects = {}
            DataManager.save_users(AuthWindow.users)
            self.update_display()
    
    def generate_today_plan(self):
        """Generate and display today's plan."""
        avail_str = self.avail_entry.get().strip()
        try:
            available = float(avail_str)
            if available <= 0:
                raise ValueError("Hours must be positive.")
            
            plan = self.user.generate_plan(available, days=1)
            if not plan:
                self.plan_display.delete(1.0, tk.END)
                self.plan_display.insert(tk.END, "No subjects added yet.")
                return
            
            self.plan_display.delete(1.0, tk.END)
            self.plan_display.insert(tk.END, "=" * 45 + "\n")
            self.plan_display.insert(tk.END, "       TODAY'S STUDY PLAN\n")
            self.plan_display.insert(tk.END, "=" * 45 + "\n\n")
            
            today = datetime.now().strftime(DATE_FORMAT)
            for name, hours in plan.get(today, {}).items():
                bar_length = min(int(hours * 2), 8)
                bar = "█" * bar_length + "░" * (8 - bar_length)
                self.plan_display.insert(tk.END, f"  {name}\n")
                self.plan_display.insert(tk.END, f"  {bar} {hours} hour(s)\n\n")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    # ==========================================
    # PLAN TAB
    # ==========================================
    def setup_plan_tab(self):
        """Setup the plan tab."""
        frame = self.plan_frame
        
        control_frame = tk.Frame(frame, bg=COLORS["bg"])
        control_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(control_frame, text="Hours per day:", bg=COLORS["bg"], fg=COLORS["text"], font=("Helvetica", 11)).pack(side="left")
        self.plan_avail_entry = tk.Entry(control_frame, width=10, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.plan_avail_entry.pack(side="left", padx=10)
        self.plan_avail_entry.insert(0, "3")
        
        tk.Label(control_frame, text="Days:", bg=COLORS["bg"], fg=COLORS["text"], font=("Helvetica", 11)).pack(side="left", padx=(20, 0))
        self.days_entry = tk.Entry(control_frame, width=5, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.days_entry.pack(side="left", padx=10)
        self.days_entry.insert(0, "7")
        
        tk.Button(
            control_frame,
            text="Generate Plan",
            command=self.generate_weekly_plan,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=("Helvetica", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=20)
        
        tk.Button(
            control_frame,
            text="Export Report",
            command=self.export_report,
            bg=COLORS["success"],
            fg=COLORS["text_white"],
            font=("Helvetica", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        self.weekly_plan_display = tk.Text(
            frame,
            height=20,
            font=("Courier New", 10),
            bg=COLORS["entry_bg"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.weekly_plan_display.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def update_plan_tab(self):
        pass
    
    def generate_weekly_plan(self):
        """Generate and display a weekly plan."""
        try:
            available = float(self.plan_avail_entry.get().strip())
            days = int(self.days_entry.get().strip())
            if days < 1 or days > 30:
                raise ValueError("Days must be between 1 and 30.")
            
            plan = self.user.generate_plan(available, days)
            if not plan:
                self.weekly_plan_display.delete(1.0, tk.END)
                self.weekly_plan_display.insert(tk.END, "No subjects added yet.")
                return
            
            self.weekly_plan_display.delete(1.0, tk.END)
            self.weekly_plan_display.insert(tk.END, "=" * 50 + "\n")
            self.weekly_plan_display.insert(tk.END, "           WEEKLY STUDY PLAN\n")
            self.weekly_plan_display.insert(tk.END, "=" * 50 + "\n\n")
            
            for date, daily_plan in plan.items():
                date_obj = datetime.strptime(date, DATE_FORMAT)
                day_name = date_obj.strftime("%A")
                self.weekly_plan_display.insert(tk.END, f"{day_name} ({date})\n")
                for name, hours in daily_plan.items():
                    bar = "█" * min(int(hours * 2), 8) + "░" * (8 - min(int(hours * 2), 8))
                    self.weekly_plan_display.insert(tk.END, f"   {name}: {bar} {hours}h\n")
                self.weekly_plan_display.insert(tk.END, "\n")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def export_report(self):
        """Export the current plan to a .txt file."""
        try:
            available = float(self.plan_avail_entry.get().strip())
            days = int(self.days_entry.get().strip())
            plan = self.user.generate_plan(available, days)
            
            if not plan:
                messagebox.showerror("Error", "No subjects added yet.")
                return
            
            filename = f"study_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w") as f:
                f.write("=" * 50 + "\n")
                f.write(f"STUDY PLAN - {self.user.username}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("=" * 50 + "\n\n")
                
                total_hours = sum(sum(daily.values()) for daily in plan.values())
                f.write(f"Total study time: {total_hours:.1f} hours\n\n")
                
                for date, daily_plan in plan.items():
                    f.write(f"{date}\n")
                    for name, hours in daily_plan.items():
                        f.write(f"  {name}: {hours}h\n")
                    f.write("\n")
            
            messagebox.showinfo("Success", f"Report saved to {filename}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    # ==========================================
    # PROGRESS TAB
    # ==========================================
    def setup_progress_tab(self):
        """Setup the progress tab."""
        frame = self.progress_frame
        
        log_card = self.create_card(frame, "Log Study Time")
        
        row = tk.Frame(log_card, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=5)
        
        tk.Label(row, text="Date:", bg=COLORS["card_bg"], fg=COLORS["text"], font=("Helvetica", 11)).pack(side="left")
        self.log_date_entry = tk.Entry(row, width=12, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.log_date_entry.pack(side="left", padx=5)
        self.log_date_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
        
        tk.Label(row, text="Subject:", bg=COLORS["card_bg"], fg=COLORS["text"], font=("Helvetica", 11)).pack(side="left", padx=(10, 0))
        self.log_subject_var = tk.StringVar()
        self.log_subject_menu = ttk.Combobox(
            row,
            textvariable=self.log_subject_var,
            values=list(self.user.subjects.keys()),
            state="readonly",
            width=12
        )
        self.log_subject_menu.pack(side="left", padx=5)
        
        tk.Label(row, text="Hours:", bg=COLORS["card_bg"], fg=COLORS["text"], font=("Helvetica", 11)).pack(side="left", padx=(10, 0))
        self.log_hours_entry = tk.Entry(row, width=8, font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.log_hours_entry.pack(side="left", padx=5)
        
        tk.Button(
            row,
            text="Log Time",
            command=self.log_study_time,
            bg=COLORS["accent_light"],
            fg=COLORS["text_white"],
            font=("Helvetica", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        stats_card = self.create_card(frame, "Statistics & Goals")
        self.stats_display = tk.Text(
            stats_card,
            height=10,
            font=("Courier New", 10),
            bg=COLORS["entry_bg"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.stats_display.pack(fill="both", expand=True, pady=(5, 0))
        
        chart_card = self.create_card(frame, "Study Distribution")
        self.chart_canvas = tk.Canvas(
            chart_card,
            height=150,
            bg=COLORS["entry_bg"],
            relief="flat",
            bd=0
        )
        self.chart_canvas.pack(fill="both", expand=True, pady=(5, 0))
    
    def update_progress_tab(self):
        self.log_subject_menu["values"] = list(self.user.subjects.keys())
        if self.user.subjects:
            self.log_subject_var.set(next(iter(self.user.subjects.keys())))
    
    def log_study_time(self):
        date = self.log_date_entry.get().strip()
        subject = self.log_subject_var.get()
        hours_str = self.log_hours_entry.get().strip()
        
        if not subject:
            messagebox.showerror("Error", "Please select a subject.")
            return
        
        try:
            hours = float(hours_str)
            self.user.log_study_time(date, subject, hours)
            DataManager.save_users(AuthWindow.users)
            self.log_hours_entry.delete(0, tk.END)
            self.update_stats()
            messagebox.showinfo("Success", f"Logged {hours}h for {subject} on {date}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def update_stats(self):
        if not self.user.subjects:
            self.stats_display.delete(1.0, tk.END)
            self.stats_display.insert(tk.END, "No subjects to show stats for.")
            self.chart_canvas.delete("all")
            return
        
        total_hours = sum(data["hours"] for data in self.user.subjects.values())
        
        self.stats_display.delete(1.0, tk.END)
        self.stats_display.insert(tk.END, f"Total weekly hours: {total_hours:.1f}\n")
        self.stats_display.insert(tk.END, f"Number of subjects: {len(self.user.subjects)}\n")
        self.stats_display.insert(tk.END, f"Pomodoros completed: {self.user.pomodoro_count}\n\n")
        
        # Show goal completion
        self.stats_display.insert(tk.END, "--- Goals vs Actual ---\n")
        for name, data in self.user.subjects.items():
            goal = data.get("goal_hours", data["hours"])
            actual = data["hours"]
            completion = self.user.get_goal_completion(name)
            grade = data.get("target_grade", "")
            grade_str = f" [Target: {grade}]" if grade else ""
            self.stats_display.insert(
                tk.END,
                f"{name}: {actual}h / {goal}h goal ({completion*100:.0f}%){grade_str}\n"
            )
        
        self.draw_chart(total_hours)
    
    def draw_chart(self, total_hours):
        canvas = self.chart_canvas
        canvas.delete("all")
        
        if not self.user.subjects or total_hours == 0:
            canvas.create_text(200, 75, text="No data to display", fill=COLORS["text_light"])
            return
        
        width = canvas.winfo_width() if canvas.winfo_width() > 100 else 800
        height = canvas.winfo_height() if canvas.winfo_height() > 50 else 150
        
        subjects = list(self.user.subjects.items())
        num_items = len(subjects)
        max_width = width - 60
        
        bar_width = min(max_width / num_items - 10, 60)
        max_bar_height = height - 50
        
        x = 30
        for name, data in subjects:
            hours = data["hours"]
            bar_height = (hours / max(total_hours, 1)) * max_bar_height
            bar_height = max(bar_height, 5)
            
            canvas.create_rectangle(
                x, height - 20 - bar_height,
                x + bar_width, height - 20,
                fill=COLORS["chart_bar"],
                outline=""
            )
            
            display_name = name[:6] + ".." if len(name) > 8 else name
            canvas.create_text(
                x + bar_width / 2,
                height - 5,
                text=display_name,
                font=("Helvetica", 8),
                fill=COLORS["text"]
            )
            canvas.create_text(
                x + bar_width / 2,
                height - 22 - bar_height,
                text=f"{hours:.1f}h",
                font=("Helvetica", 7),
                fill=COLORS["text"]
            )
            x += bar_width + 10
    
    # ==========================================
    # FOCUS TAB - Pomodoro Timer (NEW)
    # ==========================================
    def setup_focus_tab(self):
        """Setup the focus/pomodoro tab."""
        frame = self.focus_frame
        
        # Main timer display
        timer_card = self.create_card(frame, "Pomodoro Timer")
        
        # Time display
        self.timer_label = tk.Label(
            timer_card,
            text="25:00",
            font=("Helvetica", 64, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["card_bg"]
        )
        self.timer_label.pack(pady=20)
        
        # Status label
        self.timer_status = tk.Label(
            timer_card,
            text="Work Time",
            font=("Helvetica", 14),
            fg=COLORS["text"],
            bg=COLORS["card_bg"]
        )
        self.timer_status.pack(pady=5)
        
        # Progress bar (simple text-based)
        self.progress_label = tk.Label(
            timer_card,
            text="████████░░░░░░░░░░",
            font=("Helvetica", 14),
            fg=COLORS["accent"],
            bg=COLORS["card_bg"]
        )
        self.progress_label.pack(pady=5)
        
        # Button row
        btn_row = tk.Frame(timer_card, bg=COLORS["card_bg"])
        btn_row.pack(pady=15)
        
        self.start_btn = tk.Button(
            btn_row,
            text="▶ Start",
            command=self.start_pomodoro,
            bg=COLORS["success"],
            fg=COLORS["text_white"],
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=5
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.pause_btn = tk.Button(
            btn_row,
            text="⏸ Pause",
            command=self.pause_pomodoro,
            bg=COLORS["warning"],
            fg=COLORS["text_white"],
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=5
        )
        self.pause_btn.pack(side="left", padx=5)
        self.pause_btn.config(state="disabled")
        
        self.reset_btn = tk.Button(
            btn_row,
            text="⟳ Reset",
            command=self.reset_pomodoro,
            bg=COLORS["text_light"],
            fg=COLORS["text_white"],
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=5
        )
        self.reset_btn.pack(side="left", padx=5)
        
        # Stats
        stats_card = self.create_card(frame, "Focus Stats")
        
        row = tk.Frame(stats_card, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=5)
        
        tk.Label(row, text="Pomodoros Today:", bg=COLORS["card_bg"], fg=COLORS["text"], font=("Helvetica", 11)).pack(side="left")
        self.pomodoro_count_label = tk.Label(row, text="0", bg=COLORS["card_bg"], fg=COLORS["accent"], font=("Helvetica", 14, "bold"))
        self.pomodoro_count_label.pack(side="left", padx=10)
        
        row2 = tk.Frame(stats_card, bg=COLORS["card_bg"])
        row2.pack(fill="x", pady=5)
        tk.Label(row2, text="Focus Time Today:", bg=COLORS["card_bg"], fg=COLORS["text"], font=("Helvetica", 11)).pack(side="left")
        self.focus_time_label = tk.Label(row2, text="0 min", bg=COLORS["card_bg"], fg=COLORS["accent"], font=("Helvetica", 14, "bold"))
        self.focus_time_label.pack(side="left", padx=10)
    
    def start_pomodoro(self):
        """Start the pomodoro timer."""
        if self.pomodoro_remaining <= 0:
            self.reset_pomodoro()
        
        self.pomodoro_running = True
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.update_pomodoro()
    
    def pause_pomodoro(self):
        """Pause the pomodoro timer."""
        self.pomodoro_running = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        if self.pomodoro_timer_id:
            self.root.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None
    
    def reset_pomodoro(self):
        """Reset the pomodoro timer."""
        self.pomodoro_running = False
        self.pomodoro_is_work = True
        self.pomodoro_remaining = 25 * 60
        if self.pomodoro_timer_id:
            self.root.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.update_timer_display()
        self.timer_status.config(text="Work Time")
        self.progress_label.config(text="████████░░░░░░░░░░")
    
    def update_pomodoro(self):
        """Update the pomodoro timer each second."""
        if not self.pomodoro_running:
            return
        
        if self.pomodoro_remaining <= 0:
            self.timer_complete()
            return
        
        self.pomodoro_remaining -= 1
        self.update_timer_display()
        self.pomodoro_timer_id = self.root.after(1000, self.update_pomodoro)
    
    def update_timer_display(self):
        """Update the timer label and progress."""
        mins = self.pomodoro_remaining // 60
        secs = self.pomodoro_remaining % 60
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
        
        # Update progress bar
        total = 25 * 60 if self.pomodoro_is_work else 5 * 60
        progress = (total - self.pomodoro_remaining) / total
        filled = int(progress * 16)
        bar = "█" * filled + "░" * (16 - filled)
        self.progress_label.config(text=bar)
    
    def timer_complete(self):
        """Handle timer completion."""
        self.pomodoro_running = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        
        if self.pomodoro_is_work:
            # Work session complete
            self.user.pomodoro_count += 1
            self.user.focus_time_today += 25
            DataManager.save_users(AuthWindow.users)
            self.update_pomodoro_stats()
            messagebox.showinfo("Timer Complete", "Work session complete! Take a 5 minute break.")
            self.pomodoro_is_work = False
            self.pomodoro_remaining = 5 * 60
            self.timer_status.config(text="Break Time")
        else:
            # Break complete
            messagebox.showinfo("Break Complete", "Break is over! Time to focus again.")
            self.pomodoro_is_work = True
            self.pomodoro_remaining = 25 * 60
            self.timer_status.config(text="Work Time")
        
        self.update_timer_display()
        self.progress_label.config(text="████████░░░░░░░░░░")
        self.pomodoro_timer_id = None
    
    def update_pomodoro_stats(self):
        """Update the pomodoro stats display."""
        self.pomodoro_count_label.config(text=str(self.user.pomodoro_count))
        self.focus_time_label.config(text=f"{self.user.focus_time_today} min")
    
    # ==========================================
    # SETTINGS TAB
    # ==========================================
    def setup_settings_tab(self):
        """Setup the settings tab."""
        frame = self.settings_frame
        
        # Theme toggle (NEW)
        theme_card = self.create_card(frame, "Appearance")
        
        self.theme_var = tk.BooleanVar(value=(COLORS is DARK_THEME))
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
        
        # Change password
        pw_card = self.create_card(frame, "Change Password")
        
        tk.Label(pw_card, text="Current Password:", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.old_pw_entry = tk.Entry(pw_card, show="●", font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.old_pw_entry.pack(fill="x", pady=(0, 10))
        
        tk.Label(pw_card, text="New Password (min 6):", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.new_pw_entry = tk.Entry(pw_card, show="●", font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.new_pw_entry.pack(fill="x", pady=(0, 10))
        
        tk.Label(pw_card, text="Confirm New Password:", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.confirm_pw_entry = tk.Entry(pw_card, show="●", font=("Helvetica", 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.confirm_pw_entry.pack(fill="x", pady=(0, 15))
        
        tk.Button(
            pw_card,
            text="Change Password",
            command=self.change_password,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(fill="x")
        
        # Data management
        data_card = self.create_card(frame, "Data Management")
        
        tk.Button(
            data_card,
            text="Clear All Study Data",
            command=self.clear_data,
            bg=COLORS["warning"],
            fg=COLORS["text_white"],
            font=("Helvetica", 11),
            relief="flat",
            cursor="hand2"
        ).pack(fill="x", pady=5)
        
        # Delete account
        delete_card = self.create_card(frame, "Danger Zone")
        
        tk.Label(
            delete_card,
            text="Delete your account and all data permanently.",
            fg=COLORS["delete"],
            bg=COLORS["card_bg"],
            font=("Helvetica", 10)
        ).pack(anchor="w", pady=(5, 10))
        
        tk.Button(
            delete_card,
            text="Delete Account",
            command=self.delete_account,
            bg=COLORS["delete"],
            fg=COLORS["text_white"],
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(fill="x", pady=(0, 5))
    
    # ==========================================
    # THEME TOGGLE (NEW)
    # ==========================================
    def toggle_theme(self):
        """Switch between light and dark theme."""
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
        """Refresh all UI elements with new theme."""
        # Update root background
        self.root.configure(bg=COLORS["bg"])
        
        # Update notebook background
        for frame in [self.dashboard_frame, self.plan_frame, self.progress_frame, self.focus_frame, self.settings_frame]:
            if frame.winfo_exists():
                frame.configure(bg=COLORS["bg"])
        
        # Update ttk style
        self.apply_ttk_style()
        
        # Rebuild all tabs
        # Clear and rebuild each tab
        self.dashboard_frame.destroy()
        self.plan_frame.destroy()
        self.progress_frame.destroy()
        self.focus_frame.destroy()
        self.settings_frame.destroy()
        
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
        
        self.settings_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()
        
        self.update_display()
        self.update_stats()
        self.update_pomodoro_stats()
    
    # ==========================================
    # SETTINGS FUNCTIONS
    # ==========================================
    def change_password(self):
        old = self.old_pw_entry.get()
        new = self.new_pw_entry.get()
        confirm = self.confirm_pw_entry.get()
        
        if not self.user.check_password(old):
            messagebox.showerror("Error", "Current password is incorrect.")
            return
        
        if len(new) < 6:
            messagebox.showerror("Error", "New password must be at least 6 characters.")
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
        if not self.user.subjects and not self.user.logs:
            messagebox.showinfo("Info", "No data to clear.")
            return
        
        if messagebox.askyesno("Confirm", "Delete ALL subjects and logs?"):
            self.user.subjects = {}
            self.user.logs = {}
            self.user.pomodoro_count = 0
            self.user.focus_time_today = 0
            DataManager.save_users(AuthWindow.users)
            self.update_display()
            self.update_pomodoro_stats()
            messagebox.showinfo("Success", "Data cleared.")
    
    def delete_account(self):
        if messagebox.askyesno("Confirm", "Delete your account permanently? This cannot be undone."):
            username = self.user.username
            del AuthWindow.users[username]
            DataManager.save_users(AuthWindow.users)
            messagebox.showinfo("Goodbye", "Your account has been deleted.")
            self.logout()
    
    def logout(self):
        self.root.destroy()
        auth = AuthWindow()
        auth.run()
    
    def run(self):
        self.root.mainloop()


# ============================================
# UNIT TESTS
# ============================================
class TestStudyScheduler(unittest.TestCase):
    def setUp(self):
        self.user = User("testuser", hashlib.sha256("password".encode()).hexdigest())
    
    def test_add_subject_valid(self):
        self.user.add_subject("Math", 5, "High", "2026-08-01", 8, "A")
        self.assertIn("Math", self.user.subjects)
        self.assertEqual(self.user.subjects["Math"]["hours"], 5)
        self.assertEqual(self.user.subjects["Math"]["goal_hours"], 8)
    
    def test_add_subject_invalid_name(self):
        with self.assertRaises(ValueError):
            self.user.add_subject("", 5)
    
    def test_add_subject_invalid_hours(self):
        with self.assertRaises(ValueError):
            self.user.add_subject("Math", -1)
    
    def test_generate_plan(self):
        self.user.add_subject("Math", 10)
        self.user.add_subject("English", 10)
        plan = self.user.generate_plan(3, days=1)
        date = datetime.now().strftime(DATE_FORMAT)
        self.assertIn(date, plan)
        self.assertEqual(plan[date]["Math"], 1.5)
    
    def test_goal_completion(self):
        self.user.add_subject("Math", 5, goal_hours=10)
        completion = self.user.get_goal_completion("Math")
        self.assertEqual(completion, 0.5)


# ============================================
# RUN APPLICATION
# ============================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main(argv=["first-arg-is-ignored"])
    else:
        AuthWindow.users = DataManager.load_users()
        auth = AuthWindow()
        auth.run()