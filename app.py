import sqlite3
from flask import Flask, render_template, request, redirect, session
import sqlite3
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.secret_key = "secret123"

@app.route("/")
def home():
    return render_template("index.html")
# ---------- DATABASE INIT ----------
def init_db():
    conn = sqlite3.connect("database.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()
    init_db()
# ---------- HOME PAGE ----------
@app.route("/dashboard")
def index():
    conn = sqlite3.connect("database.db")
    expenses = conn.execute("SELECT * FROM expenses").fetchall()
    conn.close()
    return render_template("index.html", expenses=expenses)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            conn.commit()
            conn.close()

        except sqlite3.IntegrityError:
            return "Username already exists"

        finally:
            conn.close()

        return redirect("/login")

    return render_template("register.html")
#--------- register ----------#

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")
# ---------- ADD EXPENSE ----------
@app.route("/add", methods=["POST"])
def add():
    amount = request.form["amount"]
    category = request.form["category"]
    date = request.form["date"]

    conn = sqlite3.connect("database.db")
    conn.execute("INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)",
                 (amount, category, date))
    conn.commit()
    conn.close()

    return redirect("/")


# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    conn.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("database.db")
    data = conn.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        GROUP BY category
    """).fetchall()
    conn.close()

    categories = [row[0] for row in data]
    totals = [row[1] for row in data]

    return render_template("dashboard.html",
                           categories=categories,
                           totals=totals)


# ---------- AI PREDICTION ----------
@app.route("/ai")
def ai_prediction():

    conn = sqlite3.connect("database.db")
    data = conn.execute("SELECT amount FROM expenses").fetchall()
    conn.close()

    if len(data) < 2:
        return render_template("ai.html",
                               prediction="Not enough data")

    months = np.array(range(len(data))).reshape(-1, 1)
    totals = np.array([row[0] for row in data])

    model = LinearRegression()
    model.fit(months, totals)

    next_month = np.array([[len(data)]])
    prediction = model.predict(next_month)[0]

    return render_template("ai.html",
                           prediction=int(prediction))

@app.route("/")
def start():
    return redirect("/login")
# ---------- MAIN ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)