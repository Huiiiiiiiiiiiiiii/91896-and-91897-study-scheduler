import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


MAX_HOURS_PER_DAY = 24/Users/hueyyyy/Desktop/Screenshot 2026-05-27 at 11.48.44 AM.png
MIN_HOURS = 0
SAVE_FILE = "study_plan.json"


def add_subject():
    name = name_entry.get().strip()
    hours_str = hours_entry.get().strip()
    
    if not name:
        messagebox.showerror("Input Error", "Subject name cannot be empty.")
        return
    
    try:
        hours = float(hours_str)
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid number for hours.")
        return
    
    if hours < MIN_HOURS or hours > MAX_HOURS_PER_DAY:
        messagebox.showerror("Input Error", f"Hours must be between {MIN_HOURS} and {MAX_HOURS_PER_DAY}.")
        return
    
    subjects[name] = hours
    update_display()
    
    name_entry.delete(0, tk.END)
    hours_entry.delete(0, tk.END)
    messagebox.showinfo("Success", f"Added/Updated {name}: {hours} hours/week")

def update_display():
    subject_list.delete(1.0, tk.END)
    if not subjects:
        subject_list.insert(tk.END, "No subjects yet. Add some!")
    else:
        for name, hrs in subjects.items():
            subject_list.insert(tk.END, f"{name}: {hrs} hours/week\n")

def generate_plan():
    avail_str = avail_entry.get().strip()
    
    if not avail_str:
        messagebox.showerror("Plan Error", "Please enter available study hours.")
        return
    
    try:
        available = float(avail_str)
    except ValueError:
        messagebox.showerror("Plan Error", "Please enter a valid number.")
        return
    
    if available < 0:
        messagebox.showerror("Plan Error", "Available hours cannot be negative.")
        return
    
    total_weekly = sum(subjects.values())
    
    if total_weekly == 0:
        plan_display.delete(1.0, tk.END)
        plan_display.insert(tk.END, "No subjects added yet. Add subjects first!")
        return
    
    ratio = available / total_weekly
    plan = {name: round(hours * ratio, 1) for name, hours in subjects.items()}
    
    output = ["===== Your Daily Study Plan =====", ""]
    for name, hrs in plan.items():
        output.append(f"• {name}: {hrs} hour(s)")
    output.append("")
    output.append("=================================")
    
    plan_display.delete(1.0, tk.END)
    plan_display.insert(tk.END, "\n".join(output))

def save_plan():
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(subjects, f, indent=4)
        messagebox.showinfo("Saved", f"Plan saved to {SAVE_FILE}")
    except Exception as e:
        messagebox.showerror("Save Error", str(e))

def load_plan():
    global subjects
    if not os.path.exists(SAVE_FILE):
        messagebox.showwarning("Load Error", f"No saved file found: {SAVE_FILE}")
        return
    
    try:
        with open(SAVE_FILE, "r") as f:
            subjects = json.load(f)
        update_display()
        messagebox.showinfo("Loaded", f"Loaded plan from {SAVE_FILE}")
    except Exception as e:
        messagebox.showerror("Load Error", str(e))

# ========== GUI 界面 ==========
root = tk.Tk()
root.title("Personalised Study Scheduler")
root.geometry("550x520")

subjects = {}

# 输入区域
input_frame = ttk.LabelFrame(root, text="Add / Update Subject", padding=10)
input_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(input_frame, text="Subject Name:").grid(row=0, column=0, sticky="w")
name_entry = ttk.Entry(input_frame, width=25)
name_entry.grid(row=0, column=1, padx=5)

ttk.Label(input_frame, text="Weekly Hours (0-24):").grid(row=1, column=0, sticky="w")
hours_entry = ttk.Entry(input_frame, width=10)
hours_entry.grid(row=1, column=1, sticky="w", padx=5)

add_button = ttk.Button(input_frame, text="Add Subject", command=add_subject)
add_button.grid(row=2, column=0, columnspan=2, pady=5)

# 显示区域
display_frame = ttk.LabelFrame(root, text="Current Subjects", padding=10)
display_frame.pack(fill="both", expand=True, padx=10, pady=5)

subject_list = tk.Text(display_frame, height=8, width=50, wrap="word")
subject_list.pack(fill="both", expand=True)

# 计划生成区域
plan_frame = ttk.LabelFrame(root, text="Generate Daily Plan", padding=10)
plan_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(plan_frame, text="Available study hours per day:").grid(row=0, column=0, sticky="w")
avail_entry = ttk.Entry(plan_frame, width=10)
avail_entry.grid(row=0, column=1, padx=5)
avail_entry.insert(0, "3")

generate_button = ttk.Button(plan_frame, text="Generate Plan", command=generate_plan)
generate_button.grid(row=1, column=0, columnspan=2, pady=5)

plan_display = tk.Text(plan_frame, height=6, width=50, wrap="word")
plan_display.grid(row=2, column=0, columnspan=2, pady=5)

# 文件操作按钮
button_frame = ttk.Frame(root)
button_frame.pack(fill="x", padx=10, pady=5)

save_button = ttk.Button(button_frame, text="Save Plan to File", command=save_plan)
save_button.pack(side="left", padx=5)

load_button = ttk.Button(button_frame, text="Load Plan from File", command=load_plan)
load_button.pack(side="left", padx=5)

root.mainloop()