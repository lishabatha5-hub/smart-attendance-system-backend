from flask import Flask, render_template, request, redirect
import psycopg2

app = Flask(__name__)

DATABASE_URL = "postgresql://edutrack_db_wa2v_user:lIkXo2EtvaxJ68oqWgFPTwDEpS1R1By9@dpg-d9364dlaeets73b74mag-a.oregon-postgres.render.com/edutrack_db_wa2v"

def get_connection():
    return psycopg2.connect(DATABASE_URL)


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
    avg_aai = round(result, 2) if result else 0

    cursor.execute("SELECT COUNT(*) FROM aai WHERE status='At Risk'")
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

    cursor.execute("SELECT rollno, name, branch FROM students ORDER BY id")
    students_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("students.html", students=students_data)


@app.route("/add_student", methods=["POST"])
def add_student():
    rollno = request.form["rollno"]
    name = request.form["name"]
    branch = request.form["branch"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO students (rollno, name, branch) VALUES (%s, %s, %s)",
        (rollno, name, branch)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/students")


@app.route("/edit_student/<rollno>", methods=["GET", "POST"])
def edit_student(rollno):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        branch = request.form["branch"]

        cursor.execute(
            "UPDATE students SET name=%s, branch=%s WHERE rollno=%s",
            (name, branch, rollno)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/students")

    cursor.execute(
        "SELECT rollno, name, branch FROM students WHERE rollno=%s",
        (rollno,)
    )
    student = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("edit_student.html", student=student)


@app.route("/delete_student/<rollno>")
def delete_student(rollno):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE rollno=%s", (rollno,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/students")


@app.route("/attendance")
def attendance():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, rollno, total_classes, classes_attended, percentage FROM attendance ORDER BY id"
    )
    attendance_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("attendance.html", attendance_records=attendance_data)


@app.route("/save_attendance", methods=["POST"])
def save_attendance():
    rollno = request.form["rollno"]
    total_classes = int(request.form["total_classes"])
    classes_attended = int(request.form["classes_attended"])

    percentage = (classes_attended / total_classes) * 100

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO attendance (rollno, total_classes, classes_attended, percentage)
        VALUES (%s, %s, %s, %s)
        """,
        (rollno, total_classes, classes_attended, percentage)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/attendance")


@app.route("/delete_attendance/<int:id>")
def delete_attendance(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM attendance WHERE id=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/attendance")


@app.route("/marks")
def marks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, rollno, mid1, mid2, average, internal_percentage, status
        FROM marks
        ORDER BY id
        """
    )
    marks_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("marks.html", marks_records=marks_data)


@app.route("/save_marks", methods=["POST"])
def save_marks():
    rollno = request.form["rollno"]
    mid1 = int(request.form["mid1"])
    mid2 = int(request.form["mid2"])

    average = (mid1 + mid2) / 2
    internal_percentage = (average / 25) * 100

    if average >= 22:
        status = "Excellent"
    elif average >= 18:
        status = "Good"
    elif average >= 12:
        status = "Average"
    else:
        status = "At Risk"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO marks (rollno, mid1, mid2, average, internal_percentage, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (rollno, mid1, mid2, average, internal_percentage, status)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/marks")


@app.route("/delete_marks/<int:id>")
def delete_marks(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM marks WHERE id=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/marks")


@app.route("/aai")
def aai():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, rollno, attendance, internal, aai_score, status
        FROM aai
        ORDER BY id
        """
    )
    aai_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("aai.html", aai_records=aai_data)


@app.route("/save_aai", methods=["POST"])
def save_aai():
    rollno = request.form["rollno"]
    attendance = float(request.form["attendance"])
    internal = float(request.form["internal"])

    aai_score = (attendance * 0.65) + (internal * 0.35)

    if aai_score >= 85:
        status = "Excellent"
    elif aai_score >= 70:
        status = "Good"
    elif aai_score >= 50:
        status = "Average"
    else:
        status = "At Risk"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO aai (rollno, attendance, internal, aai_score, status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (rollno, attendance, internal, aai_score, status)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/aai")


@app.route("/delete_aai/<int:id>")
def delete_aai(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM aai WHERE id=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/aai")


def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        rollno TEXT,
        name TEXT,
        branch TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        rollno TEXT,
        total_classes INTEGER,
        classes_attended INTEGER,
        percentage REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        id SERIAL PRIMARY KEY,
        rollno TEXT,
        mid1 INTEGER,
        mid2 INTEGER,
        average REAL,
        internal_percentage REAL,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aai (
        id SERIAL PRIMARY KEY,
        rollno TEXT,
        attendance REAL,
        internal REAL,
        aai_score REAL,
        status TEXT
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()


create_database()

if __name__ == "__main__":
    app.run(debug=True)