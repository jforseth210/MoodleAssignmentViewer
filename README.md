# Moodle Assignment Viewer 
This is a simple imap client written in python that allows you to view emails in the console. 

To install this program, you'll need [python](https://www.python.org) and [git](https://git-scm.com) installed.

1. Simply clone the repository using: 
```bash
git clone https://github.com/jforseth210/MoodleAssignmentViewer
cd MoodleAssignmentViewer
```

2. Install the dependencies using: 
```bash
python -m venv venv
venv/bin/activate
pip install -r requirements.txt
```

3. Run the program using: 
```bash
python main.py
```

This program uses moodle's calendar feed to show you your courses and upcoming assignments.  
You can view a courses assignments by clicking on the course name, then view an 
assignment by ckicking on the assignment name in the adjacent list.

Finally, you can add the assignment you're viewing to your calendar program using the "Add to Calendar" button.

