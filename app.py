import sqlite3
import os
from flask import Flask
from flask_cors import CORS

# Import route blueprints to handle modular system tasks [cite: 1921]
from routes.report_routes import report_bp
from routes.dashboard_routes import dashboard_bp
from routes.order_routes import order_bp
from routes.inventory_routes import inventory_bp 
from routes.auth_routes import auth_bp  
from routes.user_routes import user_bp  
from routes.rpa_routes import rpa_bp  # For monitoring automated workflows [cite: 1928]

app = Flask(__name__)

# 1. CORS: Facilitates secure data exchange between the React client and Flask server [cite: 1930]
# Updated to trust your live Vercel domain and your local testing environment
CORS(app, resources={r"/api/*": {"origins": ["https://softdes2-frontend.vercel.app", "http://localhost:3000"]}})

# 2. FAIL-SAFE TABLE CREATION: Ensures reliable back-end inventory and record maintenance [cite: 1931, 1932]
def init_sqlite_db():
    # Set up absolute path for the database file to ensure it's found on cloud servers [cite: 1934-1936]
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "data", "cafe.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    # Sales Table: Synchronizes with Kaggle referenced dataset fields [cite: 1939-1943]
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            order_id INTEGER, order_line_id INTEGER, datetime TEXT,
            item_id TEXT, item_name TEXT, category TEXT, size TEXT,
            qty INTEGER, unit_price REAL, addons TEXT,
            addons_total REAL, line_total REAL, payment_method TEXT,
            time_of_order TEXT
        )
    ''')
    
    # Inventory Table: Tracks stock and evaluates levels against reorder thresholds [cite: 1945-1957]
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT UNIQUE,
            category TEXT,
            unit TEXT,
            current_stock INTEGER,
            reorder_level INTEGER,
            reorder_qty INTEGER,
            status TEXT,
            supplier TEXT
        )
    ''')

    # Users Table: Facilitates secure role-based access control [cite: 1958-1967]
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            full_name TEXT,
            username TEXT UNIQUE, 
            password TEXT,
            role TEXT, 
            status TEXT, 
            last_login TEXT
        )
    ''')

    # RPA Logs Table: Records automation activity for real-time monitoring [cite: 1969-1977]
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rpa_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            bot_name TEXT,
            task_description TEXT,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("SQLite check complete: All records and logs are synchronized. [cite: 1980]")

# Initialize DB before starting the server process [cite: 1982]
init_sqlite_db()

# 3. REGISTER BLUEPRINTS: Maps RESTful API endpoints for seamless workflows [cite: 1983-1991]
app.register_blueprint(report_bp, url_prefix='/api/reports')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(order_bp, url_prefix='/api/orders')
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(rpa_bp, url_prefix='/api/rpa')

@app.route("/")
def home():
    # Health check route for Render to monitor service status [cite: 1993, 1994]
    return {"message": "Cafe POS Backend is running", "status": "online"}

if __name__ == "__main__":
    # 🔥 UPDATED FOR DEPLOYMENT: host="0.0.0.0" allows external connections from Vercel
    app.run(host="0.0.0.0", port=5000)