import os

import psycopg2
from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)

# Add DATABASE_URL in Render Environment Variables.
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Add it in Render Environment Variables."
        )

    return psycopg2.connect(DATABASE_URL)


def calculate_aai_status(aai_score):
    if aai_score >= 85:
        return "Excellent"
    if aai_score >= 70:
        return "Good"
    if aai_score >= 50:
        return "Average"
    return "At Risk"


def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            rollno VARCHAR(30) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            branch VARCHAR(100) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            rollno VARCHAR(30) NOT NULL,
            total_classes INTEGER NOT NULL,
            classes_attended INTEGER NOT NULL,
            percentage DOUBLE PRECISION NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id SERIAL PRIMARY KEY,
            rollno VARCHAR(30) NOT NULL,
            mid1 INTEGER NOT NULL,
            mid2 INTEGER NOT NULL,
            average DOUBLE PRECISION NOT NULL,
            internal_percentage DOUBLE PRECISION NOT NULL,
            status VARCHAR(30) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aai (
            id SERIAL PRIMARY KEY,
            rollno VARCHAR(30) NOT NULL,
            attendance DOUBLE PRECISION NOT NULL,
            internal DOUBLE PRECISION NOT NULL,
            aai_score DOUBLE PRECISION NOT NULL,
            status VARCHAR(30) NOT NULL
        )
    """)

    sample_students = [
        ("23L31A4401", "Ravi Kumar", "CSE"),
        ("23L31A4402", "Sita Devi", "CSE-DS"),
        ("23L31A4403", "Kiran Kumar", "AI & ML"),
        ("23L31A4404", "Anjali", "IT"),
        ("23L31A4405", "Rahul", "ECE"),
        ("23L31A4406", "Meena", "EEE"),
        ("23L31A4407", "Arjun", "Mechanical"),
        ("23L31A4408", "Divya", "Civil"),
        ("23L31A4409", "Naveen", "CSE"),
        ("23L31A4410", "Priya", "CSE-DS")
    ]

    sample_attendance = [
        ("23L31A4401", 100, 95, 95.0),
        ("23L31A4402", 100, 88, 88.0),
        ("23L31A4403", 100, 82, 82.0),
        ("23L31A4404", 100, 78, 78.0),
        ("23L31A4405", 100, 72, 72.0),
        ("23L31A4406", 100, 68, 68.0),
        ("23L31A4407", 100, 60, 60.0),
        ("23L31A4408", 100, 55, 55.0),
        ("23L31A4409", 100, 48, 48.0),
        ("23L31A4410", 100, 42, 42.0)
    ]

    sample_marks = [
        ("23L31A4401", 24, 23, 23.5, 94.0, "Good"),
        ("23L31A4402", 22, 21, 21.5, 86.0, "Good"),
        ("23L31A4403", 20, 19, 19.5, 78.0, "Good"),
        ("23L31A4404", 18, 18, 18.0, 72.0, "Good"),
        ("23L31A4405", 17, 16, 16.5, 66.0, "Good"),
        ("23L31A4406", 15, 14, 14.5, 58.0, "At Risk"),
        ("23L31A4407", 13, 12, 12.5, 50.0, "At Risk"),
        ("23L31A4408", 11, 10, 10.5, 42.0, "At Risk"),
        ("23L31A4409", 9, 8, 8.5, 34.0, "At Risk"),
        ("23L31A4410", 7, 6, 6.5, 26.0, "At Risk")
    ]

    sample_aai = [
        ("23L31A4401", 95.0, 94.0, 94.65, "Excellent"),
        ("23L31A4402", 88.0, 86.0, 87.30, "Excellent"),
        ("23L31A4403", 82.0, 78.0, 80.60, "Good"),
        ("23L31A4404", 78.0, 72.0, 75.90, "Good"),
        ("23L31A4405", 72.0, 66.0, 69.90, "Average"),
        ("23L31A4406", 68.0, 58.0, 64.50, "Average"),
        ("23L31A4407", 60.0, 50.0, 56.50, "Average"),
        ("23L31A4408", 55.0, 42.0, 50.45, "Average"),
        ("23L31A4409", 48.0, 34.0, 43.10, "At Risk"),
        ("23L31A4410", 42.0, 26.0, 36.40, "At Risk")
    ]

    cursor.executemany("""
        INSERT INTO students (rollno, name, branch)
        VALUES (%s, %s, %s)
        ON CONFLICT (rollno) DO NOTHING
    """, sample_students)

    cursor.execute("SELECT COUNT(*) FROM attendance")

    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO attendance (
                rollno,
                total_classes,
                classes_attended,
                percentage
            )
            VALUES (%s, %s, %s, %s)
        """, sample_attendance)

    cursor.execute("SELECT COUNT(*) FROM marks")

    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO marks (
                rollno,
                mid1,
                mid2,
                average,
                internal_percentage,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, sample_marks)

    cursor.execute("SELECT COUNT(*) FROM aai")

    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO aai (
                rollno,
                attendance,
                internal,
                aai_score,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
        """, sample_aai)

    conn.commit()
    cursor.close()
    conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT rollno) FROM attendance")
    present_today = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(aai_score) FROM aai")
    result = cursor.fetchone()[0]
    avg_aai = round(float(result), 2) if result is not None else 0

    cursor.execute("SELECT COUNT(*) FROM aai WHERE status = %s", ("At Risk",))
    at_risk = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        present_today=present_today,
        avg_aai=avg_aai,
        at_risk=at_risk
    )


@app.route("/students")
def students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT rollno, name, branch
        FROM students
        ORDER BY rollno
    """)

    students_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("students.html", students=students_data)


@app.route("/add_student", methods=["POST"])
def add_student():
    rollno = request.form["rollno"].strip()
    name = request.form["name"].strip()
    branch = request.form["branch"].strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO students (rollno, name, branch)
        VALUES (%s, %s, %s)
        ON CONFLICT (rollno) DO NOTHING
    """, (rollno, name, branch))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/students")


@app.route("/edit_student/<rollno>", methods=["GET", "POST"])
def edit_student(rollno):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"].strip()
        branch = request.form["branch"].strip()

        cursor.execute("""
            UPDATE students
            SET name = %s, branch = %s
            WHERE rollno = %s
        """, (name, branch, rollno))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/students")

    cursor.execute("""
        SELECT rollno, name, branch
        FROM students
        WHERE rollno = %s
    """, (rollno,))

    student = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("edit_student.html", student=student)


@app.route("/delete_student/<rollno>")
def delete_student(rollno):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE rollno = %s", (rollno,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/students")


@app.route("/attendance")
def attendance():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT rollno, total_classes, classes_attended, percentage
        FROM attendance
        ORDER BY id DESC
    """)

    attendance_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "attendance.html",
        attendance_records=attendance_data
    )


@app.route("/save_attendance", methods=["POST"])
def save_attendance():
    rollno = request.form["rollno"].strip()
    total_classes = int(request.form["total_classes"])
    classes_attended = int(request.form["classes_attended"])

    if total_classes <= 0:
        return "Total classes must be greater than zero", 400

    if classes_attended < 0 or classes_attended > total_classes:
        return "Classes attended must be between 0 and total classes", 400

    percentage = (classes_attended / total_classes) * 100

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO attendance (
            rollno,
            total_classes,
            classes_attended,
            percentage
        )
        VALUES (%s, %s, %s, %s)
    """, (
        rollno,
        total_classes,
        classes_attended,
        percentage
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/attendance")


@app.route("/marks")
def marks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            rollno,
            mid1,
            mid2,
            average,
            internal_percentage,
            status
        FROM marks
        ORDER BY id DESC
    """)

    marks_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "marks.html",
        marks_records=marks_data
    )


@app.route("/save_marks", methods=["POST"])
def save_marks():
    rollno = request.form["rollno"].strip()
    mid1 = int(request.form["mid1"])
    mid2 = int(request.form["mid2"])

    if not 0 <= mid1 <= 25 or not 0 <= mid2 <= 25:
        return "Mid marks must be between 0 and 25", 400

    average = (mid1 + mid2) / 2
    internal_percentage = (average / 25) * 100

    status = "Good" if internal_percentage >= 60 else "At Risk"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO marks (
            rollno,
            mid1,
            mid2,
            average,
            internal_percentage,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        rollno,
        mid1,
        mid2,
        average,
        internal_percentage,
        status
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/marks")


@app.route("/aai")
def aai():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            rollno,
            attendance,
            internal,
            aai_score,
            status
        FROM aai
        ORDER BY id DESC
    """)

    aai_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("aai.html", aai_records=aai_data)


@app.route("/save_aai", methods=["POST"])
def save_aai():
    rollno = request.form["rollno"].strip()
    attendance_value = float(request.form["attendance"])
    internal_value = float(request.form["internal"])

    aai_score = (
        attendance_value * 0.65
        + internal_value * 0.35
    )

    status = calculate_aai_status(aai_score)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO aai (
            rollno,
            attendance,
            internal,
            aai_score,
            status
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        rollno,
        attendance_value,
        internal_value,
        aai_score,
        status
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/aai")


@app.route("/delete_aai/<int:record_id>")
def delete_aai(record_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM aai WHERE id = %s",
        (record_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/aai")


@app.route("/get_student_data/<rollno>")
def get_student_data(rollno):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, branch
        FROM students
        WHERE rollno = %s
    """, (rollno,))

    student = cursor.fetchone()

    if student is None:
        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Student not found"
        })

    cursor.execute("""
        SELECT percentage
        FROM attendance
        WHERE rollno = %s
        ORDER BY id DESC
        LIMIT 1
    """, (rollno,))

    attendance_record = cursor.fetchone()

    cursor.execute("""
        SELECT
            mid1,
            mid2,
            average,
            internal_percentage,
            status
        FROM marks
        WHERE rollno = %s
        ORDER BY id DESC
        LIMIT 1
    """, (rollno,))

    marks_record = cursor.fetchone()

    cursor.execute("""
        SELECT aai_score, status
        FROM aai
        WHERE rollno = %s
        ORDER BY id DESC
        LIMIT 1
    """, (rollno,))

    aai_record = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "rollno": rollno,
        "name": student[0],
        "branch": student[1],
        "attendance": (
            round(float(attendance_record[0]), 2)
            if attendance_record else 0
        ),
        "mid1": marks_record[0] if marks_record else 0,
        "mid2": marks_record[1] if marks_record else 0,
        "average": (
            round(float(marks_record[2]), 2)
            if marks_record else 0
        ),
        "internal_percentage": (
            round(float(marks_record[3]), 2)
            if marks_record else 0
        ),
        "marks_status": marks_record[4] if marks_record else "No Data",
        "aai_score": (
            round(float(aai_record[0]), 2)
            if aai_record else 0
        ),
        "aai_status": aai_record[1] if aai_record else "No Data"
    })


create_database()


if __name__ == "__main__":
    app.run(debug=True)