import sqlite3
import os
from datetime import datetime
from flask import Blueprint, request, jsonify

rpa_bp = Blueprint('rpa', __name__)

def get_db_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "cafe.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# 1. API for the Bot to send logs (POST)
@rpa_bp.route("/log", methods=["POST"])
def add_log():
    data = request.get_json()
    bot_name = data.get("bot_name", "Unknown Bot")
    task = data.get("task_description", "No description provided")
    status = data.get("status", "Info")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = get_db_connection()
        # Ensure the logs table exists
        conn.execute('''
            CREATE TABLE IF NOT EXISTS rpa_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                bot_name TEXT,
                task_description TEXT,
                status TEXT
            )
        ''')
        
        conn.execute('''
            INSERT INTO rpa_logs (timestamp, bot_name, task_description, status)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, bot_name, task, status))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. API for React to read the logs (GET)
@rpa_bp.route("/logs", methods=["GET"])
def get_logs():
    try:
        conn = get_db_connection()
        logs = conn.execute("SELECT * FROM rpa_logs ORDER BY id DESC LIMIT 50").fetchall()
        conn.close()
        return jsonify([dict(row) for row in logs])
    except Exception as e:
        # If table doesn't exist yet, return empty list
        return jsonify([])