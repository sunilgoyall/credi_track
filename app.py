from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# DATABASE CONNECT
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# INIT DATABASE
def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        amount REAL,
        type TEXT,
        date TEXT,
        note TEXT
    )
    """)
    conn.commit()

init_db()

# DASHBOARD
@app.route("/")
def index():
    conn = get_db()

    credit = conn.execute("SELECT SUM(amount) FROM transactions WHERE type='credit'").fetchone()[0] or 0
    payment = conn.execute("SELECT SUM(amount) FROM transactions WHERE type='payment'").fetchone()[0] or 0
    balance = credit - payment

    return render_template("index.html", credit=credit, payment=payment, balance=balance)

# CUSTOMER PAGE
@app.route("/customers")
def customers():
    conn = get_db()

    data = conn.execute("""
    SELECT c.*, 
    IFNULL(SUM(CASE WHEN t.type='credit' THEN t.amount ELSE 0 END),0) -
    IFNULL(SUM(CASE WHEN t.type='payment' THEN t.amount ELSE 0 END),0)
    as balance
    FROM customers c
    LEFT JOIN transactions t ON c.id = t.customer_id
    GROUP BY c.id
    """).fetchall()

    return render_template("customers.html", customers=data)

# ADD CUSTOMER
@app.route("/add_customer", methods=["POST"])
def add_customer():
    name = request.form["name"]
    phone = request.form["phone"]

    conn = get_db()
    conn.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
    conn.commit()

    return redirect("/customers")

# ADD CREDIT
@app.route("/add_credit", methods=["POST"])
def add_credit():
    cid = request.form["customer_id"]
    amount = request.form["amount"]
    note = request.form["note"]

    conn = get_db()
    conn.execute(
        "INSERT INTO transactions (customer_id, amount, type, date, note) VALUES (?, ?, 'credit', datetime('now'), ?)",
        (cid, amount, note)
    )
    conn.commit()

    return redirect("/customers")

# ADD PAYMENT
@app.route("/add_payment", methods=["POST"])
def add_payment():
    cid = request.form["customer_id"]
    amount = request.form["amount"]

    conn = get_db()
    conn.execute(
        "INSERT INTO transactions (customer_id, amount, type, date) VALUES (?, ?, 'payment', datetime('now'))",
        (cid, amount)
    )
    conn.commit()

    return redirect("/customers")

# VIEW TRANSACTIONS
@app.route("/history/<int:customer_id>")
def transactions(customer_id):
    conn = get_db()

    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    query = "SELECT * FROM transactions WHERE customer_id=?"
    params = [customer_id]

    if from_date and to_date:
        query += " AND date BETWEEN ? AND ?"
        params.extend([from_date, to_date])

    query += " ORDER BY date DESC"

    data = conn.execute(query, params).fetchall()

    return render_template("transactions.html", transactions=data)

# RUN
if __name__ == "__main__":
    app.run(debug=True)