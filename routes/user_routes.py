import sqlite3
import os
from flask import Blueprint, request, jsonify

user_bp = Blueprint('users', __name__)

def get_db_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "cafe.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@user_bp.route("/", methods=["GET"])
def get_users():
    conn = get_db_connection()
    users = conn.execute("SELECT user_id, full_name, username, role, status FROM users").fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@user_bp.route("/", methods=["POST"])
def add_user():
    data = request.get_json()
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO users (user_id, full_name, username, password, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data.get('user_id'), data.get('full_name'), data.get('username'), 
              data.get('password'), data.get('role'), data.get('status', 'Active')))
        conn.commit()
        return jsonify({"success": True}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or ID already exists!"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# 🔥 NEW: The Delete Route!
@user_bp.route("/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    # Security: Prevent the system from deleting the Master Admin!
    if user_id == 'ADM001' or user_id.lower() == 'admin':
        return jsonify({"error": "Cannot delete the master admin account!"}), 403

    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "User not found."}), 404
            
        return jsonify({"success": True, "message": "User deleted successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()