import tkinter as tk
from tkinter import ttk
from ics import Calendar
import requests
from pprint import pprint
URL = ""

assignments_calendar = Calendar(requests.get(URL).text)
course_assignments = {}
selected_course = None
for assignment in assignments_calendar.events:
    for category in assignment.categories:
        if category not in course_assignments:
            course_assignments[category] = []
        course_assignments[category].append(
            {"name": assignment.name, "description": assignment.description})


def on_select(event):
    global selected_course
    print(course_assignments.keys())
    selected_course = course_assignments[event.widget.selection_get()]
    update_assignments()


def update_assignments():
    assignment_list.delete(0, tk.END)
    for assignment in selected_course:
        print(assignment)
        assignment_list.insert(tk.END, assignment["name"])


window = tk.Tk()
window.title("Todo")


course_list = tk.Listbox(window, selectmode=tk.EXTENDED)
course_list.grid(row=0, column=0, rowspan=2, sticky="ns")
course_list.bind("<<ListboxSelect>>", on_select)


for course in course_assignments.keys():
    course_list.insert(tk.END, course)


assignment_list = tk.Listbox(window)
assignment_list.grid(row=1, column=1, sticky="nsew")

window.columnconfigure(1, weight=1)
window.rowconfigure(1, weight=1)

window.mainloop()
