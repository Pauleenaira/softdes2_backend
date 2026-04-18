import sqlite3
import os

def check_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "cafe.db")
    
    if not os.path.exists(db_path):
        print("Database not found! Run app.py first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, full_name, username, password, role FROM users")
    users = cursor.fetchall()
    
    print("\n=== CURRENT USERS IN SQLITE DATABASE ===")
    print(f"{'ID':<10} | {'NAME':<15} | {'USERNAME':<15} | {'PASSWORD':<15} | {'ROLE'}")
    print("-" * 70)
    
    if not users:
        print("No users found in the database!")
    
    for u in users:
        # u[0]=id, u[1]=name, u[2]=username, u[3]=password, u[4]=role
        print(f"{u[0]:<10} | {u[1]:<15} | {u[2]:<15} | '{u[3]}'{'':<15} | {u[4]}")
        
    print("-" * 70)
    conn.close()

if __name__ == "__main__":
    check_db()