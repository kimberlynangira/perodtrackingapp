import os
import logging
import re
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, g, session, redirect, render_template
from flask import send_from_directory
from flask_cors import CORS
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Database Configuration
DATABASE = 'users.db'
# Frontend Directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
# Template Directory
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, 'templates')
# Static Directory
STATIC_DIR = os.path.join(FRONTEND_DIR, 'static')
# Assets Directory
ASSETS_DIR = os.path.join(STATIC_DIR, 'assets')

# Flask Application Setup
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR, static_url_path='/static')
# Logging Configuration
logging.basicConfig(level=logging.DEBUG)
# CORS Configuration
CORS(app, resources={r"/predict_cycle": {"origins": "*"}})
# Session Configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Load the Model
model = None
try:
    # model = load_model('model/cycle_length_rf_model.joblib')  # commented out to avoid errors if model file is missing
    logging.info("Model loading is currently disabled.")
except Exception as e:
    logging.error(f"Error loading model: {e}")

# Database Connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        try:
            db = sqlite3.connect(DATABASE)
            db.row_factory = sqlite3.Row
            setattr(g, '_database', db)
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            raise  # Re-raise the exception to be handled in the route
    return db

# Initialize the Database
def init_db():
    with app.app_context():
        db = get_db()
        try:
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()
            logging.info("Initialized database schema.")
        except sqlite3.Error as e:
            logging.error(f"Error initializing database: {e}")
            db.rollback()
            raise  # Raise the error to stop app initialization
        finally:
            db.close()

# Validation Functions
def is_valid_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))

def is_valid_password(password):
    return len(password) >= 8 and any(c.isdigit() for c in password) and any(c.isalpha() for c in password)

# Login Required Decorator
def login_required(view):
    @wraps(view)  # Use wraps to preserve function metadata
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect('/')  # Redirect to login if not logged in
        return view(**kwargs)
    return wrapped_view

# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400

    if not is_valid_email(email):
        return jsonify({'success': False, 'error': 'Invalid email format'}), 400
    if len(password) < 8 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password):
        return jsonify({'success': False, 'error': 'Password must be at least 8 characters long and contain letters and numbers'}), 400

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone() is not None:
            return jsonify({'success': False, 'error': 'Email already exists'}), 400

        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        db.commit()
        return jsonify({"success": True, "message": "Registration successful"}), 201
    except sqlite3.Error as e:
        db.rollback()
        print(f"Database Error during registration: {e}") # ADD THIS LINE
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    finally:
        cur.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT id, password FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        if user is None:
            logging.warning(f"Login attempt with non-existent email: {email}")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

        if not check_password_hash(user['password'], password):
            logging.warning(f"Login attempt with incorrect password for email: {email}")
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

        session["user_id"] = user['id']
        logging.info(f"User logged in: {email}")
        return jsonify({"success": True, "message": "Login successful"}), 200  # Changed to JSON
    except sqlite3.Error as e:
        logging.error(f"Database error during login: {e}")
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    finally:
        cur.close()

@app.route('/logout', methods=['POST'])
def logout():
    if "user_id" in session:
        logging.info(f"User logged out. Session ID: {session.sid}")
        session.pop("user_id", None)
    return jsonify({"success": True, "message": "Logout successful"}), 200  # Changed to JSON

@app.route('/cycles', methods=['POST', 'GET'])
@login_required
def cycles():
    db = get_db()
    cur = db.cursor()
    try:
        if request.method == 'GET':
            cur.execute("SELECT * FROM cycles WHERE user_id = ?", (session["user_id"],))
            cycles = cur.fetchall()
            return jsonify({'success': True, 'cycles': [dict(row) for row in cycles]}), 200
        elif request.method == 'POST':
            data = request.get_json()
            cycle_start_date = data.get('cycle_start_date')

            if not cycle_start_date:
                return jsonify({'success': False, 'error': 'Cycle start date is required'}), 400

            try:
                datetime.strptime(cycle_start_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid date format. Use %Y-%m-%d'
                }), 400

            cur.execute(
                "INSERT INTO cycles (user_id, cycle_start_date) VALUES (?, ?)",
                (session["user_id"], cycle_start_date))
            db.commit()
            logging.info(f"Cycle added for user {session['user_id']}: {cycle_start_date}")
            return jsonify({"success": True, "message": "Cycle data added successfully"}), 201
    except sqlite3.Error as e:
        db.rollback()
        logging.error(f"Database error in cycles: {e}")
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    finally:
        cur.close()

@app.route('/symptoms', methods=['POST', 'GET'])
@login_required
def symptoms():
    db = get_db()
    cur = db.cursor()
    try:
        if request.method == 'GET':
            cur.execute("SELECT * FROM symptoms WHERE user_id = ?", (session["user_id"],))
            symptoms = cur.fetchall()
            return jsonify({'success': True, 'symptoms': [dict(row) for row in symptoms]}), 200
        elif request.method == 'POST':
            data = request.get_json()
            symptom_name = data.get('symptom_name')
            severity = data.get('severity')
            date = data.get('date')

            if not symptom_name or not severity or not date:
                return jsonify({
                    'success': False,
                    'error': 'Symptom name, severity and date are required'
                }), 400
            if not isinstance(severity, int) or not 1 <= severity <= 5:
                return jsonify({
                    'success': False,
                    'error': 'Severity must be an integer between 1 and 5'
                }), 400
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid date format. Use %Y-%m-%d'
                }), 400

            cur.execute(
                "INSERT INTO symptoms (user_id, symptom_name, severity, date) VALUES (?, ?, ?, ?)",
                (session["user_id"], symptom_name, severity, date)
            )
            db.commit()
            logging.info(f"Symptom added for user {session['user_id']}: {symptom_name}, {severity}, {date}")
            return jsonify({"success": True, "message": "Symptom data added successfully"}), 201
    except sqlite3.Error as e:
        db.rollback()
        logging.error(f"Database error in symptoms: {e}")
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    finally:
        cur.close()

@app.route('/predict_cycle', methods=['POST'])
def predict_cycle():
    data = request.get_json()
    logging.debug("Received request at /predict_cycle")
    logging.debug(f"Received data: {data}")
    required_features = [
        'user_id_encoded', 'cycle_start_month', 'period_duration',
        'days_until_ovulation',
        'flow_Heavy', 'flow_Light', 'flow_Medium', 'symptom_acne',
        'symptom_mood swings',
        'symptom_fatigue', 'symptom_cramps', 'symptom_headache',
        'symptom_breast tenderness',
        'symptom_bloating', 'symptom_insomnia', 'mean_cycle_length',
        'std_cycle_length',
        'avg_period_duration'
    ]
    if not all(feature in data for feature in required_features):
        error_message = "Missing required features in request. Required features are: " + ", ".join(required_features)
        logging.error(error_message)
        return jsonify({
            'success': False,
            'error': error_message
        }), 400
    try:
        prediction_data = {
            'user_id_encoded': int(data.get('user_id_encoded')),
            'cycle_start_month': int(data.get('cycle_start_month')),
            'period_duration': float(data.get('period_duration')),
            'days_until_ovulation': float(data.get('days_until_ovulation')),
            'flow_Heavy': float(data.get('flow_Heavy')),
            'flow_Light': float(data.get('flow_Light')),
            'flow_Medium': float(data.get('flow_Medium')),
            'symptom_acne': float(data.get('symptom_acne')),
            'symptom_mood swings': float(data.get('symptom_mood_swings')),
            'symptom_fatigue': float(data.get('symptom_fatigue')),
            'symptom_cramps': float(data.get('symptom_cramps')),
            'symptom_headache': float(data.get('symptom_headache')),
            'symptom_breast tenderness': float(data.get('symptom_breast_tenderness')),
            'symptom_bloating': float(data.get('symptom_bloating')),
            'symptom_insomnia': float(data.get('symptom_insomnia')),
            'mean_cycle_length': float(data.get('mean_cycle_length')),
            'std_cycle_length': float(data.get('std_cycle_length')),
            'avg_period_duration': float(data.get('avg_period_duration'))
        }
        if model:
            predicted_cycle_length = predict_cycle_length(model, prediction_data)
        else:
            logging.error("Model not loaded.  Using default value.")
            predicted_cycle_length = 28
        if predicted_cycle_length is None:
            return jsonify({
                'success': False,
                'error': 'Failed to predict cycle length.  See server logs for details.'
            }), 500

        logging.info(f"Predicted cycle length: {predicted_cycle_length}")
        return jsonify({
            'success': True,
            'predicted_cycle_length': predicted_cycle_length
        }), 200
    except ValueError:
        error_message = "Invalid data type for features.  Please ensure all values are of the correct type (e.g., int, float)."
        logging.error(error_message)
        return jsonify({
            'success': False,
            'error': error_message
        }), 400
    except KeyError as e:
        error_message = f"Missing key in request data: {e}"
        logging.error(error_message)
        return jsonify({'success': False, 'error': error_message}), 400
    except Exception as e:
        logging.exception(f"Exception in /predict_cycle: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred. See server logs for details.'}), 500

# Routes to serve static content and templates
@app.route('/')
def serve_login():
    return render_template('login.html')

@app.route('/register')
def serve_register():
    return render_template('register.html')

@app.route('/home')
@login_required  # Apply the login_required decorator here
def serve_home():
    return render_template('home.html')

@app.route('/profile')
@login_required  # Apply the login_required decorator here
def serve_profile():
    return render_template('profile.html')

@app.route('/period-tracker')
@login_required
def serve_period_tracker():
    return render_template('period_tracker.html')

@app.route('/insights')
@login_required
def serve_insights():
    return render_template('insights.html')

@app.route('/health-wellness')
@login_required
def serve_health_wellness():
    return render_template('health_wellness.html')

@app.route('/journal-notes')
@login_required
def serve_journal_notes():
    return render_template('journal_notes.html')

@app.route('/settings')
@login_required
def serve_settings():
    return render_template('settings.html')

@app.route('/static/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(STATIC_DIR, 'assets/' + filename)

@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(STATIC_DIR, 'css/' + filename)

@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(STATIC_DIR, 'js/' + filename)

if __name__ == '__main__':
    # Check if the database file exists before initializing
    if not os.path.isfile(DATABASE):
        try:
            init_db()  # Initialize the database if it doesn't exist
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            # Consider if you want to exit the application here
            exit(1)  # Exit the application if database initialization fails

    app.run(debug=True, port=5000)
