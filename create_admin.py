import sqlite3
import os

def create_master_admin():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "cafe.db")
    
    conn = sqlite3.connect(db_path)
    
    # We use INSERT OR REPLACE so if it exists, it just updates it
    conn.execute('''
        INSERT OR REPLACE INTO users (user_id, full_name, username, password, role, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('ADM001', 'System Boss', 'admin', 'admin123', 'Admin', 'Active'))
    
    conn.commit()
    conn.close()
    
    print("\n✅ Master Admin Created Successfully!")
    print("-----------------------------------")
    print("Username / ID: admin (or ADM001)")
    print("Password:      admin123")
    print("Role:          Admin\n")

if __name__ == "__main__":
    create_master_admin()