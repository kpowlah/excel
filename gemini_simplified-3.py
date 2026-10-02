# 1. Helper function to read assessment CSV files using basic string methods
def read_assessment(filename):
    scores = {}
    max_mark = 0.0

    with open(filename, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    if not lines:
        return scores, max_mark

    # Extract maximum possible marks from the header line (e.g., 'Q. 1 /2.00')
    header = lines[0].strip().split(";")
    q_max_marks = []
    for col in header[3:]:
        if "/" in col:
            max_val = float(col.split("/")[1].strip())
            q_max_marks.append(max_val)

    max_mark = sum(q_max_marks)

    # Read each student's question scores
    for line in lines[1:]:
        parts = line.strip().split(";")
        if len(parts) < 3 or not parts[2].strip():
            continue

        last_name = parts[0].strip()
        first_name = parts[1].strip()
        student_id = parts[2].strip()

        # Sum question marks starting from index 3
        raw_score = 0.0
        for val in parts[3:]:
            val_clean = val.strip()
            if val_clean:
                try:
                    raw_score += float(val_clean)
                except ValueError:
                    pass

        scores[student_id] = (last_name, first_name, raw_score)

    return scores, max_mark


# 2. SIT Grading Scale mapping
def get_sit_grade(pct):
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


# 3. Main processing routine
def main():
    # Load all continuous assessments and final exam
    ca1, ca1_max = read_assessment("Grades CA 1.csv")
    ca2, ca2_max = read_assessment("Grades CA 2.csv")
    ex, ex_max = read_assessment("Grades Exercises.csv")
    final, final_max = read_assessment("Grades Final Exam.csv")

    # Fallbacks in case max mark headers were not present
    ca1_max = ca1_max or 21.0
    ca2_max = ca2_max or 16.0
    ex_max = ex_max or 10.0
    final_max = final_max or 50.0

    # Load student-to-group mappings from Groups.csv
    id_to_group = {}
    with open("Groups.csv", "r", encoding="utf-8-sig") as f:
        for line in f.readlines()[1:]:
            parts = line.strip().split(";")
            if len(parts) >= 2 and parts[0].strip():
                sid = parts[0].strip()
                grp = parts[1].strip().replace("Group", "").strip()
                id_to_group[sid] = grp

    # Load project grades from Grades Groups.csv
    group_to_grade = {}
    proj_max = 10.0
    with open("Grades Groups.csv", "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
        if lines:
            header = lines[0].strip().split(";")
            if len(header) >= 2 and "/" in header[1]:
                try:
                    proj_max = float(header[1].split("/")[1].strip())
                except ValueError:
                    proj_max = 10.0

            for line in lines[1:]:
                parts = line.strip().split(";")
                if len(parts) >= 2 and parts[0].strip():
                    grp = parts[0].strip().replace("Group", "").strip()
                    try:
                        group_to_grade[grp] = float(parts[1].strip())
                    except ValueError:
                        group_to_grade[grp] = 0.0

    # Collect and sort all unique student IDs
    all_ids = set()
    for d in (ca1, ca2, ex, final):
        all_ids.update(d.keys())
    all_ids.update(id_to_group.keys())
    sorted_ids = sorted(all_ids, key=lambda x: int(x) if x.isdigit() else x)

    # Define exact CSV column headers
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

    with open(output_filename, "w", encoding="utf-8") as out:
        # Write header row using semicolon delimiter
        out.write(";".join(headers) + "\n")

        for sid in sorted_ids:
            # 1. Names
            last_name, first_name = "", ""
            for dataset in (ca1, ca2, ex, final):
                if sid in dataset:
                    last_name, first_name = dataset[sid][0], dataset[sid][1]
                    break

            # 2. CA 1 (out of 21, normalized to 15%)
            ca1_m = ca1[sid][2] if sid in ca1 else 0.0
            ca1_pct = (ca1_m / ca1_max * 100.0) if ca1_max > 0 else 0.0
            ca1_norm = (ca1_pct / 100.0) * 15.0

            # 3. CA 2 (out of 16, normalized to 15%)
            ca2_m = ca2[sid][2] if sid in ca2 else 0.0
            ca2_pct = (ca2_m / ca2_max * 100.0) if ca2_max > 0 else 0.0
            ca2_norm = (ca2_pct / 100.0) * 15.0

            # 4. Exercises (out of 10, normalized to 15%)
            ex_m = ex[sid][2] if sid in ex else 0.0
            ex_pct = (ex_m / ex_max * 100.0) if ex_max > 0 else 0.0
            ex_norm = (ex_pct / 100.0) * 15.0

            # 5. Project (out of 10, normalized to 15%)
            grp = id_to_group.get(sid, "")
            proj_m = group_to_grade.get(grp, 0.0)
            proj_pct = (proj_m / proj_max * 100.0) if proj_max > 0 else 0.0
            proj_norm = (proj_pct / 100.0) * 15.0

            # 6. Final Exam (out of 50, normalized to 40%)
            final_m = final[sid][2] if sid in final else 0.0
            final_pct = (final_m / final_max * 100.0) if final_max > 0 else 0.0
            final_norm = (final_pct / 100.0) * 40.0

            # 7. Total Percentage and SIT Letter Grade
            total_pct = ca1_norm + ca2_norm + ex_norm + proj_norm + final_norm
            grade = get_sit_grade(total_pct)

            # Assemble student row
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

            out.write(";".join(row) + "\n")

    print(f"Successfully compiled results into '{output_filename}'.")


if __name__ == "__main__":
    main()