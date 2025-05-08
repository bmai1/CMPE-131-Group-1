import os
import sqlite3
import bcrypt
from pathlib import Path   # <- add near the top, with other imports
from datetime import datetime
from flask import (
    Flask, render_template, g, request,
    redirect, url_for, session
)
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────
# Flask & database setup
# ────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["DATABASE"] = os.path.join(BASE_DIR, "database.db")


def get_db():
    """Return the per-request SQLite handle."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(schema_path: str = "schema.sql"):
    """Run once to create tables from *schema.sql*."""
    db = get_db()
    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


# ────────────────────────────
# Tiny helper → log a transaction
# ────────────────────────────
def log_tx(username: str, accountname: str, t_type: str, amount: float):
    """Insert one row in *transactions* and commit."""
    db = get_db()
    db.execute(
        """INSERT INTO transactions
           (username, accountname, t_type, amount, ts)
           VALUES (?, ?, ?, ?, ?)""",
        (username, accountname, t_type, amount, datetime.utcnow()),
    )
    db.commit()


# ────────────────────────────
# Routes
# ────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ----------  Auth ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    if request.method == "POST":
        username = request.form["userid"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            session["username"] = username
            return redirect(url_for("dashboard"))
        message = "Invalid username or password."

    return render_template("login.html", message=message)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/registration", methods=["GET", "POST"])
def registration():
    message = None
    if request.method == "POST":
        username = request.form["userid"]
        email = request.form["email"]
        address1 = request.form["address1"]
        address2 = request.form["address2"]
        city = request.form["city"]
        state = request.form["state"]
        zip_code = request.form["zip"]
        dob = request.form["dob"]
        phone = request.form["phone"]
        password = request.form["password"]

        db = get_db()
        if db.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone():
            message = "Username already taken."
        else:
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            db.execute(
                """INSERT INTO users
                   (username, email, address1, address2, city, state,
                    zip, dob, phone, password)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    username,
                    email,
                    address1,
                    address2,
                    city,
                    state,
                    zip_code,
                    dob,
                    phone,
                    hashed,
                ),
            )
            db.commit()
            return redirect(url_for("login"))

    return render_template("registration.html", message=message)


# ----------  Dashboard ----------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    db = get_db()
    accounts = db.execute(
        "SELECT accountname, balance FROM accounts WHERE username = ?",
        (username,),
    ).fetchall()

    if request.method == "POST":
        form_id = request.form.get("form_id")
        accountname = request.form.get("accountname")

        if form_id == "open_account":
            db.execute(
                """INSERT INTO accounts (username, accountname, balance)
                   VALUES (?, ?, 0)""",
                (username, accountname),
            )
            db.commit()

        elif form_id == "close_account":
            db.execute(
                "DELETE FROM accounts WHERE username = ? AND accountname = ?",
                (username, accountname),
            )
            db.commit()

        return redirect(url_for("dashboard"))

    return render_template(
        "dashboard.html", username=username, accounts=accounts
    )


# ----------  Account details + recent activity ----------
@app.route("/account_details")
def account_details():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    txns = db.execute(
        """SELECT accountname, t_type, amount, ts
           FROM transactions
           WHERE username = ?
           ORDER BY ts DESC
           LIMIT 25""",
        (username,),
    ).fetchall()

    return render_template("accountdetails.html", user=user, txns=txns)


# ----------  Edit profile ----------
@app.route("/edit_account", methods=["GET", "POST"])
def edit_account():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    if request.method == "POST":
        db.execute(
            """UPDATE users
               SET email = ?, address1 = ?, address2 = ?, city = ?,
                   state = ?, zip = ?
               WHERE username = ?""",
            (
                request.form.get("email"),
                request.form.get("address1"),
                request.form.get("address2"),
                request.form.get("city"),
                request.form.get("state"),
                request.form.get("zip"),
                username,
            ),
        )
        db.commit()
        return redirect(url_for("account_details"))

    return render_template("edit_account.html", user=user)


# ----------  Deposit ----------
@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    db = get_db()
    message = None

    accounts = db.execute(
        "SELECT accountname, balance FROM accounts WHERE username = ?",
        (username,),
    ).fetchall()

    if request.method == "POST":
        accountname = request.form.get("accountname")
        try:
            amt = float(request.form.get("depositamount", 0))
            if amt <= 0:
                message = "Deposit amount must be positive."
            else:
                bal = db.execute(
                    """SELECT balance FROM accounts
                       WHERE username = ? AND accountname = ?""",
                    (username, accountname),
                ).fetchone()
                if not bal:
                    message = "Account not found."
                else:
                    new_bal = bal["balance"] + amt
                    db.execute(
                        """UPDATE accounts
                           SET balance = ? WHERE username = ? AND accountname = ?""",
                        (new_bal, username, accountname),
                    )
                    db.commit()
                    log_tx(username, accountname, "deposit", amt)
                    message = f"Successfully deposited ${amt:.2f}."
                    accounts = db.execute(
                        "SELECT accountname, balance FROM accounts WHERE username = ?",
                        (username,),
                    ).fetchall()
        except ValueError:
            message = "Invalid amount."

    return render_template(
        "deposit.html", username=username, accounts=accounts, message=message
    )


# ----------  Withdraw ----------
@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    db = get_db()
    message = None

    accounts = db.execute(
        "SELECT accountname, balance FROM accounts WHERE username = ?",
        (username,),
    ).fetchall()

    if request.method == "POST":
        accountname = request.form.get("accountname")
        try:
            amt = float(request.form.get("amount", 0))
            if amt <= 0:
                message = "Withdrawal amount must be positive."
            else:
                bal = db.execute(
                    """SELECT balance FROM accounts
                       WHERE username = ? AND accountname = ?""",
                    (username, accountname),
                ).fetchone()
                if not bal:
                    message = "Account not found."
                elif bal["balance"] < amt:
                    message = "Insufficient balance."
                else:
                    new_bal = bal["balance"] - amt
                    db.execute(
                        """UPDATE accounts
                           SET balance = ? WHERE username = ? AND accountname = ?""",
                        (new_bal, username, accountname),
                    )
                    db.commit()
                    log_tx(username, accountname, "withdraw", amt)
                    message = f"Successfully withdrew ${amt:.2f}."
                    accounts = db.execute(
                        "SELECT accountname, balance FROM accounts WHERE username = ?",
                        (username,),
                    ).fetchall()
        except ValueError:
            message = "Invalid amount."

    return render_template(
        "withdraw.html", username=username, accounts=accounts, message=message
    )


# ----------  Transfer ----------
@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    db = get_db()
    message = None

    accounts = db.execute(
        "SELECT accountname, balance FROM accounts WHERE username = ?",
        (username,),
    ).fetchall()

    if request.method == "POST":
        from_acct = request.form.get("fromaccount")
        to_acct = request.form.get("toaccount")
        try:
            amt = float(request.form.get("amount", 0))
            if amt <= 0:
                message = "Transfer amount must be positive."
            elif from_acct == to_acct:
                message = "Cannot transfer to the same account."
            else:
                from_bal = db.execute(
                    """SELECT balance FROM accounts
                       WHERE username = ? AND accountname = ?""",
                    (username, from_acct),
                ).fetchone()
                to_bal = db.execute(
                    """SELECT balance FROM accounts
                       WHERE username = ? AND accountname = ?""",
                    (username, to_acct),
                ).fetchone()

                if not from_bal or not to_bal:
                    message = "Invalid account selection."
                elif from_bal["balance"] < amt:
                    message = "Insufficient balance."
                else:
                    db.execute(
                        """UPDATE accounts
                           SET balance = balance - ?
                           WHERE username = ? AND accountname = ?""",
                        (amt, username, from_acct),
                    )
                    db.execute(
                        """UPDATE accounts
                           SET balance = balance + ?
                           WHERE username = ? AND accountname = ?""",
                        (amt, username, to_acct),
                    )
                    db.commit()
                    log_tx(username, from_acct, "transfer-out", amt)
                    log_tx(username, to_acct, "transfer-in", amt)
                    message = f"Successfully transferred ${amt:.2f}."
                    accounts = db.execute(
                        "SELECT accountname, balance FROM accounts WHERE username = ?",
                        (username,),
                    ).fetchall()
        except ValueError:
            message = "Invalid amount."

    return render_template(
        "transfer.html", username=username, accounts=accounts, message=message
    )



if __name__ == "__main__":
    from pathlib import Path, PurePath
    db_path = Path(__file__).resolve().parent / "database.db"

    if not db_path.exists():          # only if DB file is missing
        from pathlib import Path
        with app.app_context():
            schema_file = Path(__file__).resolve().parent / "database" / "schema.sql"
            init_db(schema_file)

    app.run(debug=True)

