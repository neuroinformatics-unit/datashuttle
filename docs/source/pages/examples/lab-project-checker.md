:html_theme.sidebar_secondary.remove:

# Validate all projects in a lab

This example shows how Viktor Plattner (Akrami Lab, [Sainsbury Wellcome Centre](https://www.sainsburywellcome.org/web/)) validates
all of a lab's projects at once, saving a log file of any detected NeuroBlueprint-formatting errors.
This runs weekly to catch any formatting issues introduced into projects.


```python

from datashuttle import DataShuttle
import os

# Define the projects directory
projects_dir = "/mnt/ceph/_projects"

# Get the list of projects
project_list = os.listdir(projects_dir)

# Dictionary to store error messages
error_messages = {}

# Iterate through projects and validate
for p in project_list:
    project_path = os.path.join(projects_dir, p)
    if os.path.isdir(project_path):  # Only process directories
        project = DataShuttle(p)
        try:
            errors = project.validate_project("rawdata", display_mode="print", strict_mode=True)
            error_messages[p] = errors if errors else "No errors"
        except Exception as e:
            error_messages[p] = f"Validation failed: {e}"

# Save log file
log_file = "project_validation.txt"
with open(log_file, "w") as f:
    for project, message in error_messages.items():
        f.write(f"{project}: {message}\n")

# Optional: Print summary of error messages
for project, message in error_messages.items():
    print(f"{project}: {message}")

```
