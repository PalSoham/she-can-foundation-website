import os
import sqlite3
import pymysql
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Default credentials for admin panel
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

def get_db_connection():
    db_host = os.getenv("DB_HOST")
    if db_host:
        try:
            # TiDB is MySQL compatible
            connection = pymysql.connect(
                host=db_host,
                port=int(os.getenv("DB_PORT", 4000)),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                ssl={'ca': os.getenv("DB_SSL_CA")} if os.getenv("DB_SSL_CA") else {},
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection, "tidb"
        except Exception as e:
            print(f"TiDB connection failed: {e}. Falling back to SQLite.")
    
    # SQLite Fallback
    db_path = os.path.join(os.path.dirname(__file__), "submissions.db")
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection, "sqlite"

def init_db():
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        if db_type == "tidb":
            create_table_query = """
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        else:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[*] Database initialized successfully using {db_type.upper()}.")
    except Exception as e:
        print(f"[!] Database initialization failed: {e}")

# Call init_db on startup
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/api/submit', methods=['POST'])
def submit_form():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    message = data.get('message', '').strip()
    
    # Server-side Validation
    errors = {}
    if not name:
        errors['name'] = "Name is required."
    elif len(name) < 2:
        errors['name'] = "Name must be at least 2 characters."
        
    if not email:
        errors['email'] = "Email is required."
    elif '@' not in email or '.' not in email:
        errors['email'] = "Invalid email format."
        
    if not message:
        errors['message'] = "Message is required."
    elif len(message) < 10:
        errors['message'] = "Message must be at least 10 characters."

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        if db_type == "tidb":
            query = "INSERT INTO contact_submissions (name, email, message) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, email, message))
        else:
            query = "INSERT INTO contact_submissions (name, email, message) VALUES (?, ?, ?)"
            cursor.execute(query, (name, email, message))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Form Submitted Successfully", "db_used": db_type})
    except Exception as e:
        print(f"[!] Error inserting submission: {e}")
        return jsonify({"success": False, "error": "Database error, please try again later."}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    if username == ADMIN_USER and password == ADMIN_PASS:
        return jsonify({"success": True, "token": "mock-session-token-admin"})
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route('/api/admin/submissions', methods=['GET'])
def get_submissions():
    # Simple token check in headers (for demonstration authentication)
    auth_header = request.headers.get("Authorization")
    if auth_header != "Bearer mock-session-token-admin":
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, name, email, message, created_at FROM contact_submissions ORDER BY created_at DESC"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        submissions = []
        if db_type == "tidb":
            # dict cursor
            submissions = rows
        else:
            # sqlite Row
            for r in rows:
                submissions.append({
                    "id": r["id"],
                    "name": r["name"],
                    "email": r["email"],
                    "message": r["message"],
                    "created_at": r["created_at"]
                })
                
        cursor.close()
        conn.close()
        return jsonify({"success": True, "submissions": submissions, "db_used": db_type})
    except Exception as e:
        print(f"[!] Error fetching submissions: {e}")
        return jsonify({"success": False, "error": "Database error."}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
