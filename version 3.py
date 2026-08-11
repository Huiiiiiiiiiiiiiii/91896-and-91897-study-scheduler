import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# ========== 常量 ==========
MAX_HOURS_PER_DAY = 24
MIN_HOURS = 0
SAVE_FILE = "study_plan.json"

# 颜色主题 - 紫色系
COLORS = {
    "bg": "#f3e8ff",           # 浅紫背景
    "frame_bg": "#ffffff",      # 白色卡片
    "accent": "#7c3aed",        # 紫色（主色调）
    "accent_light": "#a78bfa",  # 浅紫色
    "accent_dark": "#5b21b6",   # 深紫色
    "text": "#2d2d5e",          # 深紫蓝文字
    "success": "#10b981",       # 翠绿色（生成按钮）
    "delete": "#ef4444",        # 红色（删除按钮）
}

# ========== 核心函数 ==========
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
            subject_list.insert(tk.END, f"> {name}: {hrs} hours/week\n")

def delete_subject():
    try:
        selection = subject_list.tag_ranges(tk.SEL)
        if not selection:
            messagebox.showwarning("No Selection", "Please click and drag to select a subject to delete.")
            return
        
        selected_text = subject_list.get(tk.SEL_FIRST, tk.SEL_LAST)
        
        if ":" in selected_text:
            text_after_prefix = selected_text.replace(">", "").strip()
            subject_name = text_after_prefix.split(":")[0].strip()
            
            if subject_name in subjects:
                confirm = messagebox.askyesno("Confirm Delete", f"Delete '{subject_name}'?")
                if confirm:
                    del subjects[subject_name]
                    update_display()
                    plan_display.delete(1.0, tk.END)
                    messagebox.showinfo("Deleted", f"Deleted {subject_name}")
            else:
                messagebox.showwarning("Not Found", f"Could not find subject: {subject_name}")
        else:
            messagebox.showwarning("Invalid Selection", "Please select a subject line.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete: {str(e)}")

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
    
    plan_display.delete(1.0, tk.END)
    
    plan_display.insert(tk.END, "=" * 45 + "\n")
    plan_display.insert(tk.END, "           DAILY STUDY PLAN\n")
    plan_display.insert(tk.END, "=" * 45 + "\n\n")
    
    for name, hrs in plan.items():
        plan_display.insert(tk.END, f"  {name}\n")
        bar_length = min(int(hrs * 2), 8)
        bar = "█" * bar_length + "░" * (8 - bar_length)
        plan_display.insert(tk.END, f"  {bar} {hrs} hour(s)\n\n")
    
    plan_display.insert(tk.END, "=" * 45 + "\n")
    plan_display.insert(tk.END, "  Adjust hours for different plans")

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
        plan_display.delete(1.0, tk.END)
        messagebox.showinfo("Loaded", f"Loaded plan from {SAVE_FILE}")
    except Exception as e:
        messagebox.showerror("Load Error", str(e))

# ========== GUI 界面 ==========
root = tk.Tk()
root.title("Personalised Study Scheduler")
root.geometry("600x750")
root.configure(bg=COLORS["bg"])

title_font = ("Helvetica", 16, "bold")
label_font = ("Helvetica", 10)
button_font = ("Helvetica", 10, "bold")

# 标题栏
title_bar = tk.Frame(root, bg=COLORS["accent"], height=50)
title_bar.pack(fill="x")
title_label = tk.Label(title_bar, text="STUDY SCHEDULER", 
                        font=("Helvetica", 18, "bold"), 
                        fg="white", bg=COLORS["accent"])
title_label.pack(pady=10)

subjects = {}

# 输入区域
input_frame = tk.Frame(root, bg=COLORS["frame_bg"], relief="flat", bd=0)
input_frame.pack(fill="x", padx=15, pady=10)

input_card = tk.Frame(input_frame, bg=COLORS["frame_bg"], relief="ridge", bd=1)
input_card.pack(fill="x", padx=5, pady=5)

tk.Label(input_card, text="ADD SUBJECT", font=title_font, 
          fg=COLORS["accent"], bg=COLORS["frame_bg"]).pack(anchor="w", padx=10, pady=(10, 5))

name_row = tk.Frame(input_card, bg=COLORS["frame_bg"])
name_row.pack(fill="x", padx=10, pady=5)
tk.Label(name_row, text="Subject Name:", font=label_font, 
          bg=COLORS["frame_bg"], width=12, anchor="w").pack(side="left")
name_entry = tk.Entry(name_row, font=label_font, width=30, relief="solid", bd=1)
name_entry.pack(side="left", padx=5)

hours_row = tk.Frame(input_card, bg=COLORS["frame_bg"])
hours_row.pack(fill="x", padx=10, pady=5)
tk.Label(hours_row, text="Weekly Hours:", font=label_font, 
          bg=COLORS["frame_bg"], width=12, anchor="w").pack(side="left")
hours_entry = tk.Entry(hours_row, font=label_font, width=10, relief="solid", bd=1)
hours_entry.pack(side="left", padx=5)
tk.Label(hours_row, text="(0-24 hours)", font=("Helvetica", 9), 
          fg="gray", bg=COLORS["frame_bg"]).pack(side="left", padx=5)

add_button = tk.Button(input_card, text="ADD SUBJECT", command=add_subject,
                        bg=COLORS["accent"], fg="white", font=button_font,
                        padx=20, pady=5, relief="flat", cursor="hand2")
add_button.pack(pady=(10, 15))

# 显示区域
display_frame = tk.Frame(root, bg=COLORS["bg"])
display_frame.pack(fill="both", expand=True, padx=15, pady=5)

display_card = tk.Frame(display_frame, bg=COLORS["frame_bg"], relief="ridge", bd=1)
display_card.pack(fill="both", expand=True, padx=5, pady=5)

title_row = tk.Frame(display_card, bg=COLORS["frame_bg"])
title_row.pack(fill="x", padx=10, pady=(10, 0))
tk.Label(title_row, text="CURRENT SUBJECTS", font=title_font,
          fg=COLORS["accent"], bg=COLORS["frame_bg"]).pack(side="left")
tk.Label(title_row, text="(click to select)", font=("Helvetica", 9),
          fg="gray", bg=COLORS["frame_bg"]).pack(side="right")

subject_list = tk.Text(display_card, height=8, width=50, wrap="word",
                        font=("Courier New", 10), bg="#fafafa", relief="flat", bd=0)
subject_list.pack(fill="both", expand=True, padx=10, pady=(5, 10))
subject_list.config(selectbackground=COLORS["accent_light"], selectforeground="white")

# 计划生成区域
plan_frame = tk.Frame(root, bg=COLORS["bg"])
plan_frame.pack(fill="x", padx=15, pady=10)

plan_card = tk.Frame(plan_frame, bg=COLORS["frame_bg"], relief="ridge", bd=1)
plan_card.pack(fill="x", padx=5, pady=5)

tk.Label(plan_card, text="GENERATE DAILY PLAN", font=title_font,
          fg=COLORS["accent"], bg=COLORS["frame_bg"]).pack(anchor="w", padx=10, pady=(10, 5))

avail_row = tk.Frame(plan_card, bg=COLORS["frame_bg"])
avail_row.pack(fill="x", padx=10, pady=5)
tk.Label(avail_row, text="Study hours per day:", font=label_font,
          bg=COLORS["frame_bg"], width=18, anchor="w").pack(side="left")
avail_entry = tk.Entry(avail_row, font=label_font, width=10, relief="solid", bd=1)
avail_entry.pack(side="left", padx=5)
avail_entry.insert(0, "3")
tk.Label(avail_row, text="(e.g., 3 = 3 hours/day)", font=("Helvetica", 9),
          fg="gray", bg=COLORS["frame_bg"]).pack(side="left", padx=5)

generate_button = tk.Button(plan_card, text="GENERATE PLAN", command=generate_plan,
                             bg=COLORS["success"], fg="white", font=button_font,
                             padx=20, pady=5, relief="flat", cursor="hand2")
generate_button.pack(pady=(5, 10))

plan_display = tk.Text(plan_card, height=10, width=50, wrap="word",
                        font=("Courier New", 9), bg="#fafafa", relief="flat", bd=0)
plan_display.pack(fill="both", expand=True, padx=10, pady=(0, 10))

# 按钮区域
button_frame = tk.Frame(root, bg=COLORS["bg"])
button_frame.pack(fill="x", padx=15, pady=10)

save_button = tk.Button(button_frame, text="SAVE PLAN", command=save_plan,
                         bg=COLORS["accent_light"], fg="white", font=button_font,
                         padx=15, pady=5, relief="flat", cursor="hand2")
save_button.pack(side="left", padx=5, expand=True, fill="x")

load_button = tk.Button(button_frame, text="LOAD PLAN", command=load_plan,
                         bg=COLORS["accent_light"], fg="white", font=button_font,
                         padx=15, pady=5, relief="flat", cursor="hand2")
load_button.pack(side="left", padx=5, expand=True, fill="x")

delete_button = tk.Button(button_frame, text="DELETE SUBJECT", command=delete_subject,
                           bg=COLORS["delete"], fg="white", font=button_font,
                           padx=15, pady=5, relief="flat", cursor="hand2")
delete_button.pack(side="left", padx=5, expand=True, fill="x")

# 底部脚注
footer = tk.Label(root, text="Tip: Click on a subject to select it, then click DELETE SUBJECT",
                   font=("Helvetica", 8), fg="gray", bg=COLORS["bg"])
footer.pack(pady=(0, 10))

root.mainloop()