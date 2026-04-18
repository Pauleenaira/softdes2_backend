import os
import sqlite3
from flask import Blueprint, jsonify, request

inventory_bp = Blueprint('inventory', __name__)

def get_db_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "cafe.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# GET: Fetch all inventory items
# ==========================================
@inventory_bp.route("/", methods=["GET"])
def get_inventory():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Sort by Category so items stay grouped together
        cursor.execute("SELECT * FROM inventory ORDER BY category ASC, item_name ASC")
        items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# POST: Add a new item
# ==========================================
@inventory_bp.route("/", methods=["POST"])
def add_item():
    try:
        data = request.get_json(force=True)
        item_name = data.get("item_name")
        category = data.get("category")
        unit = data.get("unit", "pcs")
        current_stock = int(data.get("current_stock", 0))
        reorder_level = int(data.get("reorder_level", 10))
        reorder_qty = int(data.get("reorder_qty", 0))
        supplier = data.get("supplier", "N/A")

        if not item_name or not category:
            return jsonify({"error": "Missing required fields"}), 400

        # Calculate Status based on stock levels
        status = "Normal"
        if current_stock <= 0:
            status = "Out of Stock"
        elif current_stock <= (reorder_level * 0.25):
            status = "Critical"
        elif current_stock <= reorder_level:
            status = "Low"

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO inventory (
                item_name, category, unit, current_stock, 
                reorder_level, reorder_qty, status, supplier
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item_name, category, unit, current_stock, reorder_level, reorder_qty, status, supplier))
        
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Item added successfully!"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Item already exists in inventory"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# PUT: Update an existing item (Edit Mode)
# ==========================================
@inventory_bp.route("/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch current item to ensure it exists
        item = cursor.execute("SELECT * FROM inventory WHERE id = ?", (item_id,)).fetchone()
        if not item:
            conn.close()
            return jsonify({"error": "Item not found"}), 404

        # 2. Extract new values or fallback to current database values
        new_name = data.get("item_name", item["item_name"])
        new_cat = data.get("category", item["category"])
        new_unit = data.get("unit", item["unit"])
        new_stock = int(data.get("current_stock", item["current_stock"]))
        new_reorder_lvl = int(data.get("reorder_level", item["reorder_level"]))
        new_supplier = data.get("supplier", item["supplier"])
        
        # 3. Recalculate Status based on edited values
        status = "Normal"
        if new_stock <= 0:
            status = "Out of Stock"
        elif new_stock <= (new_reorder_lvl * 0.25):
            status = "Critical"
        elif new_stock <= new_reorder_lvl:
            status = "Low"

        # 4. Perform the Update
        cursor.execute('''
            UPDATE inventory 
            SET item_name = ?, category = ?, unit = ?, 
                current_stock = ?, reorder_level = ?, supplier = ?, status = ?
            WHERE id = ?
        ''', (new_name, new_cat, new_unit, new_stock, new_reorder_lvl, new_supplier, status, item_id))

        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Item updated successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# DELETE: Remove an item from inventory
# ==========================================
@inventory_bp.route("/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        item = cursor.execute("SELECT * FROM inventory WHERE id = ?", (item_id,)).fetchone()
        if not item:
            conn.close()
            return jsonify({"error": "Item not found"}), 404
            
        cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Item deleted successfully!"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# RPA: Fetch list of items needing reorder
# ==========================================
@inventory_bp.route("/reorder-list", methods=["GET"])
def get_reorder_list():
    try:
        conn = get_db_connection()
        # Find everything that is Critical, Low, or Out of Stock
        items = conn.execute("""
            SELECT item_name, supplier, reorder_qty, unit 
            FROM inventory 
            WHERE status IN ('Critical', 'Low', 'Out of Stock')
        """).fetchall()
        conn.close()
        return jsonify([dict(row) for row in items])
    except Exception as e:
        return jsonify({"error": str(e)}), 500