import sqlite3
import os
import jwt
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)
SECRET_KEY = "your-cafe-pos-secret-key-2026"

def get_db_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "cafe.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    
    # 1. Safely extract and TRIM spaces from inputs to prevent typos
    raw_id = data.get('username')
    raw_pw = data.get('password')
    
    # Convert to string and remove trailing/leading spaces
    login_id = str(raw_id).strip() if raw_id else ""
    password = str(raw_pw).strip() if raw_pw else ""

    # 2. Print exactly what React is sending to the backend!
    print(f"\n=== LOGIN DEBUG ===")
    print(f"React sent ID: '{login_id}'")
    print(f"React sent PW: '{password}'")
    print(f"===================\n")

    conn = get_db_connection()
    
    # 3. Use LOWER() to make the username/ID case-insensitive
    user = conn.execute('''
        SELECT * FROM users 
        WHERE (LOWER(username) = LOWER(?) OR LOWER(user_id) = LOWER(?)) 
        AND password = ?
    ''', (login_id, login_id, password)).fetchone()
    
    conn.close()

    if user:
        print("[SUCCESS] Credentials matched a database row!")
        if user['status'] == 'Disabled':
            return jsonify({'error': 'Account is disabled. Contact Admin.'}), 403

        token = jwt.encode({
            'username': user['username'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({
            'token': token,
            'role': user['role'],
            'username': user['username'],
            'full_name': user['full_name']
        })
    
    print("[FAILED] Credentials did not match anything in the database.")
    return jsonify({'error': 'Invalid username or password'}), 401


# --- THE SECURITY BOUNCER ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(data, *args, **kwargs)
    return decorated