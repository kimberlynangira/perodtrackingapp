
from flask import Flask, request, jsonify, send_from_directory, g, session, redirect
from flask_cors import CORS
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re  # For email validation
from flask_session import Session  # Import Flask-Session

DATABASE = 'users.db'

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend'))  # Set static folder to 'frontend'
CORS(app)

# Configure session management
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"  # You can choose other types
Session(app)

# ... (the rest of your code)

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_db():
    """Connects to the database and returns a database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Return rows as dictionaries
        setattr(g, '_database', db)
    return db

def init_db():
    """Initializes the database by creating tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def is_valid_email(email):
    """Validates email format."""
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))

def is_valid_password(password):
    """Validates password complexity."""
    # You can adjust these criteria
    return len(password) >= 8 and any(c.isdigit() for c in password) and any(c.isalpha() for c in password)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email format"}), 400

    if not is_valid_password(password):
        return jsonify({"success": False, "message": "Password must be at least 8 characters and contain letters and numbers"}), 400

    hashed_password = generate_password_hash(password)

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        db.commit()
        return jsonify({"success": True, "message": "Registration successful"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already exists"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        session["user_id"] = user['id']
        # Redirect to the home page
        return redirect('/home')  # Changed this line
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    """Logs the user out by clearing the session."""
    session.pop("user_id", None)
    return jsonify({"success": True, "message": "Logout successful"})

def login_required(view):
    """Decorator to protect routes that require login."""
    from functools import wraps

    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Login required"}), 401
        return view(**kwargs)

    return wrapped_view

@app.route('/cycles', methods=['POST', 'GET'])
@login_required
def cycles():
    """Handles cycle data: storing and retrieving."""
    db = get_db()
    cursor = db.cursor()
    user_id = session["user_id"]

    if request.method == 'POST':
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not start_date:
            return jsonify({"success": False, "message": "Start date is required"}), 400

        try:
            datetime.strptime(start_date, '%Y-%m-%d')  # Validate date format
            if end_date:
                datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"success": False, "message": "Invalid date format (YYYY-MM-DD)"}), 400

        cursor.execute(
            "INSERT INTO cycles (user_id, start_date, end_date) VALUES (?, ?, ?)",
            (user_id, start_date, end_date)
        )
        db.commit()
        return jsonify({"success": True, "message": "Cycle added successfully"})

    elif request.method == 'GET':
        cursor.execute("SELECT * FROM cycles WHERE user_id = ?", (user_id,))
        cycles = cursor.fetchall()
        return jsonify({"success": True, "cycles": [dict(row) for row in cycles]})

@app.route('/symptoms', methods=['POST', 'GET'])
@login_required
def symptoms():
    """Handles symptom data: storing and retrieving."""
    db = get_db()
    cursor = db.cursor()
    user_id = session["user_id"]

    if request.method == 'POST':
        data = request.get_json()
        cycle_id = data.get('cycle_id')
        symptom_name = data.get('symptom_name')
        severity = data.get('severity')

        if not cycle_id or not symptom_name or severity is None:
            return jsonify({"success": False, "message": "Cycle ID, symptom name, and severity are required"}), 400

        cursor.execute(
            "INSERT INTO symptoms (cycle_id, symptom_name, severity)VALUES(?,?,?)",
            (cycle_id, symptom_name, severity)
        )
        db.commit()
        return jsonify({"success": True, "message": "Symptom added successfully"})

    elif request.method == 'GET':
        cursor.execute("SELECT * FROM symptoms WHERE cycle_id IN (SELECT id FROM cycles WHERE user_id = ?)", (user_id,))
        symptoms = cursor.fetchall()
        return jsonify({"success": True, "symptoms": [dict(row) for row in symptoms]})

import os
pages_path = "C:\\Users\\USER\\perodtrackingapp\\frontend\\pages"  # Replace with YOUR absolute path

@app.route('/')
def serve_index():
    return send_from_directory('pages', 'login.html')

@app.route('/home')
@login_required
def serve_home():
    return send_from_directory('pages', 'home.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)