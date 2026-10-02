"""Grade Consolidation and SIT Letter Grade Calculation Script.

This script aggregates student scores across multiple assessment CSV files
(Continuous Assessments, Exercises, Group Project, and Final Exam), normalizes
each assessment according to its syllabus weighting, calculates the final total
percentage, assigns an SIT letter grade, and exports a compiled CSV report.
"""


def read_assessment(filename):
    """Reads an assessment CSV file and parses individual student question scores.

    Expected CSV format (semicolon-delimited):
        Row 1 (Header): Last name;First name;ID;Q. 1 /2.00;Q. 2 /5.00;...
        Subsequent rows: Student records with scores for each question.

    Args:
        filename (str): Path to the assessment CSV file.

    Returns:
        tuple: (scores, max_mark)
            - scores (dict): Mapping of student_id -> (last_name, first_name,
            total_raw_score)
            - max_mark (float): Sum of maximum marks across all questions
            extracted from the header.
    """
    scores = {}
    max_mark = 0.0

    # 'utf-8-sig' automatically detects and strips the UTF-8 Byte Order Mark (BOM)
    # often prepended when saving CSV files from Microsoft Excel.
    with open(filename, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    # If the file is completely empty, return empty results immediately
    if not lines:
        return scores, max_mark

    # Parse the header row to extract maximum question scores (e.g., "Q. 1 /2.00" -> 2.00)
    # Columns 0, 1, and 2 are Last Name, First Name, and ID; question columns start at index 3.
    header = lines[0].strip().split(";")
    q_max_marks = []
    for col in header[3:]:
        if "/" in col:
            # Extract the number following the slash '/'
            max_val = float(col.split("/")[1].strip())
            q_max_marks.append(max_val)

    # Total maximum possible marks for this assessment
    max_mark = sum(q_max_marks)

    # Process individual student score rows (skipping the header)
    for line in lines[1:]:
        parts = line.strip().split(";")

        # Skip rows that are malformed or missing the student ID column
        if len(parts) < 3 or not parts[2].strip():
            continue

        last_name = parts[0].strip()
        first_name = parts[1].strip()
        student_id = parts[2].strip()

        # Sum question marks starting from column index 3 onwards
        raw_score = 0.0
        for val in parts[3:]:
            val_clean = val.strip()
            if val_clean:
                try:
                    raw_score += float(val_clean)
                except ValueError:
                    # Ignore non-numeric values (e.g., blank entries, remarks)
                    pass

        # Save student record keyed by their unique Student ID
        scores[student_id] = (last_name, first_name, raw_score)

    return scores, max_mark


def get_sit_grade(pct):
    """Maps an overall percentage score to the Singapore Institute of Technology (SIT)

    official letter grading scale.

    Args:
        pct (float): Total cumulative percentage (0.0 to 100.0).

    Returns:
        str: SIT Letter Grade (A+, A, A-, B+, B, B-, C+, C, D+, D, or F).
    """
    # Round to 2 decimal places to prevent floating-point representation quirks
    pct = round(pct, 2)

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
    """Main workflow to load, calculate, normalize, and compile student grades."""
    # -------------------------------------------------------------------------
    # 1. Load Individual Assessments & Final Exam
    # -------------------------------------------------------------------------
    ca1, ca1_max = read_assessment("Grades CA 1.csv")
    ca2, ca2_max = read_assessment("Grades CA 2.csv")
    ex, ex_max = read_assessment("Grades Exercises.csv")
    final, final_max = read_assessment("Grades Final Exam.csv")

    # Fallback maximum marks in case header parsing yields 0.0 or was missing
    ca1_max = ca1_max or 21.0
    ca2_max = ca2_max or 16.0
    ex_max = ex_max or 10.0
    final_max = final_max or 50.0

    # -------------------------------------------------------------------------
    # 2. Load Student-to-Group Mapping (Groups.csv)
    # Expected format: Student ID;Group name (e.g., "12345;Group 3" -> ID "12345", Group "3")
    # -------------------------------------------------------------------------
    id_to_group = {}
    with open("Groups.csv", "r", encoding="utf-8-sig") as f:
        for line in f.readlines()[1:]:  # Skip header row
            parts = line.strip().split(";")
            if len(parts) >= 2 and parts[0].strip():
                sid = parts[0].strip()
                # Clean up group identifier (e.g., "Group 3" -> "3")
                grp = parts[1].strip().replace("Group", "").strip()
                id_to_group[sid] = grp

    # -------------------------------------------------------------------------
    # 3. Load Project Grades by Group (Grades Groups.csv)
    # Expected format: Group name;Grade (e.g., "Group 3;8.5" or header "Group;Grade /10.0")
    # -------------------------------------------------------------------------
    group_to_grade = {}
    proj_max = 10.0  # Default maximum project mark
    with open("Grades Groups.csv", "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
        if lines:
            # Check the header for the maximum mark indicator (e.g., "Grade /10.00")
            header = lines[0].strip().split(";")
            if len(header) >= 2 and "/" in header[1]:
                try:
                    proj_max = float(header[1].split("/")[1].strip())
                except ValueError:
                    proj_max = 10.0

            # Read group grade entries
            for line in lines[1:]:
                parts = line.strip().split(";")
                if len(parts) >= 2 and parts[0].strip():
                    grp = parts[0].strip().replace("Group", "").strip()
                    try:
                        group_to_grade[grp] = float(parts[1].strip())
                    except ValueError:
                        group_to_grade[grp] = 0.0

    # -------------------------------------------------------------------------
    # 4. Consolidate and Sort All Unique Student IDs
    # -------------------------------------------------------------------------
    all_ids = set()
    for d in (ca1, ca2, ex, final):
        all_ids.update(d.keys())
    all_ids.update(id_to_group.keys())

    # Sort student IDs numerically if they consist purely of digits; otherwise alphabetically
    sorted_ids = sorted(all_ids, key=lambda x: int(x) if x.isdigit() else x)

    # -------------------------------------------------------------------------
    # 5. Define Consolidated CSV Header Structure
    # -------------------------------------------------------------------------
    headers = [
        "Last name",
        "First name",
        "ID",
        "Total marks CA 1",
        "Percentage achieved CA 1",
        "Percentage CA 1 normalized to 15 %",
        "Total marks CA 2",
        "Percentage achieved CA 2",
        "Percentage CA 2 normalized to 15 %",
        "Total marks Exercises",
        "Percentage achieved Exercises",
        "Percentage Exercises normalized to 15 %",
        "Project Group",
        "Total marks Project",
        "Percentage achieved Project",
        "Percentage Project normalized to 15 %",
        "Total marks Final Exam",
        "Percentage achieved Final Exam",
        "Percentage Final Exam normalized to 40 %",
        "Total percentage",
        "Overall grade",
    ]

    output_filename = "compiled_results.csv"

    # -------------------------------------------------------------------------
    # 6. Compute Grades and Write Output File
    # -------------------------------------------------------------------------
    with open(output_filename, "w", encoding="utf-8") as out:
        # Write header line using comma delimiter
        out.write(",".join(headers) + "\n")

        for sid in sorted_ids:
            # 6a. Retrieve student name from the first dataset where the ID exists
            last_name, first_name = "", ""
            for dataset in (ca1, ca2, ex, final):
                if sid in dataset:
                    last_name, first_name = dataset[sid][0], dataset[sid][1]
                    break

            # 6b. CA 1 Calculations (Weight: 15%)
            ca1_m = ca1[sid][2] if sid in ca1 else 0.0
            ca1_pct = (ca1_m / ca1_max * 100.0) if ca1_max > 0 else 0.0
            ca1_norm = (ca1_pct / 100.0) * 15.0

            # 6c. CA 2 Calculations (Weight: 15%)
            ca2_m = ca2[sid][2] if sid in ca2 else 0.0
            ca2_pct = (ca2_m / ca2_max * 100.0) if ca2_max > 0 else 0.0
            ca2_norm = (ca2_pct / 100.0) * 15.0

            # 6d. Exercises Calculations (Weight: 15%)
            ex_m = ex[sid][2] if sid in ex else 0.0
            ex_pct = (ex_m / ex_max * 100.0) if ex_max > 0 else 0.0
            ex_norm = (ex_pct / 100.0) * 15.0

            # 6e. Group Project Calculations (Weight: 15%)
            grp = id_to_group.get(sid, "")
            proj_m = group_to_grade.get(grp, 0.0)
            proj_pct = (proj_m / proj_max * 100.0) if proj_max > 0 else 0.0
            proj_norm = (proj_pct / 100.0) * 15.0

            # 6f. Final Exam Calculations (Weight: 40%)
            final_m = final[sid][2] if sid in final else 0.0
            final_pct = (
                (final_m / final_max * 100.0) if final_max > 0 else 0.0
            )
            final_norm = (final_pct / 100.0) * 40.0

            # 6g. Total Cumulative Percentage and SIT Letter Grade
            # Syllabus weights: 15% + 15% + 15% + 15% + 40% = 100%
            total_pct = ca1_norm + ca2_norm + ex_norm + proj_norm + final_norm
            grade = get_sit_grade(total_pct)

            # 6h. Assemble formatted data row (all numerical values formatted to 2 decimal places)
            row = [
                last_name,
                first_name,
                sid,
                f"{ca1_m:.2f}",
                f"{ca1_pct:.2f}",
                f"{ca1_norm:.2f}",
                f"{ca2_m:.2f}",
                f"{ca2_pct:.2f}",
                f"{ca2_norm:.2f}",
                f"{ex_m:.2f}",
                f"{ex_pct:.2f}",
                f"{ex_norm:.2f}",
                grp,
                f"{proj_m:.2f}",
                f"{proj_pct:.2f}",
                f"{proj_norm:.2f}",
                f"{final_m:.2f}",
                f"{final_pct:.2f}",
                f"{final_norm:.2f}",
                f"{total_pct:.2f}",
                grade,
            ]

            out.write(",".join(row) + "\n")

    print(f"Successfully compiled results into '{output_filename}'.")


if __name__ == "__main__":
    main()