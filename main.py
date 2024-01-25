import tkinter as tk
from tkinter import simpledialog
import os
import sys
import subprocess
import webbrowser

from ics import Calendar
import requests
from dotenv import load_dotenv
import arrow
from tempfile import NamedTemporaryFile

load_dotenv()

MOODLE_URL = "https://m41.carroll.edu"

URL = os.environ.get("URL", None)
if URL is None:
    webbrowser.open(f"{MOODLE_URL}/calendar/export.php")
    URL = simpledialog.askstring("Enter Moodle Calendar URL",
                                 f"Go to {MOODLE_URL}/calendar/export.php, generate a calendar URL, and paste it here.")
    if URL:
        with open(".env", "w") as f:
            f.write(f"URL={URL}")


assignments_calendar = Calendar(requests.get(URL).text)
course_assignments = {}
selected_course = None
selected_assignment = None


for assignment in assignments_calendar.events:
    for category in assignment.categories:
        if category not in course_assignments:
            course_assignments[category] = []
        assignment.name = assignment.name.replace("is due", "")
        assignment.name = assignment.name.split(" - Due")[0]
        assignment.name = assignment.name.split(" - due")[0]
        assignment.name = assignment.name.split(" should be completed")[0]
        if assignment.end > arrow.now():
            course_assignments[category].append(
                assignment)
    course_assignments[category] = sorted(
        course_assignments[category], key=lambda x: x.end)


def on_select_course(event):
    if event.widget != course_list:
        return
    selection = course_assignments.get(
        event.widget.selection_get(), None)
    if selection is not None:
        global selected_course
        selected_course = selection
    update_assignments()


def on_select_assignment(event):
    if selected_course is None:
        add_to_calendar_button.grid_remove()
    else:
        add_to_calendar_button.grid(row=3, column=0, sticky="nw")

    if event.widget != assignment_list:
        return

    if selected_course is None:
        return
    global selected_assignment
    for assignment in selected_course:
        if assignment.name == event.widget.selection_get():
            selected_assignment = assignment
            break

    assignment_title.set(selected_assignment.name)
    assignment_description.set(selected_assignment.description)
    assignment_deadline.set("Due "+selected_assignment.begin.humanize())


def add_to_calendar():
    single_event_calendar = Calendar()
    single_event_calendar.events.add(selected_assignment)
    ical_file = NamedTemporaryFile(mode="w", suffix=".ics", delete=False)
    ical_file.writelines(single_event_calendar.serialize_iter())
    ical_file.close()
    open_file(ical_file.name)


def open_file(filename):
    """
    Cross platform file opener
    https://stackoverflow.com/questions/17317219/is-there-an-platform-independent-equivalent-of-os-startfile
    """
    if sys.platform == "win32":
        os.startfile(filename)
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.call([opener, filename], stdout=open(
        os.devnull, "wb"), stderr=open(os.devnull, "wb"))


def update_assignments():
    assignment_list.delete(0, tk.END)
    for assignment in selected_course:
        assignment_list.insert(tk.END, assignment.name)
    if selected_course != []:
        max_length = max([len(assignment.name)
                          for assignment in selected_course])
    else:
        max_length = 0
    assignment_list.configure(width=max_length)


def on_resize(event):
    assignment_description_label.config(wraplength=window.winfo_width()-350)


window = tk.Tk()
window.title("Todo")

assignment_title = tk.StringVar()
assignment_deadline = tk.StringVar()
assignment_description = tk.StringVar()

course_list = tk.Listbox(window, selectmode="single")
course_list.grid(row=0, column=0, sticky="nsew")
course_list.bind("<<ListboxSelect>>", on_select_course)


for course in course_assignments.keys():
    course_list.insert(tk.END, course)


assignment_list = tk.Listbox(
    window, selectmode="single")
assignment_list.grid(row=0, column=1, sticky="nsew")
assignment_list.bind("<<ListboxSelect>>", on_select_assignment)

assignment_frame = tk.Frame(window)
assignment_frame.grid(row=0, column=2, sticky="nsew")

assignment_title_label = tk.Label(
    assignment_frame, textvariable=assignment_title, font=("Arial", 16))
assignment_title_label.grid(row=0, column=0, sticky="nw")

assignment_deadline_label = tk.Label(
    assignment_frame, textvariable=assignment_deadline, font=("Arial", 12), anchor="w", justify="left")
assignment_deadline_label.grid(row=1, column=0, sticky="nw")

assignment_description_label = tk.Label(
    assignment_frame, textvariable=assignment_description, font=("Arial", 12), anchor="w", justify="left")
assignment_description_label.grid(row=2, column=0, sticky="nw")

add_to_calendar_button = tk.Button(
    assignment_frame, text="Add to Calendar", command=add_to_calendar)

# window.columnconfigure(0, weight=0)
# window.columnconfigure(1, weight=0)
window.columnconfigure(2, weight=1)
window.rowconfigure(0, weight=1)
window.bind("<Configure>", on_resize)
window.mainloop()
