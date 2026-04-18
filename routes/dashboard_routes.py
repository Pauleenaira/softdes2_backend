import sqlite3
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

dashboard_bp = Blueprint('dashboard', __name__)

def get_db_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "cafe.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# 🔥 The Date Cleaner
def parse_db_date(date_str):
    if not date_str:
        return None
    date_part = date_str.split(' ')[0] 
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_part, fmt)
        except ValueError:
            continue
    return None

@dashboard_bp.route("/stats", methods=["GET"])
def get_dashboard_stats():
    try:
        # 1. Get the range parameter from React (default to 1 day)
        days_range = int(request.args.get('range', 1))
        
        conn = get_db_connection()
        # Fetch all sales, newest first
        sales = conn.execute("SELECT * FROM sales ORDER BY order_id DESC").fetchall()
        
        # Low stock is current, it doesn't depend on date
        low_stock_count = conn.execute("SELECT COUNT(*) FROM inventory WHERE status IN ('Low', 'Critical', 'Out of Stock')").fetchone()[0] or 0
        conn.close()

        # 2. Find the most recent date in the database to act as "Today"
        max_date_found = datetime.min
        for row in sales:
            rd = parse_db_date(row['datetime'])
            if rd and rd > max_date_found:
                max_date_found = rd

        # Calculate the cutoff date based on the dropdown
        cutoff_date = max_date_found - timedelta(days=days_range)

        # 3. Filter the data!
        total_revenue = 0.0
        total_orders_set = set()
        items_sold = 0
        recent_orders = []

        for row in sales:
            rd = parse_db_date(row['datetime'])
            # Only include the row if it happened AFTER the cutoff date
            if rd and rd >= cutoff_date:
                total_revenue += float(row['line_total'])
                total_orders_set.add(row['order_id'])
                items_sold += int(row['qty'])
                
                # Keep track of recent orders for the table (limit 10)
                if len(recent_orders) < 10:
                    recent_orders.append({
                        "datetime": row['datetime'],
                        "order_id": row['order_id'],
                        "item_name": row['item_name'],
                        "qty": row['qty'],
                        "line_total": float(row['line_total']),
                        "payment_method": row['payment_method']
                    })

        return jsonify({
            "total_revenue": round(total_revenue, 2),
            "total_orders": len(total_orders_set),
            "items_sold": items_sold,
            "alerts": low_stock_count,
            "recent_orders": recent_orders
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500