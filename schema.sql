DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS cycles;
DROP TABLE IF EXISTS symptoms;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL -- Store the hashed password here!
);

CREATE TABLE cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    start_date TEXT NOT NULL,
    end_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE symptoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id INTEGER,
    symptom_name TEXT NOT NULL,
    severity INTEGER,
    FOREIGN KEY (cycle_id) REFERENCES cycles(id)
);

-- Example: Insert a user (for testing - REMOVE IN PRODUCTION)
-- INSERT INTO users (email, password) VALUES ('test@example.com', 'pbkdf2_sha256_600000some_salt$hashed_password');