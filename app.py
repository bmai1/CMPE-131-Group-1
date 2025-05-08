import sqlite3
import bcrypt
import os
from flask import Flask, render_template, g, request, redirect, url_for, session
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.config['DATABASE'] = 'database/database.db'


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('database/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def log_action(description):
    """
    Logs an action into the history table with the current timestamp.
    """
    db = get_db()
    db.execute("INSERT INTO history (datetime, description) VALUES (datetime('now'), ?)", (description,))
    db.commit()

@app.route('/')
def index():
    """
        Route for welcome page.
        Clicking "Get Started" redirects to registration page.
    """
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
        Route for login page.
        Checks for matching userid and password in database.
        Parameterized SQL query with the ? placeholder helps prevent SQL injection.
    """
    message = None
    if request.method == 'POST':
        username = request.form['userid']
        password = request.form['password']
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if username == "admin" and password == "admin":
            session['username'] = username  
            return redirect(url_for('admin')) 
        elif user and bcrypt.checkpw(password.encode('utf-8'), user['password']): 
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            message = "Invalid username or password."

    return render_template('login.html', message=message)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    """
        Route for registration page.
        Checks if username is already taken.
        Hashes password with bcrypt.
    """
    message = None
    if request.method == 'POST':
        username = request.form['userid']
        email = request.form['email']
        address1 = request.form['address1']
        address2 = request.form['address2']
        city = request.form['city']
        state = request.form['state']
        zip = request.form['zip']
        dob = request.form['dob']
        phone = request.form['phone']
        password = request.form['password']
        
        db = get_db()
        
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if existing_user:
            message = "Username already taken!"
        else:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            db.execute("INSERT INTO users (username, email, address1, address2, city, state, zip, dob, phone, password) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (username, email, address1, address2, city, state, zip, dob, phone, hashed_password))
            db.commit()
            message = "Registration successful! You can now log in."
            return redirect(url_for('login'))

    return render_template('registration.html', message=message)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """
       Route for dashboard.
       Open/close and view user accounts.
    """
    if 'username' in session:  
        
        username = session['username']
        db = get_db()
        accounts = db.execute("SELECT accountname, balance FROM accounts WHERE username = ?", (username,)).fetchall()

        if request.method == 'POST':
            form_id = request.form.get('form_id')
            accountname = request.form['accountname']

            if form_id == 'open_account':
                db.execute("INSERT INTO accounts (username, accountname, balance) VALUES (?, ?, ?)", (username, accountname, 0))
                db.commit()
                log_action(f"Opened account '{accountname}' for user '{username}'.")

            elif form_id == 'close_account':
                db.execute("DELETE FROM accounts WHERE username = ? AND accountname = ?", (username, accountname))
                db.commit()
                log_action(f"Closed account '{accountname}' for user '{username}'.")
    
            return redirect(url_for('dashboard'))
        
        return render_template('dashboard.html', username=username, accounts=accounts)  
    else:
        return redirect(url_for('login'))  
    
@app.route('/account_details')
def account_details():
    """
    Route for viewing account details.
    """
    if 'username' in session:
        username = session['username']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        history = db.execute(
                "SELECT datetime, description FROM history ORDER BY datetime DESC LIMIT 8"
        ).fetchall()
        if user:
            return render_template('accountdetails.html', user=user, history=history)
    
    return redirect(url_for('login'))  # Redirect to login if not authenticated

@app.route('/edit_account', methods=['GET', 'POST'])
def edit_account():
    """
    Route for editing account details.
    """
    if 'username' in session:
        username = session['username']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if request.method == 'POST':
            new_email = request.form.get('email')
            new_address1 = request.form.get('address1')
            new_address2 = request.form.get('address2')
            new_city = request.form.get('city')
            new_state = request.form.get('state')
            new_zip = request.form.get('zip')
            new_phone = request.form.get('phone')

            db.execute("""
                UPDATE users SET email = ?, address1 = ?, address2 = ?, city = ?, state = ?, zip = ?, phone = ?
                WHERE username = ?
            """, (new_email, new_address1, new_address2, new_city, new_state, new_zip, new_phone, username))
            db.commit()

            return redirect(url_for('account_details'))

        return render_template('editaccount.html', user=user)

    return redirect(url_for('login'))

    
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    """
        Route for deposit.
    """
    if 'username' in session:
        username = session['username']
        db = get_db()
        message = ""

        if request.method == 'POST':
            accountname = request.form.get('accountname')
            depositamount_str = request.form.get('depositamount')

            if not accountname or not depositamount_str:
                message = "Please provide all required fields."
            else:
                try:
                    depositamount = float(depositamount_str)
                    if depositamount <= 0:
                        message = "Deposit amount must be greater than zero."
                    else:
                        # Check if the account exists
                        account = db.execute(
                            "SELECT balance FROM accounts WHERE username = ? AND accountname = ?",
                            (username, accountname)
                        ).fetchone()

                        if not account:
                            message = f"Account '{accountname}' does not exist for user '{username}'."
                        else:
                            # Perform the deposit
                            new_balance = account['balance'] + depositamount
                            db.execute(
                                "UPDATE accounts SET balance = ? WHERE username = ? AND accountname = ?",
                                (new_balance, username, accountname)
                            )
                            db.commit()
                            log_action(f"Deposited ${depositamount:.2f} into account '{accountname}' for user '{username}'.")
                            message = f"Successfully deposited ${depositamount:.2f} into account '{accountname}'."
                except ValueError:
                    message = "Invalid deposit amount. Please enter a valid number."

        return render_template('deposit.html', username=username, message=message)


@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'username' in session:
        username = session['username']
        db = get_db()

        if request.method == 'POST':
            fromaccount = request.form.get('fromaccount')
            toaccount = request.form.get('toaccount')
            amount = float(request.form.get('amount'))

            if fromaccount != toaccount and amount > 0:
                from_balance = db.execute(
                    "SELECT balance FROM accounts WHERE username = ? AND accountname = ?", 
                    (username, fromaccount)
                ).fetchone()

                to_balance = db.execute(
                    "SELECT balance FROM accounts WHERE username = ? AND accountname = ?", 
                    (username, toaccount)
                ).fetchone()

                if from_balance['balance'] >= amount:
                    db.execute(
                        "UPDATE accounts SET balance = balance - ? WHERE username = ? AND accountname = ?", 
                        (amount, username, fromaccount)
                    )

                    db.execute(
                        "UPDATE accounts SET balance = balance + ? WHERE username = ? AND accountname = ?", 
                        (amount, username, toaccount)
                    )
                    db.commit()
                    log_action(f"Transferred ${amount:.2f} from account '{fromaccount}' to '{toaccount}' for user '{username}'.")

    return render_template('transfer.html')

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    db = get_db()

    # Fetch accounts associated with the user
    accounts = db.execute("SELECT accountname, balance FROM accounts WHERE username = ?", (username,)).fetchall()
    message = None

    if request.method == 'POST':
        accountname = request.form.get("account_id")  # Match the form field name
        password = request.form.get("password")
        amount_str = request.form.get("amount")

        if not accountname or not password or not amount_str:
            message = "Please provide all required fields."
        else:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    message = "Invalid withdrawal amount."
                else:
                    # Fetch user's hashed password from users table
                    user = db.execute("SELECT password FROM users WHERE username = ?", (username,)).fetchone()

                    if not user:
                        message = "User not found."
                    elif not bcrypt.checkpw(password.encode('utf-8'), user['password']):
                        message = "Incorrect password. Withdrawal denied."
                    else:
                        # Fetch the account balance
                        account = db.execute("SELECT balance FROM accounts WHERE username = ? AND accountname = ?", 
                                             (username, accountname)).fetchone()

                        if not account:
                            message = "Invalid account selection."
                        elif account['balance'] < amount:
                            message = "Insufficient balance."
                        else:
                            # Process withdrawal
                            db.execute("UPDATE accounts SET balance = balance - ? WHERE username = ? AND accountname = ?", 
                                       (amount, username, accountname))
                            db.commit()
                            log_action(f"Withdrew ${amount:.2f} from account '{accountname}' for user '{username}'.")

                            message = f"Successfully withdrew ${amount:.2f} from {accountname}."
                            accounts = db.execute("SELECT accountname, balance FROM accounts WHERE username = ?", (username,)).fetchall()

            except ValueError:
                message = "Invalid amount. Please enter a valid number."

    return render_template('withdraw.html', username=username, message=message, accounts=accounts)

@app.route('/admin')
def admin():
    """Route for admin dashboard."""    
    return render_template('admin.html')
