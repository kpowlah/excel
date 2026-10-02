import csv
import os


def find_file(candidates):
    """Return the first existing file from a list of candidate filenames."""
    for filename in candidates:
        if os.path.exists(filename):
            return filename
    return candidates[0]


def parse_moodle_grades(filepath):
    """
    Parses assessment CSV files (CA1, CA2, Exercises, Final).
    Extracts the maximum possible marks from headers formatted as 'Q. X /Y.YY'
    and sums the student's raw question scores.
    """
    students = {}
    if not os.path.exists(filepath):
        print(f"Warning: File '{filepath}' not found.")
        return students, 0.0

    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        sample = f.readline()
        f.seek(0)
        delimiter = ";" if ";" in sample else ","
        reader = csv.reader(f, delimiter=delimiter)

        headers = next(reader)

        # Extract question column indices and their maximum marks
        q_cols = []
        for i in range(3, len(headers)):
            col_name = headers[i].strip()
            if "/" in col_name:
                try:
                    max_q = float(col_name.split("/")[1].strip())
                    q_cols.append((i, max_q))
                except ValueError:
                    continue

        total_max = sum(max_q for _, max_q in q_cols)

        for row in reader:
            if not row or len(row) < 3:
                continue
            last_name = row[0].strip()
            first_name = row[1].strip()
            student_id = row[2].strip()

            if not student_id:
                continue

            raw_score = 0.0
            for col_idx, _ in q_cols:
                if col_idx < len(row):
                    val = row[col_idx].strip()
                    if val:
                        try:
                            raw_score += float(val)
                        except ValueError:
                            pass

            students[student_id] = {
                "last_name": last_name,
                "first_name": first_name,
                "raw_score": raw_score,
                "max_score": total_max,
            }

    return students, total_max


def parse_project_data(groups_path, project_grades_path):
    """
    Maps student IDs to groups, and groups to their raw project grade out of 10.
    """
    id_to_group = {}
    if os.path.exists(groups_path):
        with open(groups_path, mode="r", encoding="utf-8-sig") as f:
            sample = f.readline()
            f.seek(0)
            delimiter = ";" if ";" in sample else ","
            reader = csv.reader(f, delimiter=delimiter)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2 and row[0].strip():
                    id_to_group[row[0].strip()] = row[1].strip()

    group_to_grade = {}
    total_max = 10.0  # Default project max grade
    if os.path.exists(project_grades_path):
        with open(project_grades_path, mode="r", encoding="utf-8-sig") as f:
            sample = f.readline()
            f.seek(0)
            delimiter = ";" if ";" in sample else ","
            reader = csv.reader(f, delimiter=delimiter)
            header = next(reader, None)
            if header and len(header) >= 2 and "/" in header[1]:
                try:
                    total_max = float(header[1].split("/")[1].strip())
                except ValueError:
                    total_max = 10.0
            for row in reader:
                if len(row) >= 2 and row[0].strip():
                    try:
                        group_to_grade[row[0].strip()] = float(row[1].strip())
                    except ValueError:
                        group_to_grade[row[0].strip()] = 0.0

    return id_to_group, group_to_grade, total_max


def get_sit_grade(total_percent):
    """
    Computes letter grade according to the Singapore Institute of Technology (SIT) standard.
    """
    pct = round(total_percent, 2)
    if pct >= 85.0:
        return "A+"
    elif pct >= 80.0:
        return "A"
    elif pct >= 75.0:
        return "A-"
    elif pct >= 70.0:
        return "B+"
    elif pct >= 65.0:
        return "B"
    elif pct >= 60.0:
        return "B-"
    elif pct >= 55.0:
        return "C+"
    elif pct >= 50.0:
        return "C"
    elif pct >= 45.0:
        return "D+"
    elif pct >= 40.0:
        return "D"
    else:
        return "F"


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

    # Percentage weights
    weights = {
        "CA1": 0.15,
        "CA2": 0.15,
        "EXERCISE": 0.15,
        "FINAL": 0.40,
        "PROJECT": 0.15,
    }

    # Parse assessments and obtain scores and maximum possible marks
    ca1_data, ca1_max = parse_moodle_grades(ca1_file)
    ca2_data, ca2_max = parse_moodle_grades(ca2_file)
    exercise_data, ex_max = parse_moodle_grades(exercise_file)
    final_data, final_max = parse_moodle_grades(final_file)
    id_to_group, group_to_grade, proj_max = parse_project_data(
        groups_file, project_file
    )

    # Fallback to known totals if not parsed from headers
    ca1_max = ca1_max or 21.0
    ca2_max = ca2_max or 16.0
    ex_max = ex_max or 10.0
    final_max = final_max or 50.0
    proj_max = proj_max or 10.0

    # Master list of student IDs
    all_ids = set()
    for d in (ca1_data, ca2_data, exercise_data, final_data):
        all_ids.update(d.keys())
    all_ids.update(id_to_group.keys())
    sorted_ids = sorted(all_ids, key=lambda x: int(x) if x.isdigit() else x)

    # Output headers
    headers = [
        "Last name",
        "First name",
        "ID",
        "CA1 Marks",
        "CA1 (%)",
        "CA2 Marks",
        "CA2 (%)",
        "EXERCISE Marks",
        "EXERCISE (%)",
        "FINAL Marks",
        "FINAL (%)",
        "PROJECT Marks",
        "PROJECT (%)",
        "Total Marks",
        "Total (%)",
        "Grade",
    ]

    compiled_rows = []

    for sid in sorted_ids:
        # Determine student name
        last_name, first_name = "", ""
        for d in (ca1_data, ca2_data, exercise_data, final_data):
            if sid in d and d[sid]["last_name"]:
                last_name = d[sid]["last_name"]
                first_name = d[sid]["first_name"]
                break

        def get_raw_and_pct(data_dict, max_m):
            if sid in data_dict:
                raw = data_dict[sid]["raw_score"]
                actual_max = data_dict[sid]["max_score"] or max_m
            else:
                raw, actual_max = 0.0, max_m
            pct = (raw / actual_max * 100.0) if actual_max > 0 else 0.0
            return raw, pct

        # 1. Marks are out of respective max marks; % is section score out of 100%
        ca1_mark, ca1_pct = get_raw_and_pct(ca1_data, ca1_max)
        ca2_mark, ca2_pct = get_raw_and_pct(ca2_data, ca2_max)
        ex_mark, ex_pct = get_raw_and_pct(exercise_data, ex_max)
        final_mark, final_pct = get_raw_and_pct(final_data, final_max)

        grp = id_to_group.get(sid, "")
        proj_mark = group_to_grade.get(grp, 0.0)
        proj_pct = (proj_mark / proj_max * 100.0) if proj_max > 0 else 0.0

        # 2. Total marks = sum of marks obtained across all sections (out of 107.0 max)
        total_marks = (
            ca1_mark + ca2_mark + ex_mark + final_mark + proj_mark
        )

        # 3. Total (%) = weighted sum based on 15%, 15%, 15%, 40%, 15%
        total_pct = (
            (ca1_pct * weights["CA1"])
            + (ca2_pct * weights["CA2"])
            + (ex_pct * weights["EXERCISE"])
            + (final_pct * weights["FINAL"])
            + (proj_pct * weights["PROJECT"])
        )

        letter_grade = get_sit_grade(total_pct)

        row = [
            last_name,
            first_name,
            sid,
            f"{ca1_mark:.2f}",
            f"{ca1_pct:.2f}",
            f"{ca2_mark:.2f}",
            f"{ca2_pct:.2f}",
            f"{ex_mark:.2f}",
            f"{ex_pct:.2f}",
            f"{final_mark:.2f}",
            f"{final_pct:.2f}",
            f"{proj_mark:.2f}",
            f"{proj_pct:.2f}",
            f"{total_marks:.2f}",
            f"{total_pct:.2f}",
            letter_grade,
        ]
        compiled_rows.append(row)

    # Write compiled CSV using semicolon delimiter
    with open(output_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(compiled_rows)

    print(
        f"Compiled grades successfully written to '{output_file}' ({len(compiled_rows)} students)."
    )


if __name__ == "__main__":
    main()