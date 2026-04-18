import sqlite3
import os
import subprocess
from datetime import datetime
from flask import Blueprint, request, jsonify

order_bp = Blueprint('orders', __name__)

def get_db_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "cafe.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to deduct stock safely using LIKE to catch variations
def deduct_stock(cursor, ingredient_keyword, amount):
    cursor.execute('''
        UPDATE inventory 
        SET current_stock = current_stock - ? 
        WHERE LOWER(item_name) LIKE ?
    ''', (amount, f"%{ingredient_keyword.lower()}%"))

@order_bp.route("/", methods=["POST"])
def place_order():
    data = request.get_json()
    cart = data.get('cart', [])
    payment_method = data.get('payment_method', 'Cash')
    
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Generate a new Order ID
    last_order = cursor.execute("SELECT MAX(order_id) FROM sales").fetchone()[0]
    new_order_id = (last_order or 1000) + 1
    
    current_time = datetime.now()
    date_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    time_str = current_time.strftime("%H:%M:%S")

    try:
        line_id = 1
        for item in cart:
            item_name = item.get('item_name', '')
            qty = int(item.get('qty', 1))
            
            # 2. SAVE TO SALES TABLE
            cursor.execute('''
                INSERT INTO sales (
                    order_id, order_line_id, datetime, item_id, item_name, 
                    category, size, qty, unit_price, addons, addons_total, 
                    line_total, payment_method, time_of_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_order_id, line_id, date_str, item.get('id', '00'), 
                item_name, item.get('category', 'Drink'), item.get('size', 'Regular'), 
                qty, item.get('unit_price', 0), item.get('addons', 'None'), 
                item.get('addons_total', 0), item.get('line_total', 0), 
                payment_method, time_str
            ))
            
            # 3. SMART RECIPE DEDUCTION
            name_lower = item_name.lower()
            
            # Deduct Coffee Base
            if any(word in name_lower for word in ["americano", "latte", "espresso", "macchiato", "coffee", "mocha"]):
                deduct_stock(cursor, "coffee bean", 18 * qty)
                
            # Deduct Milk Base
            if any(word in name_lower for word in ["latte", "milk", "frappe", "frappuccino", "cream", "macchiato"]):
                deduct_stock(cursor, "milk", 150 * qty)
                
            # Deduct Lemonade Base
            if "lemon" in name_lower:
                deduct_stock(cursor, "lemon", 1 * qty) 
                
            # Deduct Flavor Syrups/Powders
            if "matcha" in name_lower: deduct_stock(cursor, "matcha", 20 * qty)
            if "strawberry" in name_lower: deduct_stock(cursor, "strawberry", 20 * qty)
            if "blueberry" in name_lower: deduct_stock(cursor, "blueberry", 20 * qty)
            if "lychee" in name_lower: deduct_stock(cursor, "lychee", 20 * qty)
            if "peach" in name_lower: deduct_stock(cursor, "peach", 20 * qty)
            if "caramel" in name_lower: deduct_stock(cursor, "caramel", 20 * qty)
            if any(w in name_lower for w in ["choco", "mocha", "nutella"]): 
                deduct_stock(cursor, "cocoa", 20 * qty)
                
            # 4. DEDUCT ADDONS
            if item.get('addons') and item.get('addons') != 'None':
                addons_list = item.get('addons').split(", ")
                for addon in addons_list:
                    deduct_stock(cursor, addon, 20 * qty)

            line_id += 1

        # 5. UPDATE INVENTORY STATUS
        cursor.execute('''
            UPDATE inventory
            SET status = CASE
                WHEN current_stock <= 0 THEN 'Out of Stock'
                WHEN current_stock <= (reorder_level * 0.25) THEN 'Critical'
                WHEN current_stock <= reorder_level THEN 'Low'
                ELSE 'Normal'
            END
        ''')

        # 6. TRIGGER RPA BOT IF NECESSARY
        # If any item is now Critical, trigger the external RPA script automatically
        critical_check = cursor.execute("SELECT COUNT(*) FROM inventory WHERE status = 'Critical'").fetchone()[0]
        if critical_check > 0:
            # This wakes up the bot to handle reordering immediately
            subprocess.Popen(["python", "rpa_agent.py"]) 

        conn.commit()
        return jsonify({
            "success": True, 
            "message": "Order placed, inventory updated, and RPA notified!", 
            "order_id": new_order_id
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()