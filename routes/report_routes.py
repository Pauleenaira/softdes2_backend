import sqlite3
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

report_bp = Blueprint('reports', __name__)

def get_db_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "cafe.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

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

# ==========================================
# 1. SUMMARY KPI ROUTE
# ==========================================
@report_bp.route("/range", methods=["GET"])
def get_range_report():
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    try:
        if start_str and end_str:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else:
            start_date = datetime.min
            end_date = datetime.max

        conn = get_db_connection()
        sales = conn.execute("SELECT order_id, line_total, category, datetime FROM sales").fetchall()
        conn.close()

        total_sales = 0.0
        unique_orders = set()
        category_counts = {}

        # The bad data we want to ignore from old tests
        invalid_categories = ['Walk-in', 'Table 1', 'Table 2', 'Table 3', 'None', '', 'Drink']

        for row in sales:
            row_date = parse_db_date(row['datetime'])
            if row_date and start_date <= row_date <= end_date:
                total_sales += float(row['line_total'])
                unique_orders.add(row['order_id'])
                
                cat = str(row['category'])
                # 🔥 THE BOUNCER: Only count real categories
                if cat not in invalid_categories:
                    category_counts[cat] = category_counts.get(cat, 0) + 1

        total_orders = len(unique_orders)
        avg_order = (total_sales / total_orders) if total_orders > 0 else 0.0
        top_category = max(category_counts, key=category_counts.get) if category_counts else "—"

        return jsonify({
            "total_sales": round(total_sales, 2),
            "total_orders": total_orders,
            "avg_order": round(avg_order, 2),
            "top_category": top_category
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================
# 2. CHART DATA ROUTE
# ==========================================
@report_bp.route("/chart", methods=["GET"])
def get_chart_data():
    days_range = int(request.args.get('range', 7))
    
    conn = get_db_connection()
    sales = conn.execute("SELECT line_total, datetime FROM sales").fetchall()
    conn.close()
    
    try:
        valid_sales = []
        for row in sales:
            rd = parse_db_date(row['datetime'])
            if rd:
                valid_sales.append({"date": rd, "total": float(row['line_total'])})
                
        if not valid_sales: return jsonify([])
            
        max_date = max(sale["date"] for sale in valid_sales)
        cutoff_date = max_date - timedelta(days=days_range)
        
        daily_sales = {}
        for sale in valid_sales:
            if sale["date"] > cutoff_date:
                d_str = sale["date"].strftime("%b %d")
                daily_sales[d_str] = daily_sales.get(d_str, 0) + sale["total"]
                
        chart_data = []
        for i in range(days_range - 1, -1, -1):
            curr_date = max_date - timedelta(days=i)
            d_str = curr_date.strftime("%b %d")
            chart_data.append({
                "date": d_str,
                "sales": round(daily_sales.get(d_str, 0.0), 2)
            })
            
        return jsonify(chart_data)
    except Exception as e:
        return jsonify([]), 500


# ==========================================
# 3. DAILY TABLE ROUTE
# ==========================================
@report_bp.route("/daily", methods=["GET"])
def get_daily_table():
    conn = get_db_connection()
    sales = conn.execute("SELECT order_id, line_total, category, datetime FROM sales").fetchall()
    conn.close()
    
    daily_summary = {}
    invalid_categories = ['Walk-in', 'Table 1', 'Table 2', 'Table 3', 'None', '', 'Drink']
    
    try:
        for row in sales:
            row_date = parse_db_date(row['datetime'])
            if not row_date: continue
                
            clean_date_str = row_date.strftime("%Y-%m-%d")
            
            if clean_date_str not in daily_summary:
                daily_summary[clean_date_str] = {"orders": set(), "total_sales": 0.0, "categories": {}}
                
            daily_summary[clean_date_str]["orders"].add(row['order_id'])
            daily_summary[clean_date_str]["total_sales"] += float(row['line_total'])
            
            cat = str(row['category'])
            # 🔥 THE BOUNCER: Only count real categories
            if cat not in invalid_categories:
                daily_summary[clean_date_str]["categories"][cat] = daily_summary[clean_date_str]["categories"].get(cat, 0) + 1

        formatted_data = []
        for date_str, data in sorted(daily_summary.items(), reverse=True): 
            order_count = len(data["orders"])
            mock_handling_time = round(1.2 + (order_count * 0.05), 1)
            
            top_cat = max(data["categories"], key=data["categories"].get) if data["categories"] else "—"
            
            formatted_data.append({
                "date": date_str,
                "orders": order_count,
                "total_sales": round(data["total_sales"], 2),
                "avg_handling": f"{mock_handling_time} s",
                "top_category": top_cat
            })
            
        return jsonify(formatted_data[:15])
    except Exception as e:
        return jsonify([]), 500