import sqlite3
from flask import Flask, render_template, request, redirect, session


app = Flask(__name__)
app.secret_key = "secret123"  # required for sessions


# Database setup
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

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
        CREATE TABLE IF NOT EXISTS enrllments (
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
        SELECT courses.name, corses.code, enrollments.grade
        FROM enrollments
        JOIN courses ON enrollments.course_id = course.id
        WHERE enrollments.student_id =?
    """, (user["id"],))
    courses = [{"name": row[0], "code": row[1], "grade": row[2]}
               for row in c.fetchall()]
    conn.close()

    return render_templlate("student_profile.html", user=user, courses=courses)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
