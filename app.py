import sqlite3
from flask import Flask, render_template, request, redirect, session


app = Flask(__name__)
app.secret_key = "secret123"  # required for sessions


# Database setup
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
              ("Admin", "admin@example.com", "admin123", "admin"))

    # Users Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL   -- 'student' or 'admin'
        )
    """)

    # Course Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              code TEXT NOT NULL,
              name TEXT NOT NULL
              )
    """)

    # Enrollment Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_id INTEGER NOT NULL,
              course_id INTEGER NOT NULL,
              grade TEXT,
              FOREIGN KEY(student_id) REFERENCES users(id),
              FOREIGN KEY(course_id) REFERENCES courses(id)
              )
    """)

    conn.commit()
    conn.close()

# Routes


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (name, email, password, role) VALUES(?, ?, ?, ?)",
                  (name, email, password, "student"))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ? AND password = ?",
              (email, password))
    user = c.fetchone()
    conn.close()

    if user:
        session["user"] = user
        if user[4] == "admin":
            return redirect("/admin/dashboard")
        return redirect("/dashboard")

    return "Invalid login!"


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    user = {
        "id": session["user"][0],
        "name": session["user"][1],
        "email": session["user"][2],
        "password": session["user"][3],
        "role": session["user"][4]
    }

    return render_template("dashboard.html", user=user)


@app.route("/admin/dashboard")
def admin_dashboard():
    if "user" not in session or session["user"][4] != "admin":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, name, email FROM users WHERE role='student'")
    students = [{"id": row[0], "name": row[1], "email": row[2]}
                for row in c.fetchall()]
    conn.close()

    return render_template("admin_dashboard.html", students=students)


@app.route("/admin/add_course", methods=["GET", "POST"])
def add_course():
    if "user" not in session or session["user"][4] != "admin":
        return redirect("/")

    if request.method == "POST":
        code = request.form["code"]
        name = request.form["name"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO courses (code, name) VALUES (?, ?)", (code, name))
        conn.commit()
        conn.close()

        return redirect("/admin/dashboard")
    return render_template("add_course.html")


@app.route("/admin/enroll_student", methods=["GET", "POST"])
def enroll_student():
    if "user" not in session or session["user"][4] != "admin":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id, name, email FROM users WHERE role='student'")
    students = [{"id": row[0], "name": row[1], "email": row[2]}
                for row in c.fetchall()]

    c.execute("SELECT id, code, name FROM courses")
    courses = [{"id": row[0], "code": row[1], "name": row[2]}
               for row in c.fetchall()]

    if request.method == "POST":
        student_id = request.form["student_id"]
        course_id = request.form["course_id"]

        # Prevent dublicate enrollments
        c.execute("SELECT * FROM enrollments WHERE student_id=? AND course_id=?",
                  (student_id, course_id))
        if not c.fetchone():
            c.execute(
                "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)", (student_id, course_id))
            conn.commit()

        conn.close()
        return redirect("/admin/dashboard")

    conn.close()
    return render_template("enroll_student.html", students=students, courses=courses)


@app.route("/admin/assign_grade", methods=["GET", "POST"])
def assign_grade():
    if "user" not in session or session["user"][4] != "admin":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT enrollments.id, users.name, courses.name, courses.code, enrollments.grade
        FROM enrollments
        JOIN users ON enrollments.student_id = users.id
        JOIN courses ON enrollments.course_id = courses.id
    """)
    enrollments = [{"id": row[0], "student_name": row[1], "course_name": row[2],
                    "course_code": row[3], "grade": row[4]} for row in c.fetchall()]

    if request.method == "POST":
        enrollment_id = request.form["enrollment_id"]
        grade = request.form["grade"]

        c.execute("UPDATE enrollments SET grade=? WHERE id=?",
                  (grade, enrollment_id))
        conn.commit()
        conn.close()
        return redirect("/admin/dashboard")

    conn.close()
    return render_template("assign_grade.html", enrollments=enrollments)


@app.route("/admin/grades")
def admin_grades():
    if "user" not in session or session["user"][4] != "admin":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT users.name, users.email, courses.name, courses.code, enrollments.grade
        FROM enrollments
        JOIN users ON enrollments.student_id = users.id
        JOIN courses ON enrollments.course_id = courses.id
    """)

    gradebook = [{
        "student_name": row[0],
        "student_email": row[1],
        "course_name": row[2],
        "course_code": row[3],
        "grade": row[4]
    } for row in c.fetchall()]

    conn.close()

    return render_template("grades.html", gradebook=gradebook)


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/")

    user = {
        "id": session["user"][0],
        "name": session["user"][1],
        "email": session["user"][2],
        "role": session["user"][4]
    }

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        SELECT courses.name, courses.code, enrollments.grade
        FROM enrollments
        JOIN courses ON enrollments.course_id = courses.id
        WHERE enrollments.student_id =?
    """, (user["id"],))
    courses = [{"name": row[0], "code": row[1], "grade": row[2]}
               for row in c.fetchall()]
    conn.close()

    return render_template("student_profile.html", user=user, courses=courses)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
