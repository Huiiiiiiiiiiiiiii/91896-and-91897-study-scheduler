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
DATE_FORMAT = "%d/%m/%Y"  # Changed to NZ format: DD/MM/YYYY

# ===== 修复1：使用脚本所在目录，避免权限问题 =====
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
    "text_white": "#2d2d5e",
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
    "text_white": "#2d2d5e",
    "success": "#34d399",
    "delete": "#f87171",
    "warning": "#fbbf24",
    "chart_bar": "#a78bfa",
    "entry_bg": "#2d2d5e",
    "entry_fg": "#e2e2e2",
    "tab_fg": "#e2e2e2",
}

COLORS = LIGHT_THEME.copy()

# ===== 字体改成更自然的字体 =====
FONT_FAMILY = "Helvetica Neue"


def draw_logo(canvas, x, y, size=35, color="#6b46c1"):
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
    canvas.create_line(x, y - size * 0.1, x, y + size * 0.4, fill=color, width=2, tags="logo")
    for i in range(3):
        y_pos = y + size * 0.05 + i * size * 0.1
        canvas.create_line(x - size * 0.25, y_pos, x - size * 0.05, y_pos, fill=color, width=1.5, tags="logo")
    for i in range(3):
        y_pos = y + size * 0.05 + i * size * 0.1
        canvas.create_line(x + size * 0.05, y_pos, x + size * 0.25, y_pos, fill=color, width=1.5, tags="logo")


class User:
    PRIORITIES = ["High", "Medium", "Low"]
    PRIORITY_WEIGHTS = {"High": 1.5, "Medium": 1.0, "Low": 0.5}
    
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash
        self.subjects = {}
        self.logs = {}
        self.theme = "light"
        self.pomodoro_count = 0
        self.focus_time_today = 0
        self.work_minutes = 25
        self.break_minutes = 5
        # ===== 新增：任务列表 =====
        self.tasks = []
        self.next_task_id = 1
    
    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def add_subject(self, name, hours, priority="Medium", deadline=None, goal_hours=None, target_grade=None):
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
                raise ValueError("Invalid date format. Use DD/MM/YYYY.")
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
        if name in self.subjects:
            del self.subjects[name]
            return True
        return False
    
    def get_subject_weight(self, subject_data):
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
        if not self.subjects:
            return {}
        if available_hours <= 0:
            raise ValueError("Available hours must be positive.")
        
        weighted_total = 0
        weighted_subjects = {}
        for name, data in self.subjects.items():
            weight = self.get_subject_weight(data)
            weighted_hours = data["hours"] * weight
            weighted_subjects[name] = weighted_hours
            weighted_total += weighted_hours
        
        if weighted_total == 0:
            return {}
        
        daily_plan = {}
        for name, weighted_hours in weighted_subjects.items():
            daily_plan[name] = round((weighted_hours / weighted_total) * available_hours, 1)
        
        plan = {}
        today = datetime.now()
        for i in range(days):
            date_str = (today + timedelta(days=i)).strftime(DATE_FORMAT)
            plan[date_str] = daily_plan.copy()
        return plan
    
    def log_study_time(self, date, subject, hours):
        if subject not in self.subjects:
            raise ValueError(f"Subject '{subject}' not found.")
        if hours < 0:
            raise ValueError("Hours cannot be negative.")
        if date not in self.logs:
            self.logs[date] = {}
        self.logs[date][subject] = self.logs[date].get(subject, 0) + hours
        return True
    
    def get_completion_rate(self, date, plan):
        if date not in self.logs:
            return 0.0
        log = self.logs[date]
        total_planned = sum(plan.get(date, {}).values()) if plan.get(date) else 0
        total_actual = sum(log.values())
        if total_planned == 0:
            return 1.0 if total_actual == 0 else 0.0
        return round(min(total_actual / total_planned, 1.0), 2)
    
    def get_goal_completion(self, subject_name):
        if subject_name not in self.subjects:
            return 0
        data = self.subjects[subject_name]
        goal = data.get("goal_hours", data["hours"])
        actual = data["hours"]
        return round(min(actual / goal, 1.0), 2) if goal > 0 else 1.0
    
    # ===== 新增：获取总学习时间 =====
    def get_total_study_hours(self):
        """Return total study hours across all logs."""
        total = 0
        for date, logs in self.logs.items():
            total += sum(logs.values())
        return round(total, 1)
    
    # ===== 新增：任务管理方法 =====
    def add_task(self, title, subject=None, deadline=None, priority="Medium"):
        if not title or len(title.strip()) < 1:
            raise ValueError("Task title cannot be empty.")
        if subject and subject not in self.subjects:
            raise ValueError(f"Subject '{subject}' not found.")
        if deadline:
            try:
                datetime.strptime(deadline, DATE_FORMAT)
            except ValueError:
                raise ValueError("Invalid date format. Use DD/MM/YYYY.")
        
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
        for task in self.tasks:
            if task["id"] == task_id:
                task["completed"] = not task["completed"]
                return True
        return False
    
    def delete_task(self, task_id):
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                del self.tasks[i]
                return True
        return False
    
    def get_task_count(self):
        return len(self.tasks)
    
    def get_completed_count(self):
        return sum(1 for t in self.tasks if t["completed"])
    
    def to_dict(self):
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
        user = cls(data["username"], data["password_hash"])
        user.subjects = data.get("subjects", {})
        user.logs = data.get("logs", {})
        user.theme = data.get("theme", "light")
        user.pomodoro_count = data.get("pomodoro_count", 0)
        user.focus_time_today = data.get("focus_time_today", 0)
        user.work_minutes = data.get("work_minutes", 25)
        user.break_minutes = data.get("break_minutes", 5)
        user.tasks = data.get("tasks", [])
        user.next_task_id = data.get("next_task_id", 1)
        return user


class DataManager:
    @staticmethod
    def load_users():
        print(f"📁 Loading users from: {USERS_FILE}")
        if not os.path.exists(USERS_FILE):
            print("⚠️ File does not exist, returning empty dict")
            return {}
        try:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
            print(f"✅ Loaded {len(data)} users")
            return {username: User.from_dict(user_data) for username, user_data in data.items()}
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return {}
        except Exception as e:
            print(f"❌ Load error: {e}")
            return {}
    
    @staticmethod
    def save_users(users):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            data = {username: user.to_dict() for username, user in users.items()}
            with open(USERS_FILE, "w") as f:
                json.dump(data, f, indent=4)
            print(f"✅ Saved {len(data)} users to {USERS_FILE}")
        except Exception as e:
            print(f"❌ Save error: {e}")


class AuthWindow:
    def __init__(self):
        self.users = DataManager.load_users()
        self.current_user = None
        
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Login")
        self.root.geometry("400x550")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)
        
        self.setup_ui()
        self.show_login()
    
    def setup_ui(self):
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
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def show_login(self):
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
        
        tk.Button(
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
            text="Username (min 3 characters)",
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
            text="Password (min 6 characters)",
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
        
        tk.Button(
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
        
        global COLORS
        if user.theme == "dark":
            COLORS = DARK_THEME.copy()
        else:
            COLORS = LIGHT_THEME.copy()
        
        self.current_user = user
        self.root.destroy()
        self.open_main_app()
    
    def do_signup(self):
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
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.users[username] = User(username, password_hash)
        DataManager.save_users(self.users)
        
        messagebox.showinfo("Success", f"Account '{username}' created successfully! Please login.")
        self.show_login()
    
    def open_main_app(self):
        app = MainApp(self.current_user)
        app.run()
    
    def run(self):
        self.root.mainloop()


class MainApp:
    def __init__(self, user):
        self.user = user
        self.pomodoro_running = False
        self.pomodoro_remaining = self.user.work_minutes * 60
        self.pomodoro_is_work = True
        self.pomodoro_timer_id = None
        
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - {user.username}")
        self.root.geometry("950x850")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(850, 750)
        
        # ===== theme_var 在 root 之后创建，并指定 master =====
        self.theme_var = tk.BooleanVar(master=self.root, value=(self.user.theme == "dark"))
        
        self.apply_ttk_style()
        self.setup_ui()
        
        self.root.after(100, self.update_display)
    
    def apply_ttk_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook.Tab', foreground=COLORS["tab_fg"], font=(FONT_FAMILY, 10))
        style.map('TNotebook.Tab', foreground=[('selected', COLORS["accent"])])
        style.configure('TCombobox', fieldbackground=COLORS["entry_bg"], foreground=COLORS["text"])
        style.map('TCombobox', fieldbackground=[('readonly', COLORS["entry_bg"])])
    
    def create_card(self, parent, title):
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
        
        # ===== 所有按钮统一深紫色背景+白色文字 =====
        tk.Button(
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
        
        # ===== 新增：Tasks 标签页 =====
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
        frame = self.dashboard_frame
        
        self.deadline_frame = tk.Frame(frame, bg=COLORS["bg"])
        self.deadline_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        self.deadline_label = tk.Label(
            self.deadline_frame,
            text="",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            wraplength=600,
            justify="left"
        )
        self.deadline_label.pack()
        
        top_frame = tk.Frame(frame, bg=COLORS["bg"])
        top_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        left_frame = tk.Frame(top_frame, bg=COLORS["bg"])
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        add_card = self.create_card(left_frame, "Add Subject")
        
        tk.Label(add_card, text="Subject Name:", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.name_entry = tk.Entry(add_card, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        tk.Label(add_card, text="Weekly Hours (0-24):", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.hours_entry = tk.Entry(add_card, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.hours_entry.pack(fill="x", pady=(0, 10))
        
        tk.Label(add_card, text="Priority:", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.priority_var = tk.StringVar(value="Medium")
        priority_menu = ttk.Combobox(
            add_card,
            textvariable=self.priority_var,
            values=User.PRIORITIES,
            state="readonly",
            font=(FONT_FAMILY, 11)
        )
        priority_menu.pack(fill="x", pady=(0, 10))
        
        tk.Label(add_card, text="Deadline (DD/MM/YYYY, optional):", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.deadline_entry = tk.Entry(add_card, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.deadline_entry.pack(fill="x", pady=(0, 10))
        
        tk.Label(add_card, text="Goal Hours (target per week):", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.goal_entry = tk.Entry(add_card, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.goal_entry.pack(fill="x", pady=(0, 10))
        self.goal_entry.insert(0, "5")
        
        tk.Label(add_card, text="Target Grade (optional):", bg=COLORS["card_bg"], fg=COLORS["text"]).pack(anchor="w", pady=(5, 0))
        self.grade_entry = tk.Entry(add_card, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.grade_entry.pack(fill="x", pady=(0, 15))
        
        tk.Button(
            add_card,
            text="Add Subject",
            command=self.add_subject,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 11, "bold"),
            relief="solid",
            cursor="hand2",
            height=2
        ).pack(fill="x")
        
        right_frame = tk.Frame(top_frame, bg=COLORS["bg"])
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        list_card = self.create_card(right_frame, "My Subjects")
        self.subject_list = tk.Text(
            list_card,
            height=18,
            font=(FONT_FAMILY, 10),
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
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 10),
            relief="solid",
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="Clear All Subjects",
            command=self.clear_all_subjects,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 10),
            relief="solid",
            cursor="hand2"
        ).pack(side="left", padx=5)
    
          def add_subject(self):
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
            print(f"✅ Subject '{name}' added, total subjects: {len(self.user.subjects)}")
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
    
    def update_deadline_alert(self):
        if not self.user.subjects:
            self.deadline_label.config(text="", bg=COLORS["bg"])
            return
        
        upcoming = []
        today = datetime.now()
        
        for name, data in self.user.subjects.items():
            if data.get("deadline"):
                try:
                    deadline_date = datetime.strptime(data["deadline"], DATE_FORMAT)
                    days_left = (deadline_date - today).days
                    if 0 <= days_left <= 7:
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
        self.deadline_label.config(text=alert_text, fg=COLORS["delete"], bg=COLORS["bg"])
    
    def update_display(self):
        self.subject_list.config(fg=COLORS["text"])
        self.plan_display.config(fg=COLORS["text"])
        self.weekly_plan_display.config(fg=COLORS["text"])
        self.stats_display.config(fg=COLORS["text"])
        
        self.update_deadline_alert()
        
        self.subject_list.delete(1.0, tk.END)
        if not self.user.subjects:
            self.subject_list.insert(tk.END, "No subjects yet. Add one above!")
            return
        
        for name, data in self.user.subjects.items():
            goal_hours = data.get("goal_hours", data["hours"])
            grade = data.get("target_grade", "")
            goal_str = f"Goal: {goal_hours}h" if goal_hours else ""
            grade_str = f"Target: {grade}" if grade else ""
            deadline_str = ""
            if data.get("deadline"):
                try:
                    deadline_date = datetime.strptime(data["deadline"], DATE_FORMAT)
                    days_left = (deadline_date - datetime.now()).days
                    if days_left < 0:
                        deadline_str = f"  ⚠️ OVERDUE!"
                    elif days_left <= 3:
                        deadline_str = f"  🔴 DUE IN {days_left} DAYS!"
                    elif days_left <= 7:
                        deadline_str = f"  🟡 Due in {days_left} days"
                    else:
                        deadline_str = f"  📅 Due: {data['deadline']}"
                except ValueError:
                    deadline_str = f"  📅 Due: {data['deadline']}"
            self.subject_list.insert(
                tk.END,
                f"{name}  {data['hours']}h/wk  [{data['priority']}]  {goal_str} {grade_str} {deadline_str}\n"
            )
        
        self.update_stats()
        self.update_pomodoro_stats()
        self.update_tasks_display()
    
    def select_subject(self):
        try:
            selection = self.subject_list.tag_ranges(tk.SEL)
            if selection:
                selected = self.subject_list.get(tk.SEL_FIRST, tk.SEL_LAST)
                name = selected.split()[0]
                self.selected_subject = name
        except Exception:
            pass
    
    def delete_subject(self):
        if hasattr(self, 'selected_subject') and self.selected_subject:
            if messagebox.askyesno("Confirm", f"Delete '{self.selected_subject}'?"):
                self.user.delete_subject(self.selected_subject)
                DataManager.save_users(AuthWindow.users)
                self.update_display()
                self.selected_subject = None
        else:
            messagebox.showwarning("No Selection", "Click on a subject to select it.")
    
    def clear_all_subjects(self):
        if not self.user.subjects:
            messagebox.showinfo("Info", "No subjects to clear.")
            return
        if messagebox.askyesno("Confirm", "Delete ALL subjects?"):
            self.user.subjects = {}
            DataManager.save_users(AuthWindow.users)
            self.update_display()
    
    # ==========================================
    # PLAN TAB
    # ==========================================
    def setup_plan_tab(self):
        frame = self.plan_frame
        
        daily_card = self.create_card(frame, "Generate Daily Plan")
        row = tk.Frame(daily_card, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=5)
        
        tk.Label(row, text="Hours per day:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 11)).pack(side="left")
        self.avail_entry = tk.Entry(row, width=10, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.avail_entry.pack(side="left", padx=10)
        self.avail_entry.insert(0, "3")
        
        tk.Button(
            row,
            text="Generate Today's Plan",
            command=self.generate_today_plan,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 10, "bold"),
            relief="solid",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        self.plan_display = tk.Text(
            daily_card,
            height=8,
            font=(FONT_FAMILY, 10),
            bg=COLORS["entry_bg"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.plan_display.pack(fill="both", expand=True, pady=(10, 0))
        
        weekly_card = self.create_card(frame, "Weekly Plan")
        control_frame = tk.Frame(weekly_card, bg=COLORS["card_bg"])
        control_frame.pack(fill="x", pady=5)
        
        tk.Label(control_frame, text="Days:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 11)).pack(side="left")
        self.days_entry = tk.Entry(control_frame, width=5, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.days_entry.pack(side="left", padx=10)
        self.days_entry.insert(0, "7")
        
        tk.Button(
            control_frame,
            text="Generate Weekly Plan",
            command=self.generate_weekly_plan,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 10, "bold"),
            relief="solid",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        tk.Button(
            control_frame,
            text="Export Report",
            command=self.export_report,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 10, "bold"),
            relief="solid",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        self.weekly_plan_display = tk.Text(
            weekly_card,
            height=12,
            font=(FONT_FAMILY, 10),
            bg=COLORS["entry_bg"],
            fg=COLORS["text"],
            relief="flat",
            bd=0,
            wrap="word"
        )
        self.weekly_plan_display.pack(fill="both", expand=True, pady=(10, 0))
    
    def generate_today_plan(self):
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
    
    def generate_weekly_plan(self):
        try:
            avail_str = self.avail_entry.get().strip()
            available = float(avail_str) if avail_str else 3
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
        try:
            avail_str = self.avail_entry.get().strip()
            available = float(avail_str) if avail_str else 3
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
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    # ==========================================
    # PROGRESS TAB
    # ==========================================
    def setup_progress_tab(self):
        frame = self.progress_frame
        
        log_card = self.create_card(frame, "Log Study Time")
        row = tk.Frame(log_card, bg=COLORS["card_bg"])
        row.pack(fill="x", pady=5)
        
        tk.Label(row, text="Date:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 11)).pack(side="left")
        self.log_date_entry = tk.Entry(row, width=12, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.log_date_entry.pack(side="left", padx=5)
        self.log_date_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
        
        tk.Label(row, text="Subject:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 11)).pack(side="left", padx=(10, 0))
        self.log_subject_var = tk.StringVar()
        self.log_subject_menu = ttk.Combobox(
            row,
            textvariable=self.log_subject_var,
            values=list(self.user.subjects.keys()),
            state="readonly",
            width=12
        )
        self.log_subject_menu.pack(side="left", padx=5)
        
        tk.Label(row, text="Hours:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 11)).pack(side="left", padx=(10, 0))
        self.log_hours_entry = tk.Entry(row, width=8, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.log_hours_entry.pack(side="left", padx=5)
        
        tk.Button(
            row,
            text="Log Time",
            command=self.log_study_time,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 10, "bold"),
            relief="solid",
            cursor="hand2"
        ).pack(side="left", padx=10)
        
        stats_card = self.create_card(frame, "Statistics & Goals")
        self.stats_display = tk.Text(
            stats_card,
            height=10,
            font=(FONT_FAMILY, 10),
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
                font=(FONT_FAMILY, 8),
                fill=COLORS["text"]
            )
            canvas.create_text(
                x + bar_width / 2,
                height - 22 - bar_height,
                text=f"{hours:.1f}h",
                font=(FONT_FAMILY, 7),
                fill=COLORS["text"]
            )
            x += bar_width + 10
    
    # ==========================================
    # FOCUS TAB
    # ==========================================
    def setup_focus_tab(self):
        frame = self.focus_frame
        
        timer_card = self.create_card(frame, "Pomodoro Timer")
        
        settings_row = tk.Frame(timer_card, bg=COLORS["card_bg"])
        settings_row.pack(pady=10)
        
        tk.Label(settings_row, text="Work (min):", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 11)).pack(side="left", padx=5)
        self.work_min_entry = tk.Entry(settings_row, width=5, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.work_min_entry.pack(side="left", padx=5)
        self.work_min_entry.insert(0, str(self.user.work_minutes))
        
        tk.Label(settings_row, text="Break (min):", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 11)).pack(side="left", padx=10)
        self.break_min_entry = tk.Entry(settings_row, width=5, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.break_min_entry.pack(side="left", padx=5)
        self.break_min_entry.insert(0, str(self.user.break_minutes))
        
        tk.Button(
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
        
        self.start_btn = tk.Button(
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
        
        self.pause_btn = tk.Button(
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
        
        self.reset_btn = tk.Button(
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
        tk.Label(row, text="Pomodoros Today:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 11)).pack(side="left")
        self.pomodoro_count_label = tk.Label(row, text="0", bg=COLORS["card_bg"], fg=COLORS["accent"], font=(FONT_FAMILY, 14, "bold"))
        self.pomodoro_count_label.pack(side="left", padx=10)
        
        row2 = tk.Frame(stats_card, bg=COLORS["card_bg"])
        row2.pack(fill="x", pady=5)
        tk.Label(row2, text="Focus Time Today:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 11)).pack(side="left")
        self.focus_time_label = tk.Label(row2, text="0 min", bg=COLORS["card_bg"], fg=COLORS["accent"], font=(FONT_FAMILY, 14, "bold"))
        self.focus_time_label.pack(side="left", padx=10)
    
    def apply_timer_settings(self):
        try:
            work = int(self.work_min_entry.get().strip())
            break_min = int(self.break_min_entry.get().strip())
            if work <= 0 or break_min < 0:
                raise ValueError
            self.user.work_minutes = work
            self.user.break_minutes = break_min
            self.pomodoro_remaining = work * 60
            self.pomodoro_is_work = True
            self.timer_label.config(text=f"{work:02d}:00")
            self.timer_status.config(text="Work Time")
            self.progress_label.config(text="████████░░░░░░░░░░")
            DataManager.save_users(AuthWindow.users)
            messagebox.showinfo("Success", f"Timer set: {work} min work, {break_min} min break")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers (work > 0, break >= 0)")
    
    def update_pomodoro_stats(self):
        self.pomodoro_count_label.config(text=str(self.user.pomodoro_count))
        self.focus_time_label.config(text=f"{self.user.focus_time_today} min")
    
    def start_pomodoro(self):
        if self.pomodoro_remaining <= 0:
            self.reset_pomodoro()
        self.pomodoro_running = True
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.update_pomodoro()
    
    def pause_pomodoro(self):
        self.pomodoro_running = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        if self.pomodoro_timer_id:
            self.root.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None
    
    def reset_pomodoro(self):
        self.pomodoro_running = False
        self.pomodoro_is_work = True
        self.pomodoro_remaining = self.user.work_minutes * 60
        if self.pomodoro_timer_id:
            self.root.after_cancel(self.pomodoro_timer_id)
            self.pomodoro_timer_id = None
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.timer_label.config(text=f"{self.user.work_minutes:02d}:00")
        self.timer_status.config(text="Work Time")
        self.progress_label.config(text="████████░░░░░░░░░░")
    
    def update_pomodoro(self):
        if not self.pomodoro_running:
            return
        if self.pomodoro_remaining <= 0:
            self.timer_complete()
            return
        self.pomodoro_remaining -= 1
        self.update_timer_display()
        self.pomodoro_timer_id = self.root.after(1000, self.update_pomodoro)
    
    def update_timer_display(self):
        mins = self.pomodoro_remaining // 60
        secs = self.pomodoro_remaining % 60
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
        total = self.user.work_minutes * 60 if self.pomodoro_is_work else self.user.break_minutes * 60
        if total <= 0:
            return
        progress = (total - self.pomodoro_remaining) / total
        filled = int(progress * 16)
        bar = "█" * filled + "░" * (16 - filled)
        self.progress_label.config(text=bar)
    
    def timer_complete(self):
        self.pomodoro_running = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        
        if self.pomodoro_is_work:
            self.user.pomodoro_count += 1
            self.user.focus_time_today += self.user.work_minutes
            DataManager.save_users(AuthWindow.users)
            self.update_pomodoro_stats()
            messagebox.showinfo("Timer Complete", f"Work session complete! Take a {self.user.break_minutes} minute break.")
            self.pomodoro_is_work = False
            self.pomodoro_remaining = self.user.break_minutes * 60
            self.timer_status.config(text="Break Time")
        else:
            messagebox.showinfo("Break Complete", "Break is over! Time to focus again.")
            self.pomodoro_is_work = True
            self.pomodoro_remaining = self.user.work_minutes * 60
            self.timer_status.config(text="Work Time")
        
        self.update_timer_display()
        self.progress_label.config(text="████████░░░░░░░░░░")
        self.pomodoro_timer_id = None
    
    # ==========================================
    # TASKS TAB - 改成表格样式
    # ==========================================
    def setup_tasks_tab(self):
        frame = self.tasks_frame
        
        # 添加任务区域
        add_card = self.create_card(frame, "Add Task")
        
        row1 = tk.Frame(add_card, bg=COLORS["card_bg"])
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Task Title:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 10)).pack(side="left", padx=5)
        self.task_title_entry = tk.Entry(row1, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"], width=25)
        self.task_title_entry.pack(side="left", padx=5)
        
        row2 = tk.Frame(add_card, bg=COLORS["card_bg"])
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Subject:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 10)).pack(side="left", padx=5)
        self.task_subject_var = tk.StringVar()
        self.task_subject_menu = ttk.Combobox(
            row2,
            textvariable=self.task_subject_var,
            values=list(self.user.subjects.keys()),
            state="readonly",
            width=15
        )
        self.task_subject_menu.pack(side="left", padx=5)
        tk.Label(row2, text="(optional)", bg=COLORS["card_bg"], fg=COLORS["text_light"], font=(FONT_FAMILY, 9)).pack(side="left")
        
        row3 = tk.Frame(add_card, bg=COLORS["card_bg"])
        row3.pack(fill="x", pady=2)
        tk.Label(row3, text="Priority:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 10)).pack(side="left", padx=5)
        self.task_priority_var = tk.StringVar(value="Medium")
        task_priority_menu = ttk.Combobox(
            row3,
            textvariable=self.task_priority_var,
            values=User.PRIORITIES,
            state="readonly",
            width=8
        )
        task_priority_menu.pack(side="left", padx=5)
        
        tk.Label(row3, text="Deadline (DD/MM/YYYY):", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 10)).pack(side="left", padx=(15, 5))
        self.task_deadline_entry = tk.Entry(row3, font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"], width=12)
        self.task_deadline_entry.pack(side="left", padx=5)
        
        tk.Button(
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
        
        # 任务列表区域 - 改用 Treeview 表格
        list_card = self.create_card(frame, "My Tasks")
        
        # 统计信息
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
        
        tk.Button(
            stats_row,
            text="Clear Completed",
            command=self.clear_completed_tasks,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 9),
            relief="solid",
            cursor="hand2"
        ).pack(side="right")
        
        # 用 Treeview 代替 Text
        columns = ("Date", "Subject", "Task", "Status")
        self.task_tree = ttk.Treeview(
            list_card,
            columns=columns,
            show="headings",
            height=10
        )
        
        # 定义列头
        self.task_tree.heading("Date", text="Date")
        self.task_tree.heading("Subject", text="Subject")
        self.task_tree.heading("Task", text="Task")
        self.task_tree.heading("Status", text="Status")
        
        # 设置列宽
        self.task_tree.column("Date", width=100, anchor="center")
        self.task_tree.column("Subject", width=100, anchor="center")
        self.task_tree.column("Task", width=280, anchor="w")
        self.task_tree.column("Status", width=80, anchor="center")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_card, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # 绑定双击事件切换任务状态
        self.task_tree.bind("<Double-1>", self.on_task_double_click)
    
    def add_task(self):
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
    
    def on_task_double_click(self, event):
        """双击任务切换完成状态"""
        selected = self.task_tree.selection()
        if not selected:
            return
        
        # 获取选中行的 Task ID
        item = selected[0]
        task_id = int(self.task_tree.item(item, "text"))
        self.user.toggle_task(task_id)
        DataManager.save_users(AuthWindow.users)
        self.update_tasks_display()
    
    def update_tasks_display(self):
        # 清空 Treeview
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # 更新科目下拉列表
        self.task_subject_menu["values"] = list(self.user.subjects.keys())
        
        # 更新统计
        total = self.user.get_task_count()
        completed = self.user.get_completed_count()
        self.task_stats_label.config(text=f"Total: {total}  |  Completed: {completed}  |  Pending: {total - completed}")
        
        if not self.user.tasks:
            # 显示空状态消息
            empty_msg = ttk.Label(self.task_tree, text="No tasks yet. Add one above!", font=(FONT_FAMILY, 10))
            # 无法直接放入 Treeview，用占位行代替
            return
        
        # 未完成的在前
        tasks = sorted(self.user.tasks, key=lambda t: (t["completed"], t["id"]))
        
        for task in tasks:
            status = "✔ Done" if task["completed"] else "⏳ Pending"
            subject = task.get("subject") or "-"
            deadline = task.get("deadline") or "-"
            
            # 把 task_id 存到 item 的 text 属性里
            item = self.task_tree.insert("", "end", text=str(task["id"]), values=(
                deadline,
                subject,
                task["title"],
                status
            ))
            
            # 如果已完成，文字变灰
            if task["completed"]:
                self.task_tree.item(item, tags=("completed",))
        
        # 配置已完成的样式
        self.task_tree.tag_configure("completed", foreground=COLORS["text_light"])
    
    def clear_completed_tasks(self):
        if not self.user.tasks:
            messagebox.showinfo("Info", "No tasks to clear.")
            return
        
        completed = [t for t in self.user.tasks if t["completed"]]
        if not completed:
            messagebox.showinfo("Info", "No completed tasks.")
            return
        
        if messagebox.askyesno("Confirm", f"Delete {len(completed)} completed task(s)?"):
            self.user.tasks = [t for t in self.user.tasks if not t["completed"]]
            DataManager.save_users(AuthWindow.users)
            self.update_tasks_display()
            messagebox.showinfo("Success", "Completed tasks cleared.")
    
    # ==========================================
    # SETTINGS TAB
    # ==========================================
    def setup_settings_tab(self):
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
        tk.Label(pw_card, text="Current Password:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 10)).pack(anchor="w", pady=(5, 0))
        self.old_pw_entry = tk.Entry(pw_card, show="●", font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.old_pw_entry.pack(fill="x", pady=(0, 10))
        
        tk.Label(pw_card, text="New Password (min 6):", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 10)).pack(anchor="w", pady=(5, 0))
        self.new_pw_entry = tk.Entry(pw_card, show="●", font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.new_pw_entry.pack(fill="x", pady=(0, 10))
        
        tk.Label(pw_card, text="Confirm New Password:", bg=COLORS["card_bg"], fg=COLORS["text"], font=(FONT_FAMILY, 10)).pack(anchor="w", pady=(5, 0))
        self.confirm_pw_entry = tk.Entry(pw_card, show="●", font=(FONT_FAMILY, 11), fg=COLORS["text"], bg=COLORS["entry_bg"])
        self.confirm_pw_entry.pack(fill="x", pady=(0, 15))
        
        tk.Button(
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
        
        tk.Button(
            data_card,
            text="Clear All Study Data",
            command=self.clear_data,
            bg=COLORS["accent"],
            fg=COLORS["text_white"],
            font=(FONT_FAMILY, 11),
            relief="solid",
            cursor="hand2"
        ).pack(fill="x", pady=5)
        
        # ===== 新增：导出数据到文本文件 =====
        tk.Button(
            data_card,
            text="Export All Data to .txt File",
            command=self.export_data_to_txt,
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
        
        tk.Button(
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
        if not self.user.subjects and not self.user.logs and not self.user.tasks:
            messagebox.showinfo("Info", "No data to clear.")
            return
        if messagebox.askyesno("Confirm", "Delete ALL subjects, logs, and tasks?"):
            self.user.subjects = {}
            self.user.logs = {}
            self.user.tasks = []
            self.user.pomodoro_count = 0
            self.user.focus_time_today = 0
            DataManager.save_users(AuthWindow.users)
            self.update_display()
            messagebox.showinfo("Success", "Data cleared.")
    
    # ===== 新增：导出数据到文本文件 =====
    def export_data_to_txt(self):
        """Export all user data to a .txt file."""
        filename = f"{self.user.username}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, "w") as f:
                # 标题
                f.write("=" * 60 + "\n")
                f.write(f"StudyMate Data Export - {self.user.username}\n")
                f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write("=" * 60 + "\n\n")
                
                # 1. Subjects
                f.write("SUBJECTS\n")
                f.write("-" * 40 + "\n")
                if self.user.subjects:
                    for name, data in self.user.subjects.items():
                        deadline = data.get("deadline") or "No deadline"
                        f.write(f"  {name}: {data['hours']} hours/week  [{data['priority']}]  Due: {deadline}\n")
                else:
                    f.write("  No subjects added yet.\n")
                f.write("\n")
                
                # 2. Tasks
                f.write("TASKS\n")
                f.write("-" * 40 + "\n")
                if self.user.tasks:
                    for task in self.user.tasks:
                        status = "Done" if task["completed"] else "Pending"
                        subject = task.get("subject") or "-"
                        deadline = task.get("deadline") or "-"
                        f.write(f"  {task['title']}  |  Subject: {subject}  |  Due: {deadline}  |  Status: {status}\n")
                else:
                    f.write("  No tasks added yet.\n")
                f.write("\n")
                
                # 3. Study Logs
                f.write("STUDY LOGS\n")
                f.write("-" * 40 + "\n")
                if self.user.logs:
                    for date, logs in sorted(self.user.logs.items()):
                        f.write(f"  {date}:\n")
                        for subject, hours in logs.items():
                            f.write(f"    {subject}: {hours} hours\n")
                else:
                    f.write("  No study logs recorded yet.\n")
                f.write("\n")
                
                # 4. Statistics
                f.write("STATISTICS\n")
                f.write("-" * 40 + "\n")
                total_hours = self.user.get_total_study_hours()
                f.write(f"  Total study hours: {total_hours}\n")
                f.write(f"  Number of subjects: {len(self.user.subjects)}\n")
                f.write(f"  Number of tasks: {self.user.get_task_count()}\n")
                f.write(f"  Completed tasks: {self.user.get_completed_count()}\n")
                f.write(f"  Pomodoros completed: {self.user.pomodoro_count}\n")
                f.write(f"  Focus time today: {self.user.focus_time_today} minutes\n")
                f.write("\n")
                
                f.write("=" * 60 + "\n")
                f.write("End of export\n")
            
            messagebox.showinfo("Export Successful", f"Data exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")
    
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


class TestStudyScheduler(unittest.TestCase):
    def setUp(self):
        self.user = User("testuser", hashlib.sha256("password".encode()).hexdigest())
    
    def test_add_subject_valid(self):
        self.user.add_subject("Math", 5, "High", "2026-08-01", 8, "A")
        self.assertIn("Math", self.user.subjects)
        self.assertEqual(self.user.subjects["Math"]["hours"], 5)
    
    def test_add_subject_invalid_name(self):
        with self.assertRaises(ValueError):
            self.user.add_subject("", 5)
    
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
    
    # ===== 新增测试 =====
    def test_add_task(self):
        self.user.add_subject("Math", 5)
        self.user.add_task("Test task", "Math", "15/08/2026", "High")
        self.assertEqual(len(self.user.tasks), 1)
        self.assertEqual(self.user.tasks[0]["title"], "Test task")
    
    def test_toggle_task(self):
        self.user.add_subject("Math", 5)
        self.user.add_task("Test task", "Math")
        task_id = self.user.tasks[0]["id"]
        self.user.toggle_task(task_id)
        self.assertTrue(self.user.tasks[0]["completed"])


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main(argv=["first-arg-is-ignored"])
    else:
        AuthWindow.users = DataManager.load_users()
        auth = AuthWindow()
        auth.run()