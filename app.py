import sqlite3
import bcrypt
import os
from flask import Flask, render_template, g, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.config['DATABASE'] = 'database/users.db'

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

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']): 
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

@app.route('/dashboard')
def dashboard():
    """
       Route for dashboard.
       Open/close and view user accounts.
    """
    if 'username' in session:  
        username = session['username']  
        return render_template('dashboard.html', username=username)  
    else:
        return redirect(url_for('login'))  
@app.route('/accountdetails')
def account_details():
    """
    Route for viewing account details.
    """
    if 'username' in session:
        username = session['username']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user:
            return render_template('accountdetails.html', user=user)
    
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
