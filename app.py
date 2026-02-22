from flask import Flask, render_template, request, redirect
import sqlite3
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)

# ===============================
# DATABASE CONNECTION
# ===============================
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# ===============================
# CREATE TABLES
# ===============================
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL,
    category TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monthly_budget REAL
)
""")

conn.commit()


# ===============================
# HOME PAGE
# ===============================
@app.route("/")
def home():

    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    expenses = cursor.fetchall()

    # Total spent
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_result = cursor.fetchone()
    total = total_result[0] if total_result[0] else 0

    # Latest budget
    cursor.execute("SELECT monthly_budget FROM budget ORDER BY id DESC LIMIT 1")
    budget_result = cursor.fetchone()
    budget = budget_result[0] if budget_result else 0

    # Category chart data
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    category_data = cursor.fetchall()
    categories = [row[0] for row in category_data]
    amounts = [row[1] for row in category_data]

    # Trend chart data
    cursor.execute("SELECT date, amount FROM expenses ORDER BY date")
    trend_data = cursor.fetchall()
    dates = [row[0] for row in trend_data]
    trend_amounts = [row[1] for row in trend_data]

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        budget=budget,
        categories=categories,
        amounts=amounts,
        dates=dates,
        trend_amounts=trend_amounts
    )


# ===============================
# ADD EXPENSE
# ===============================
@app.route("/add", methods=["POST"])
def add_expense():
    amount = request.form["amount"]
    category = request.form["category"]

    cursor.execute(
        "INSERT INTO expenses (amount, category) VALUES (?, ?)",
        (amount, category)
    )
    conn.commit()

    return redirect("/")


# ===============================
# SET BUDGET
# ===============================
@app.route("/set_budget", methods=["POST"])
def set_budget():
    budget = request.form["budget"]

    cursor.execute(
        "INSERT INTO budget (monthly_budget) VALUES (?)",
        (budget,)
    )
    conn.commit()

    return redirect("/")


# ===============================
# AI PREDICTION
# ===============================
@app.route("/predict")
def predict():

    cursor.execute("SELECT amount FROM expenses")
    data = cursor.fetchall()

    if len(data) < 2:
        return redirect("/")

    X = np.array(range(len(data))).reshape(-1, 1)
    y = np.array([d[0] for d in data])

    model = LinearRegression()
    model.fit(X, y)

    next_value = model.predict([[len(data)]])[0]
    prediction = round(next_value, 2)

    # Re-fetch everything for page
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    expenses = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_result = cursor.fetchone()
    total = total_result[0] if total_result[0] else 0

    cursor.execute("SELECT monthly_budget FROM budget ORDER BY id DESC LIMIT 1")
    budget_result = cursor.fetchone()
    budget = budget_result[0] if budget_result else 0

    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    category_data = cursor.fetchall()
    categories = [row[0] for row in category_data]
    amounts = [row[1] for row in category_data]

    cursor.execute("SELECT date, amount FROM expenses ORDER BY date")
    trend_data = cursor.fetchall()
    dates = [row[0] for row in trend_data]
    trend_amounts = [row[1] for row in trend_data]

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        budget=budget,
        prediction=prediction,
        categories=categories,
        amounts=amounts,
        dates=dates,
        trend_amounts=trend_amounts
    )


# ===============================
# RUN APP
# ===============================
# ===============================
# DELETE EXPENSE
# ===============================
@app.route("/delete/<int:id>")
def delete(id):
    cursor.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    return redirect("/")


# ===============================
# EXPORT CSV  👇 ADD HERE
# ===============================
@app.route("/export")
def export():
    cursor.execute("SELECT * FROM expenses")
    data = cursor.fetchall()

    from flask import Response

    def generate():
        yield "ID,Amount,Category,Date\n"
        for row in data:
            yield f"{row[0]},{row[1]},{row[2]},{row[3]}\n"

    return Response(generate(),
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=expenses.csv"})


# ===============================
# RUN APP
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
