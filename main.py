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

# The base URL for the moodle instance
# Only used to help the user get the REAL calendar url
MOODLE_URL = "https://m41.carroll.edu"

# Read URL from '.env' file
URL = os.environ.get("URL", None)

assignments_calendar = None
try:
    # Attempt to load and parse the calendar
    assignments_calendar = Calendar(requests.get(URL).text)
except requests.exceptions.RequestException:
    # If parsing fails, reprompt for url
    URL = None

if URL is None:
    # There is no calendar URL saved yet!
    # Open the browser to the calendar export page
    webbrowser.open(f"{MOODLE_URL}/calendar/export.php")

    while not assignments_calendar:
        # Ask the user to paste in the URL from the page
        URL = simpledialog.askstring("Enter Moodle Calendar URL",
                                     f"Go to {MOODLE_URL}/calendar/export.php, generate a calendar URL, and paste it here.")

        # Quit if cancel is pressed
        if URL is None:
            exit()

        # Retrieve the calendar and parse it
        try:
            assignments_calendar = Calendar(requests.get(URL).text)
        except requests.exceptions.RequestException:
            pass

        # We've successfully retrieved the calendar, save the url to '.env'
        with open(".env", "w") as f:
            f.write(f"URL={URL}")

# Dictionary with course code as key and list of assignment names as a value
course_assignments = {}
selected_course = None
selected_assignment = None

for assignment in assignments_calendar.events:
    # Moodle uses course codes as event categories
    for category in assignment.categories:
        # Add new courses as keys to the dictionary
        if category not in course_assignments:
            course_assignments[category] = []

        # Try to improve readability of assignment names, since
        # due dates are part of the event
        assignment.name = assignment.name.replace("is due", "")
        assignment.name = assignment.name.split(" - Due")[0]
        assignment.name = assignment.name.split(" - due")[0]
        assignment.name = assignment.name.split(" should be completed")[0]

        # If assignment is past-due, assume it's complete and omit it
        if assignment.end > arrow.now():
            # Add upcoming assignments to the dictionary
            course_assignments[category].append(
                assignment)

# Sort assignment deadlines for all courses
for course, assignment_list in course_assignments.items():
    course_assignments[course] = sorted(
        assignment_list, key=lambda x: x.end)


def on_select_course(event):
    """
    Handle changes in selection for the course list
    """
    # Name of the selected course
    selection = course_assignments.get(
        event.widget.selection_get(), None)

    # Bail out if unselection
    if selection is None:
        return

    # Save the name of the selected course
    global selected_course
    selected_course = selection

    # Update the assignments list
    update_assignments()


def on_select_assignment(event):
    """
    Handle changes in selection for the assignment list
    """

    global selected_assignment
    # Hide the button if no assignment is selected
    if selected_assignment is None:
        add_to_calendar_button.grid_remove()

    # There is no selected course
    # We can't get assignments from a nonexistent course!
    if selected_course is None:
        return

    # Find the selected assignment in the list of assignment events
    for assignment in selected_course:
        if assignment.name == event.widget.selection_get():
            selected_assignment = assignment
            break

    # If we still don't have an assignment somehow, bail
    if selected_assignment is None:
        return

    # Show the button if an assignment is selected
    add_to_calendar_button.grid(row=3, column=0, sticky="nw")

    # Update the UI with the new assigment
    assignment_title.set(selected_assignment.name)
    assignment_description.set(selected_assignment.description)
    assignment_deadline.set("Due "+selected_assignment.begin.humanize())


def add_to_calendar():
    """
    Add the selected assignment to the default calendar program
    """
    # Create a calendar with the selected assignment as the only event
    single_event_calendar = Calendar()
    single_event_calendar.events.add(selected_assignment)

    # Create a temporary file
    ical_file = NamedTemporaryFile(mode="w", suffix=".ics", delete=False)

    # Write the calendar to the file
    ical_file.writelines(single_event_calendar.serialize_iter())
    ical_file.close()

    # Open it using the default calendar program
    open_file(ical_file.name)


def open_file(filename):
    """
    Cross platform file opener
    https://stackoverflow.com/questions/17317219/is-there-an-platform-independent-equivalent-of-os-startfile

    Tested and working on EndeavorOS, hopefully works on other platforms.
    """
    # Use startfile for Windows
    if sys.platform == "win32":
        os.startfile(filename)
        return

    # Use open for MacOS
    # Use xdg-open for Linux
    opener = "open" if sys.platform == "darwin" else "xdg-open"

    # Run the command with the path to the file and silence output
    subprocess.call([opener, filename], stdout=open(
        os.devnull, "wb"), stderr=open(os.devnull, "wb"))


def update_assignments():
    """
    Update the assignment listbox to include all assignments in the selected course
    """
    # Clear the assignment list
    assignment_list.delete(0, tk.END)

    # Re-add each assignment to the listbox
    for assignment in selected_course:
        assignment_list.insert(tk.END, assignment.name)

    # Make the listbox fit the longest assignment name
    if selected_course != []:
        max_length = max([len(assignment.name)
                          for assignment in selected_course])
    else:
        max_length = 0
    assignment_list.configure(width=max_length)


def on_resize(event):
    """
    Wrap text for the assignment description

    NOTE: This can create a loop where wrapping the text alters
    the window size. I haven't found a good fix yet.
    """
    assignment_description_label.config(wraplength=window.winfo_width()-350)


# Create the window
window = tk.Tk()
window.title("Moodle Todos")

# Create the string variables for the assignment info frame
assignment_title = tk.StringVar()
assignment_deadline = tk.StringVar()
assignment_description = tk.StringVar()

# The leftmost list of all courses
course_list = tk.Listbox(window, selectmode="single")
course_list.grid(row=0, column=0, sticky="nsew")
course_list.bind("<<ListboxSelect>>", on_select_course)

# Add all courses to the list
for course in course_assignments.keys():
    course_list.insert(tk.END, course)

# The right list of assignments in the selected course
assignment_list = tk.Listbox(
    window, selectmode="single")
assignment_list.grid(row=0, column=1, sticky="nsew")
assignment_list.bind("<<ListboxSelect>>", on_select_assignment)

# Add a frame for assignment information
assignment_frame = tk.Frame(window)
assignment_frame.grid(row=0, column=2, sticky="nsew")

# Name of the assignment
assignment_title_label = tk.Label(
    assignment_frame, textvariable=assignment_title, font=("Arial", 16))
assignment_title_label.grid(row=0, column=0, sticky="nw")

# Label showing the deadline
assignment_deadline_label = tk.Label(
    assignment_frame, textvariable=assignment_deadline, font=("Arial", 12), anchor="w", justify="left")
assignment_deadline_label.grid(row=1, column=0, sticky="nw")

# Label showing the assigment description
assignment_description_label = tk.Label(
    assignment_frame, textvariable=assignment_description, font=("Arial", 12), anchor="w", justify="left")
assignment_description_label.grid(row=2, column=0, sticky="nw")

# Button allowing the user to add the selected assignment to their default calendar
add_to_calendar_button = tk.Button(
    assignment_frame, text="Add to Calendar", command=add_to_calendar)

# Make the assignment panel take up whatever space the listboxes don't use
window.columnconfigure(2, weight=1)
window.rowconfigure(0, weight=1)

# Add resize listener
window.bind("<Configure>", on_resize)
window.mainloop()
