"""
STUDY SCHEDULER - AS91896 Excellence Level
Author: Hui Su
Date: 2026-07-21
Description: A multi-user desktop application for planning study time.
             Features: login/signup, subject management, priority system,
             deadlines, daily/weekly planning, progress tracking,
             statistics charts, and report export.
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

# Color theme
COLORS = {
    "bg": "#f5f0fa",
    "frame_bg": "#ffffff",
    "accent": "#6b46c1",
    "accent_light": "#9b6dff",
    "accent_dark": "#553c9a",
    "text": "#2d2d5e",
    "text_light": "#718096",
    "success": "#2e7d64",
    "delete": "#b91c1c",
    "warning": "#d69e2e",
    "high_priority": "#e53e3e",
    "medium_priority": "#d69e2e",
    "low_priority": "#38a169",
    "chart_bar": "#6b46c1",
    "chart_bg": "#edf2f7",
}


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
        self.subjects = {}  # name -> {"hours": float, "priority": str, "deadline": str or None}
        self.logs = {}      # date -> {subject_name: hours_studied}
    
    def check_password(self, password):
        """Verify password against stored hash."""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def add_subject(self, name, hours, priority="Medium", deadline=None):
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
        
        self.subjects[name] = {"hours": hours, "priority": priority, "deadline": deadline}
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
    
    def to_dict(self):
        """Convert user to dictionary for JSON storage."""
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "subjects": self.subjects,
            "logs": self.logs
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create User from dictionary."""
        user = cls(data["username"], data["password_hash"])
        user.subjects = data.get("subjects", {})
        user.logs = data.get("logs", {})
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
            text="📚 STUDY SCHEDULER",
            font=("Helvetica", 20, "bold"),
            fg="white",
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
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.login_username = tk.Entry(self.container, font=("Helvetica", 12))
        self.login_username.pack(fill="x", pady=(0, 15))
        
        # Password
        tk.Label(
            self.container,
            text="Password",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.login_password = tk.Entry(self.container, font=("Helvetica", 12), show="●")
        self.login_password.pack(fill="x", pady=(0, 20))
        self.login_password.bind("<Return>", lambda e: self.do_login())
        
        # Login button
        tk.Button(
            self.container,
            text="LOGIN",
            command=self.do_login,
            bg=COLORS["accent"],
            fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        ).pack(fill="x", pady=(0, 15))
        
        # Signup link
        tk.Label(
            self.container,
            text="Don't have an account? Sign up",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            fg=COLORS["accent_light"],
            cursor="hand2"
        ).pack()
        self.container.winfo_children()[-1].bind("<Button-1>", lambda e: self.show_signup())
    
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
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.signup_username = tk.Entry(self.container, font=("Helvetica", 12))
        self.signup_username.pack(fill="x", pady=(0, 15))
        
        # Password
        tk.Label(
            self.container,
            text="Password (min 6 characters)",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.signup_password = tk.Entry(self.container, font=("Helvetica", 12), show="●")
        self.signup_password.pack(fill="x", pady=(0, 15))
        
        # Confirm password
        tk.Label(
            self.container,
            text="Confirm Password",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.signup_confirm = tk.Entry(self.container, font=("Helvetica", 12), show="●")
        self.signup_confirm.pack(fill="x", pady=(0, 20))
        self.signup_confirm.bind("<Return>", lambda e: self.do_signup())
        
        # Signup button
        tk.Button(
            self.container,
            text="CREATE ACCOUNT",
            command=self.do_signup,
            bg=COLORS["success"],
            fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat",
            cursor="hand2",
            height=2
        ).pack(fill="x", pady=(0, 15))
        
        # Login link
        tk.Label(
            self.container,
            text="Already have an account? Login",
            font=("Helvetica", 10),
            bg=COLORS["bg"],
            fg=COLORS["accent_light"],
            cursor="hand2"
        ).pack()
        self.container.winfo_children()[-1].bind("<Button-1>", lambda e: self.show_login())
    
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
        
        self.root = tk.Tk()
        self.root.title(f"Study Scheduler - {user.username}")
        self.root.geometry("900x800")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(800, 700)
        
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Build all UI components."""
        # Title bar with user info
        title_bar = tk.Frame(self.root, bg=COLORS["accent"], height=50)
        title_bar.pack(fill="x")
        
        tk.Label(
            title_bar,
            text=f"📚 STUDY SCHEDULER — {self.user.username}",
            font=("Helvetica", 16, "bold"),
            fg="white",
            bg=COLORS["accent"]
        ).pack(side="left", padx=20, pady=10)
        
        # Logout button in title bar
        tk.Button(
            title_bar,
            text="Logout",
            command=self.logout,
            bg=COLORS["accent_dark"],
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            cursor="hand2"
        ).pack(side="right", padx=20, pady=8)
        
        # Main content in notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Dashboard
        self.dashboard_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.dashboard_frame, text="📋 Dashboard")
        self.setup_dashboard()
        
        # Tab 2: Plan
        self.plan_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.plan_frame, text="📅 Plan")
        self.setup_plan_tab()
        
        # Tab 3: Progress
        self.progress_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.progress_frame, text="📊 Progress")
        self.setup_progress_tab()
        
        # Tab 4: Settings
        self.settings_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.notebook.add(self.settings_frame, text="⚙️ Settings")
        self.setup_settings_tab()
    
    # ==========================================
    # DASHBOARD TAB
    # ==========================================
    def setup_dashboard(self):
        """Setup the dashboard tab."""
        frame = self.dashboard_frame
        
        # Two columns: Add subject (left) and Subject list (right)
        top_frame = tk.Frame(frame, bg=COLORS["bg"])
        top_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left column - Add subject
        left_frame = tk.Frame(top_frame, bg=COLORS["bg"])
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        add_card = self.create_card(left_frame, "Add Subject")
        
        # Subject name
        tk.Label(add_card, text="Subject Name:", bg=COLORS["frame_bg"]).pack(anchor="w", pady=(5, 0))
        self.name_entry = tk.Entry(add_card, font=("Helvetica", 11))
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        # Hours
        tk.Label(add_card, text="Weekly Hours (0-24):", bg=COLORS["frame_bg"]).pack(anchor="w", pady=(5, 0))
        self.hours_entry = tk.Entry(add_card, font=("Helvetica", 11))
        self.hours_entry.pack(fill="x", pady=(0, 10))
        
        # Priority
        tk.Label(add_card, text="Priority:", bg=COLORS["frame_bg"]).pack(anchor="w", pady=(5, 0))
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
        tk.Label(add_card, text="Deadline (YYYY-MM-DD, optional):", bg=COLORS["frame_bg"]).pack(anchor="w", pady=(5, 0))
        self.deadline_entry = tk.Entry(add_card, font=("Helvetica", 11))
        self.deadline_entry.pack(fill="x", pady=(0, 15))
        
        tk.Button(
            add_card,
            text="Add Subject",
            command=self.add_subject,
            bg=COLORS["accent"],
            fg="white",
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
            height=12,
            font=("Courier New", 10),
            bg="#fafafa",
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.subject_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.subject_list.bind("<Button-1>", lambda e: self.select_subject())
        
        # Delete button below list
        btn_frame = tk.Frame(list_card, bg=COLORS["frame_bg"])
        btn_frame.pack(fill="x", pady=(0, 5))
        tk.Button(
            btn_frame,
            text="Delete Selected Subject",
            command=self.delete_subject,
            bg=COLORS["delete"],
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="Clear All Subjects",
            command=self.clear_all_subjects,
            bg=COLORS["text_light"],
            fg="white",
            font=("Helvetica", 10),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        # Plan generation section
        plan_card = self.create_card(frame, "Generate Daily Plan")
        row = tk.Frame(plan_card, bg=COLORS["frame_bg"])
        row.pack(fill="x", pady=5)
        
        tk.Label(row, text="Hours per day:", bg=COLORS["frame_bg"], font=("Helvetica", 11)).pack(side="left")
        self.avail_entry = tk.Entry(row, width=10, font=("Helvetica", 11))
        self.avail_entry.pack(side="left", padx=10)
        self.avail_entry.insert(0, "3")
        
        tk.Button(
            row,
            text="Generate Today's Plan",
            command=self.generate_today_plan,
            bg=COLORS["success"],
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        # Plan display
        self.plan_display = tk.Text(
            plan_card,
            height=8,
            font=("Courier New", 10),
            bg="#fafafa",
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.plan_display.pack(fill="both", expand=True, pady=(10, 0))
    
    def create_card(self, parent, title):
        """Create a card-style frame."""
        card = tk.Frame(parent, bg=COLORS["frame_bg"], relief="ridge", bd=1)
        card.pack(fill="both", expand=True, padx=5, pady=5)
        
        tk.Label(
            card,
            text=title,
            font=("Helvetica", 12, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["frame_bg"]
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        content = tk.Frame(card, bg=COLORS["frame_bg"])
        content.pack(fill="both", expand=True, padx=10, pady=5)
        return content
    
    def add_subject(self):
        """Add a subject from the input fields."""
        name = self.name_entry.get().strip()
        hours_str = self.hours_entry.get().strip()
        priority = self.priority_var.get()
        deadline = self.deadline_entry.get().strip() or None
        
        try:
            hours = float(hours_str)
            self.user.add_subject(name, hours, priority, deadline)
            DataManager.save_users(AuthWindow.users)
            self.update_display()
            self.name_entry.delete(0, tk.END)
            self.hours_entry.delete(0, tk.END)
            self.deadline_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Added '{name}'")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def update_display(self):
        """Refresh the subject list and plan display."""
        # Update subject list
        self.subject_list.delete(1.0, tk.END)
        if not self.user.subjects:
            self.subject_list.insert(tk.END, "No subjects yet. Add one above!")
            return
        
        for name, data in self.user.subjects.items():
            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(data["priority"], "")
            deadline_str = f"  📅 {data['deadline']}" if data.get("deadline") else ""
            self.subject_list.insert(
                tk.END,
                f"{name}  {data['hours']}h/week  {priority_emoji}{data['priority']}{deadline_str}\n"
            )
        
        # Also update plan tab
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
            
            # Display plan
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
        
        # Controls at top
        control_frame = tk.Frame(frame, bg=COLORS["bg"])
        control_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(control_frame, text="Hours per day:", bg=COLORS["bg"], font=("Helvetica", 11)).pack(side="left")
        self.plan_avail_entry = tk.Entry(control_frame, width=10, font=("Helvetica", 11))
        self.plan_avail_entry.pack(side="left", padx=10)
        self.plan_avail_entry.insert(0, "3")
        
        tk.Label(control_frame, text="Days:", bg=COLORS["bg"], font=("Helvetica", 11)).pack(side="left", padx=(20, 0))
        self.days_entry = tk.Entry(control_frame, width=5, font=("Helvetica", 11))
        self.days_entry.pack(side="left", padx=10)
        self.days_entry.insert(0, "7")
        
        tk.Button(
            control_frame,
            text="Generate Plan",
            command=self.generate_weekly_plan,
            bg=COLORS["accent"],
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=20)
        
        tk.Button(
            control_frame,
            text="Export Report",
            command=self.export_report,
            bg=COLORS["success"],
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        # Plan display
        self.weekly_plan_display = tk.Text(
            frame,
            height=20,
            font=("Courier New", 10),
            bg="#fafafa",
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.weekly_plan_display.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def update_plan_tab(self):
        """Update the plan tab (called when subjects change)."""
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
                self.weekly_plan_display.insert(tk.END, f"📅 {day_name} ({date})\n")
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
        
        # Logging section
        log_card = self.create_card(frame, "Log Study Time")
        
        row = tk.Frame(log_card, bg=COLORS["frame_bg"])
        row.pack(fill="x", pady=5)
        
        tk.Label(row, text="Date:", bg=COLORS["frame_bg"], font=("Helvetica", 11)).pack(side="left")
        self.log_date_entry = tk.Entry(row, width=12, font=("Helvetica", 11))
        self.log_date_entry.pack(side="left", padx=5)
        self.log_date_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
        
        tk.Label(row, text="Subject:", bg=COLORS["frame_bg"], font=("Helvetica", 11)).pack(side="left", padx=(10, 0))
        self.log_subject_var = tk.StringVar()
        self.log_subject_menu = ttk.Combobox(
            row,
            textvariable=self.log_subject_var,
            values=list(self.user.subjects.keys()),
            state="readonly",
            width=12
        )
        self.log_subject_menu.pack(side="left", padx=5)
        
        tk.Label(row, text="Hours:", bg=COLORS["frame_bg"], font=("Helvetica", 11)).pack(side="left", padx=(10, 0))
        self.log_hours_entry = tk.Entry(row, width=8, font=("Helvetica", 11))
        self.log_hours_entry.pack(side="left", padx=5)
        
        tk.Button(
            row,
            text="Log Time",
            command=self.log_study_time,
            bg=COLORS["accent_light"],
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        # Stats display
        stats_card = self.create_card(frame, "Statistics")
        self.stats_display = tk.Text(
            stats_card,
            height=8,
            font=("Courier New", 10),
            bg="#fafafa",
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.stats_display.pack(fill="both", expand=True, pady=(5, 0))
        
        # Charts
        chart_card = self.create_card(frame, "Study Distribution")
        self.chart_canvas = tk.Canvas(
            chart_card,
            height=150,
            bg="white",
            relief="flat",
            bd=0
        )
        self.chart_canvas.pack(fill="both", expand=True, pady=(5, 0))
    
    def update_progress_tab(self):
        """Update the progress tab (called when subjects change)."""
        # Update subject dropdown
        self.log_subject_menu["values"] = list(self.user.subjects.keys())
        if self.user.subjects:
            self.log_subject_var.set(next(iter(self.user.subjects.keys())))
    
    def log_study_time(self):
        """Log study time for a subject."""
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
        """Update statistics display."""
        if not self.user.subjects:
            self.stats_display.delete(1.0, tk.END)
            self.stats_display.insert(tk.END, "No subjects to show stats for.")
            self.chart_canvas.delete("all")
            return
        
        # Calculate totals
        total_hours = sum(data["hours"] for data in self.user.subjects.values())
        
        # Display stats
        self.stats_display.delete(1.0, tk.END)
        self.stats_display.insert(tk.END, f"Total weekly hours: {total_hours:.1f}\n")
        self.stats_display.insert(tk.END, f"Number of subjects: {len(self.user.subjects)}\n\n")
        
        for name, data in self.user.subjects.items():
            percentage = (data["hours"] / total_hours * 100) if total_hours > 0 else 0
            self.stats_display.insert(tk.END, f"{name}: {data['hours']:.1f}h ({percentage:.0f}%)\n")
        
        # Draw chart
        self.draw_chart(total_hours)
    
    def draw_chart(self, total_hours):
        """Draw a bar chart on the canvas."""
        canvas = self.chart_canvas
        canvas.delete("all")
        
        if not self.user.subjects or total_hours == 0:
            canvas.create_text(200, 75, text="No data to display", fill="gray")
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
            
            color = COLORS["chart_bar"]
            canvas.create_rectangle(
                x, height - 20 - bar_height,
                x + bar_width, height - 20,
                fill=color,
                outline=""
            )
            
            # Subject name (truncate if too long)
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
    # SETTINGS TAB
    # ==========================================
    def setup_settings_tab(self):
        """Setup the settings tab."""
        frame = self.settings_frame
        
        # Change password
        pw_card = self.create_card(frame, "Change Password")
        
        tk.Label(pw_card, text="Current Password:", bg=COLORS["frame_bg"]).pack(anchor="w", pady=(5, 0))
        self.old_pw_entry = tk.Entry(pw_card, show="●", font=("Helvetica", 11))
        self.old_pw_entry.pack(fill="x", pady=(0, 10))
        
        tk.Label(pw_card, text="New Password (min 6):", bg=COLORS["frame_bg"]).pack(anchor="w", pady=(5, 0))
        self.new_pw_entry = tk.Entry(pw_card, show="●", font=("Helvetica", 11))
        self.new_pw_entry.pack(fill="x", pady=(0, 10))
        
        tk.Label(pw_card, text="Confirm New Password:", bg=COLORS["frame_bg"]).pack(anchor="w", pady=(5, 0))
        self.confirm_pw_entry = tk.Entry(pw_card, show="●", font=("Helvetica", 11))
        self.confirm_pw_entry.pack(fill="x", pady=(0, 15))
        
        tk.Button(
            pw_card,
            text="Change Password",
            command=self.change_password,
            bg=COLORS["accent"],
            fg="white",
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
            fg="white",
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
            bg=COLORS["frame_bg"],
            font=("Helvetica", 10)
        ).pack(anchor="w", pady=(5, 10))
        
        tk.Button(
            delete_card,
            text="Delete Account",
            command=self.delete_account,
            bg=COLORS["delete"],
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(fill="x", pady=(0, 5))
    
    def change_password(self):
        """Change user password."""
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
        """Clear all subjects and logs."""
        if not self.user.subjects and not self.user.logs:
            messagebox.showinfo("Info", "No data to clear.")
            return
        
        if messagebox.askyesno("Confirm", "Delete ALL subjects and logs?"):
            self.user.subjects = {}
            self.user.logs = {}
            DataManager.save_users(AuthWindow.users)
            self.update_display()
            messagebox.showinfo("Success", "Data cleared.")
    
    def delete_account(self):
        """Delete the user account."""
        if messagebox.askyesno("Confirm", "Delete your account permanently? This cannot be undone."):
            username = self.user.username
            del AuthWindow.users[username]
            DataManager.save_users(AuthWindow.users)
            messagebox.showinfo("Goodbye", "Your account has been deleted.")
            self.logout()
    
    def logout(self):
        """Logout and return to login screen."""
        self.root.destroy()
        auth = AuthWindow()
        auth.run()
    
    def run(self):
        """Start the main application."""
        self.root.mainloop()


# ============================================
# UNIT TESTS
# ============================================
class TestStudyScheduler(unittest.TestCase):
    """Unit tests for core functionality."""
    
    def setUp(self):
        self.user = User("testuser", hashlib.sha256("password".encode()).hexdigest())
    
    def test_add_subject_valid(self):
        self.user.add_subject("Math", 5, "High", "2026-08-01")
        self.assertIn("Math", self.user.subjects)
        self.assertEqual(self.user.subjects["Math"]["hours"], 5)
    
    def test_add_subject_invalid_name(self):
        with self.assertRaises(ValueError):
            self.user.add_subject("", 5)
        with self.assertRaises(ValueError):
            self.user.add_subject("A", 5)
    
    def test_add_subject_invalid_hours(self):
        with self.assertRaises(ValueError):
            self.user.add_subject("Math", -1)
        with self.assertRaises(ValueError):
            self.user.add_subject("Math", 25)
    
    def test_add_subject_invalid_date(self):
        with self.assertRaises(ValueError):
            self.user.add_subject("Math", 5, deadline="2026-13-01")
    
    def test_delete_subject(self):
        self.user.add_subject("Math", 5)
        self.assertTrue(self.user.delete_subject("Math"))
        self.assertNotIn("Math", self.user.subjects)
    
    def test_generate_plan(self):
        self.user.add_subject("Math", 10)
        self.user.add_subject("English", 10)
        plan = self.user.generate_plan(3, days=1)
        date = datetime.now().strftime(DATE_FORMAT)
        self.assertIn(date, plan)
        self.assertEqual(plan[date]["Math"], 1.5)
        self.assertEqual(plan[date]["English"], 1.5)
    
    def test_priority_weight(self):
        self.user.add_subject("Math", 10, "High")
        self.user.add_subject("English", 10, "Low")
        plan = self.user.generate_plan(3, days=1)
        date = datetime.now().strftime(DATE_FORMAT)
        self.assertGreater(plan[date]["Math"], plan[date]["English"])
    
    def test_log_study_time(self):
        self.user.add_subject("Math", 5)
        self.user.log_study_time("2026-07-21", "Math", 2)
        self.assertIn("2026-07-21", self.user.logs)
        self.assertEqual(self.user.logs["2026-07-21"]["Math"], 2)
    
    def test_completion_rate(self):
        self.user.add_subject("Math", 10)
        self.user.add_subject("English", 10)
        plan = self.user.generate_plan(3, days=1)
        date = datetime.now().strftime(DATE_FORMAT)
        self.user.log_study_time(date, "Math", 1.5)
        self.user.log_study_time(date, "English", 1.5)
        rate = self.user.get_completion_rate(date, plan)
        self.assertEqual(rate, 1.0)


# ============================================
# RUN APPLICATION
# ============================================
if __name__ == "__main__":
    # Check if running tests
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main(argv=["first-arg-is-ignored"])
    else:
        # Initialize global users
        AuthWindow.users = DataManager.load_users()
        auth = AuthWindow()
        auth.run()