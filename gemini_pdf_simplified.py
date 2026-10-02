import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle


# 1. Read assessment files using standard split operations
def read_assessment(filename):
    scores = {}         #cleat score and max_mark
    max_mark = 0.0

    if not os.path.exists(filename):
        print(f"[-] Warning: '{filename}' not found.")
        return scores, max_mark

    with open(filename, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()       #read all lines at once

    if not lines:
        return scores, max_mark

    # Parse question maximums from header (e.g. 'Q. 1 /2.00')
    header = lines[0].strip().split(";")    #split header by semicolon
    q_max_marks = []
    for col in header[3:]:
        if "/" in col:
            try:
                max_val = float(col.split("/")[1])  #get Q marks
                q_max_marks.append(max_val)     #add to list
            except ValueError:
                continue

    max_mark = sum(q_max_marks)

    # Read each student's question marks
    for line in lines[1:]:
        parts = line.strip().split(";")
        if len(parts) < 3 or not parts[2].strip():
            continue

        last_name = parts[0].strip()
        first_name = parts[1].strip()
        student_id = parts[2].strip()

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


# 2. SIT Grading Scale
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


# 3. ReportLab PDF Generation
def generate_pdf(table_data, pdf_filename="compiled_results.pdf"):
    """Builds a styled, landscape multi-page PDF directly from table rows."""
    if not table_data or len(table_data) <= 1:
        print("[-] Error: No data rows available to generate PDF.")
        return

    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=25,
        bottomMargin=25,
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#A6192E"),  # SIT Crimson
        spaceAfter=10,
    )
    elements.append(
        Paragraph("Singapore Institute of Technology – Student Grades Report", title_style)
    )

    # 16 column widths across landscape A4 (approx 800 pt total)
    col_widths = [
        60,
        55,
        45,  # Last Name, First Name, ID
        45,
        45,  # CA1 Marks, %
        45,
        45,  # CA2 Marks, %
        48,
        48,  # EXERCISE Marks, %
        48,
        48,  # FINAL Marks, %
        48,
        48,  # PROJECT Marks, %
        52,
        52,  # Total Marks, %
        38,  # Grade
    ]

    grade_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    grade_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 5.5),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 6.5),
                ("ALIGN", (0, 1), (1, -1), "LEFT"),
                ("ALIGN", (2, 1), (-1, -1), "CENTER"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F8F9FA")],
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#BDC3C7"),
                ),
            ]
        )
    )

    elements.append(grade_table)
    doc.build(elements)
    print(f"[✓] PDF successfully generated: '{pdf_filename}'")


# 4. Main Workflow
def main():
    # Load assessments
    ca1, ca1_max = read_assessment("Grades CA 1.csv")
    ca2, ca2_max = read_assessment("Grades CA 2.csv")
    ex, ex_max = read_assessment("Grades Exercises.csv")
    final, final_max = read_assessment("Grades Final Exam.csv")

    # Defaults in case question max marks were missing
    ca1_max = ca1_max or 21.0
    ca2_max = ca2_max or 16.0
    ex_max = ex_max or 10.0
    final_max = final_max or 50.0

    # Load Groups.csv
    id_to_group = {}
    if os.path.exists("Groups.csv"):
        with open("Groups.csv", "r", encoding="utf-8-sig") as f:
            for line in f.readlines()[1:]:
                parts = line.strip().split(";")
                if len(parts) >= 2 and parts[0].strip():
                    sid = parts[0].strip()
                    grp = parts[1].strip().replace("Group", "").strip()
                    id_to_group[sid] = grp

    # Load Grades Project.csv
    group_to_grade = {}
    proj_max = 10.0
    if os.path.exists("Grades Project.csv"):
        with open("Grades Project.csv", "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
            if lines:
                header = lines[0].strip().split(";")
                if len(header) >= 2 and "/" in header[1]:
                    try:
                        proj_max = float(header[1].split("/")[1])
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

    # Collect unique IDs
    all_ids = set()
    for d in (ca1, ca2, ex, final):
        all_ids.update(d.keys())
    all_ids.update(id_to_group.keys())
    sorted_ids = sorted(all_ids, key=lambda x: int(x) if x.isdigit() else x)

    # Prepare table headers
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

    table_data = [headers]

    for sid in sorted_ids:
        # Retrieve student names
        last_name, first_name = "", ""
        for dataset in (ca1, ca2, ex, final):
            if sid in dataset:
                last_name, first_name = dataset[sid][0], dataset[sid][1]
                break

        # Calculate section marks and %
        ca1_m = ca1[sid][2] if sid in ca1 else 0.0
        ca1_pct = (ca1_m / ca1_max * 100.0) if ca1_max > 0 else 0.0

        ca2_m = ca2[sid][2] if sid in ca2 else 0.0
        ca2_pct = (ca2_m / ca2_max * 100.0) if ca2_max > 0 else 0.0

        ex_m = ex[sid][2] if sid in ex else 0.0
        ex_pct = (ex_m / ex_max * 100.0) if ex_max > 0 else 0.0

        final_m = final[sid][2] if sid in final else 0.0
        final_pct = (final_m / final_max * 100.0) if final_max > 0 else 0.0

        grp = id_to_group.get(sid, "")
        proj_m = group_to_grade.get(grp, 0.0)
        proj_pct = (proj_m / proj_max * 100.0) if proj_max > 0 else 0.0

        # Total scores
        total_marks = ca1_m + ca2_m + ex_m + final_m + proj_m
        total_pct = (
            (ca1_pct * 0.15)
            + (ca2_pct * 0.15)
            + (ex_pct * 0.15)
            + (final_pct * 0.40)
            + (proj_pct * 0.15)
        )
        grade = get_sit_grade(total_pct)

        row = [
            last_name,
            first_name,
            sid,
            f"{ca1_m:.2f}",
            f"{ca1_pct:.2f}",
            f"{ca2_m:.2f}",
            f"{ca2_pct:.2f}",
            f"{ex_m:.2f}",
            f"{ex_pct:.2f}",
            f"{final_m:.2f}",
            f"{final_pct:.2f}",
            f"{proj_m:.2f}",
            f"{proj_pct:.2f}",
            f"{total_marks:.2f}",
            f"{total_pct:.2f}",
            grade,
        ]
        table_data.append(row)

    # 1. Write to CSV and ensure it is fully written and closed[cite: 2]
    csv_filename = "compiled_results.csv"
    with open(csv_filename, "w", encoding="utf-8") as out:
        for row in table_data:
            out.write(";".join(row) + "\n")

    print(
        f"[✓] CSV written to '{csv_filename}' ({len(table_data) - 1} students)."
    )

    # 2. Generate PDF directly from the in-memory data (avoids 0-byte file conflicts)
    generate_pdf(table_data, "compiled_results.pdf")


if __name__ == "__main__":
    main()