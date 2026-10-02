# 1. Helper function to read an assessment CSV file using only basic string methods
def read_assessment(filename):
    scores = {}     #Clear score and max_mark
    max_mark = 0.0

    with open(filename, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()   # Read all lines from the file

    if not lines:
        return scores, max_mark     #return empty if file is empty

    # Read the header row to extract maximum marks for each question
    header = lines[0].strip().split(";")    # Split the header line by semicolon
    q_max_marks = []
    for col in header[3:]:  #skip names and id
        if "/" in col:
            # Splits "Q. 1 /2.00" to get "2.00"
            max_val = float(col.split("/")[1])
            q_max_marks.append(max_val)     # Append the maximum mark for this question

    max_mark = sum(q_max_marks)     # Sum of maximum marks for all questions

    # Read each student's scores
    for line in lines[1:]:
        parts = line.strip().split(";")
        if len(parts) < 3 or not parts[2]:
            continue

        last_name = parts[0].strip()
        first_name = parts[1].strip()
        student_id = parts[2].strip()

        # Sum question marks starting from index 3
        raw_score = 0.0
        for val in parts[3:]:
            if val.strip():
                raw_score += float(val.strip())

        scores[student_id] = (last_name, first_name, raw_score)

    return scores, max_mark


# 2. Function to map SIT grades based on the final total percentage
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
    # Load assessments
    ca1, ca1_max = read_assessment("Grades CA 1.csv")
    ca2, ca2_max = read_assessment("Grades CA 2.csv")
    ex, ex_max = read_assessment("Grades Exercises.csv")
    final, final_max = read_assessment("Grades Final Exam.csv")

    # Load student-to-group mappings from Groups.csv
    id_to_group = {}
    with open("Groups.csv", "r", encoding="utf-8-sig") as f:
        for line in f.readlines()[1:]:
            parts = line.strip().split(";")
            if len(parts) >= 2 and parts[0].strip():
                sid = parts[0].strip()
                # Remove any extra text like 'Group ' leaving just the group number
                grp = parts[1].strip().replace("Group", "").strip()
                id_to_group[sid] = grp

    # Load project grades by group from Grades Project.csv
    group_to_grade = {}
    proj_max = 10.0
    with open("Grades Groups.csv", "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
        if lines:
            # Check header for max marks
            header = lines[0].strip().split(";")
            if len(header) >= 2 and "/" in header[1]:
                proj_max = float(header[1].split("/")[1])

            for line in lines[1:]:
                parts = line.strip().split(";")
                if len(parts) >= 2 and parts[0].strip():
                    grp = parts[0].strip().replace("Group", "").strip()
                    group_to_grade[grp] = float(parts[1].strip())

    # Collect all unique student IDs
    all_ids = set()
    for d in (ca1, ca2, ex, final):
        all_ids.update(d.keys())
    all_ids.update(id_to_group.keys())

    # Sort student IDs numerically
    sorted_ids = sorted(all_ids, key=lambda x: int(x) if x.isdigit() else x)

    # Write the compiled CSV directly using standard string operations
    output_filename = "compiled_results.csv"
    with open(output_filename, "w", encoding="utf-8") as out:
        # Header line
        out.write(
            "Last name;First name;ID;"
            "CA1 Marks;CA1 (%);"
            "CA2 Marks;CA2 (%);"
            "EXERCISE Marks;EXERCISE (%);"
            "FINAL Marks;FINAL (%);"
            "PROJECT Marks;PROJECT (%);"
            "Total Marks;Total (%);Grade\n"
        )

        for sid in sorted_ids:
            # Retrieve student name
            last_name, first_name = "", ""
            for dataset in (ca1, ca2, ex, final):
                if sid in dataset:
                    last_name, first_name = dataset[sid][0], dataset[sid][1]
                    break

            # Section marks and individual % scores
            ca1_m = ca1[sid][2] if sid in ca1 else 0.0
            ca1_pct = (ca1_m / ca1_max * 100.0) if ca1_max > 0 else 0.0

            ca2_m = ca2[sid][2] if sid in ca2 else 0.0
            ca2_pct = (ca2_m / ca2_max * 100.0) if ca2_max > 0 else 0.0

            ex_m = ex[sid][2] if sid in ex else 0.0
            ex_pct = (ex_m / ex_max * 100.0) if ex_max > 0 else 0.0

            final_m = final[sid][2] if sid in final else 0.0
            final_pct = (final_m / final_max * 100.0) if final_max > 0 else 0.0

            # Match project mark via group
            grp = id_to_group.get(sid, "")
            proj_m = group_to_grade.get(grp, 0.0)
            proj_pct = (proj_m / proj_max * 100.0) if proj_max > 0 else 0.0

            # Total marks: sum of raw scores across all components (out of 107.0)
            total_marks = ca1_m + ca2_m + ex_m + final_m + proj_m

            # Total %: weighted percentage (15%, 15%, 15%, 40%, 15%)
            total_pct = (
                (ca1_pct * 0.15)
                + (ca2_pct * 0.15)
                + (ex_pct * 0.15)
                + (final_pct * 0.40)
                + (proj_pct * 0.15)
            )

            grade = get_sit_grade(total_pct)

            # Write formatted line
            out.write(
                f"{last_name};{first_name};{sid};"
                f"{ca1_m:.2f};{ca1_pct:.2f};"
                f"{ca2_m:.2f};{ca2_pct:.2f};"
                f"{ex_m:.2f};{ex_pct:.2f};"
                f"{final_m:.2f};{final_pct:.2f};"
                f"{proj_m:.2f};{proj_pct:.2f};"
                f"{total_marks:.2f};{total_pct:.2f};{grade}\n"
            )

    print(f"Done! Successfully wrote compiled results to '{output_filename}'.")


if __name__ == "__main__":
    main()