
## Readme.md
StudyMate is a Python desktop study-management application designed for senior secondary school students.

The program helps users organise subjects, create daily and weekly study plans, track actual study time, manage tasks and use a Pomodoro timer. User data is saved locally so that information can remain available between sessions.

---

## Requirements

StudyMate requires:

- Python 3
- Python 3.10 or later is recommended
- tkinter support for the graphical user interface
- A desktop or laptop computer

No external third-party Python libraries are required.

StudyMate uses Python Standard Library modules including:

- tkinter
- json
- os
- pathlib
- datetime
- hashlib
- math
- unittest

An internet connection is not required for normal use.

---

## Files

The main files used for the final program are:

main.py
- The main StudyMate application.

test_main.py
- Supplementary automated tests for persistence, boundary and robustness scenarios.

README.md
- Instructions for installing, running and using StudyMate.

data/users.json
- Created automatically when StudyMate saves user data.

---

## How to Run StudyMate

1. Make sure Python 3 is installed.
2. Keep `main.py` in the StudyMate project folder.
3. Open Terminal on macOS or Command Prompt / Terminal on Windows.
4. Navigate to the folder containing `main.py`.

On macOS, run:

    python3 main.py

On Windows, run:

    python main.py

The StudyMate Login window should open.

---

## How to Use StudyMate

### 1. Create an Account or Log In

When StudyMate starts, create a new account or log in to an existing account.

A new account requires:

- Username
- Password
- Password confirmation

The current version requires a username of at least 3 characters and a password of at least 6 characters.

### 2. Add Subjects

Open the Dashboard and enter:

- Subject Name
- Weekly Target Hours
- Priority
- Deadline (optional)
- Target Grade (optional)

Weekly Target Hours represent the total study target across a seven-day period.

StudyMate formats subject names consistently and prevents duplicate subjects such as `Maths`, `maths` and `MATHS`.

### 3. Generate a Study Plan

Open the Plan tab.

For a daily plan:

- Enter the available study hours for today.
- Select `Generate Today's Plan`.

For a weekly plan:

- Enter the maximum available study hours per day.
- Enter the number of days.
- Select `Generate Weekly Plan`.

StudyMate considers:

- weekly target hours
- priority
- approaching deadlines
- available study capacity

Weekly target hours are not repeated automatically every day.

For example, if Maths has a weekly target of 2 hours and a seven-day plan is generated, StudyMate aims to schedule a total of 2 hours across the seven-day period.

### 4. Record Study Progress

Open the Progress tab after studying.

Enter:

- Date
- Subject
- Hours completed

StudyMate compares actual logged hours with the subject's weekly target and displays:

- Desired hours
- Logged hours
- Remaining hours
- Completion percentage
- Visual comparison information

### 5. Use the Pomodoro Timer

Open the Focus tab.

The user can:

- Set the work-session length
- Set the break length
- Start the timer
- Pause the timer
- Reset the timer

The countdown and horizontal progress indicator update while the timer is running.

Completed work sessions update the Pomodoro count and focus-time statistics.

### 6. Manage Tasks

Open the Tasks tab.

Tasks can include:

- Task Title
- Subject (optional)
- Priority
- Deadline

Tasks are displayed in a structured table with Date, Subject, Task and Status columns.

The user can:

- Mark a task complete or incomplete
- Delete a selected task
- Clear completed tasks
- Double-click a task to change its completion status

### 7. Settings

The Settings tab allows the user to:

- Switch between Light Mode and Dark Mode
- Change the account password
- Clear saved study data
- Delete the account

Dark Mode changes the appearance across the StudyMate interface. The selected theme is saved with the user's data so it can be restored when the user logs in again.

Actions that permanently delete information require confirmation.

---

## Data Storage

StudyMate stores user information locally in:

    data/users.json

The program automatically creates the `data` folder when saved data is required.

Saved information includes account data, subjects, study logs, tasks, Pomodoro settings and the selected theme.

Passwords are stored as SHA-256 hashes rather than plain-text passwords.

StudyMate does not send user information to an online server.

---

## Running the Supplementary Tests

Keep `test_main.py` in the same folder as `main.py`.

Run:

    python3 -m unittest -v test_main.py

The supplementary tests check additional persistence, boundary and robustness scenarios.

---

## FAQ

### Why is my study plan not generating?

Make sure at least one subject has been added and that the available study-hours value is greater than zero.

### Why does my weekly plan not use all of the available hours?

Available hours represent maximum capacity. StudyMate does not increase a subject beyond its target simply to fill unused time.

### What does "Weekly Target Hours" mean?

It is the total amount of time the user wants to study that subject across a seven-day period.

### Why can't I add the same subject twice?

StudyMate prevents duplicate subjects to avoid inconsistent data. For example, `Maths`, `maths` and `MATHS` are treated as the same subject.

### What date format should I use?

Use:

    DD/MM/YYYY

For example:

    14/08/2026

### What happens if I enter an invalid number or date?

StudyMate validates the input and displays an instructional error message rather than accepting invalid information.

### What happens if I forget my password?

The current version does not include password recovery.

Deleting `users.json` would reset the stored account data, but it would also remove all other saved accounts and information in that file.

### Does StudyMate require internet access?

No. StudyMate operates locally.

---

## Current Limitations

- StudyMate is designed for desktop/laptop use rather than mobile devices.
- Password recovery is not currently available.
- Interface rendering may vary slightly between macOS and Windows because StudyMate uses tkinter.
- User data is stored locally rather than synchronised online.