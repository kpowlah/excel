import csv
import os

def find_file(candidates):
    """Return the first existing file from a list of candidate filenames."""
    for filename in candidates:
        if os.path.exists(filename):
            return filename
    return candidates[0]

def main():
    # File locations
    ca1_file = find_file(["Grades CA 1.csv"])
    ca2_file = find_file(["Grades CA 2.csv"])
    exercise_file = find_file(
        ["Grades Exercises.csv"]
    )
    final_file = find_file(
        ["Grades Final Exam.csv"]
    )
    groups_file = find_file(
        ["Groups.csv"]
    )
    project_file = find_file(
        ["Grades Groups.csv"]
    )

    output_file = "compiled_results.csv"