import os
import pandas as pd
from flask import Blueprint, jsonify, request
from datetime import timedelta

dashboard_bp = Blueprint('dashboard', __name__)

def load_data():
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(basedir, "data", "monthly_Sales.csv")
    
    try:
        # Using Pandas to handle the DD/MM/YYYY format efficiently
        df = pd.read_csv(csv_path)
        # 🔥 FIX 1: Use dayfirst=True to match your CSV format (e.g., 18/04/2026)
        df["datetime"] = pd.to_datetime(df["datetime"], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['datetime'])
        return df
    except Exception as e:
        print(f"Error loading dashboard data: {e}")
        return pd.DataFrame()

@dashboard_bp.route("/stats", methods=["GET"]) # 🔥 FIX 2: Route must match React's /stats call
def get_stats():
    try:
        # Get range from URL (default to 1 day)
        range_days = int(request.args.get("range", 1))
        df = load_data()

        if df.empty:
            return jsonify({
                "total_revenue": 0, "total_orders": 0, 
                "items_sold": 0, "alerts": 0, "recent_orders": []
            })

        df["date_only"] = df["datetime"].dt.date
        
        # 🔥 FIX 3: Anchor "Today" to the latest date in your CSV (April 16)
        # instead of the real-world today (April 18), so the filter finds data.
        latest_date = df["date_only"].max()
        start_date = latest_date - timedelta(days=range_days - 1)

        # Filter data based on the selected range
        filtered_df = df[df["date_only"] >= start_date]

        # Calculate KPIs using keys that match your React Dashboard state
        total_revenue = filtered_df["line_total"].sum()
        total_orders = filtered_df["order_id"].nunique()
        items_sold = filtered_df["qty"].sum()

        # Prepare Recent Orders table data
        # We sort by datetime to show the most recent transactions first
        recent = filtered_df.sort_values(by="datetime", ascending=False).head(5)
        recent_list = []
        for _, row in recent.iterrows():
            recent_list.append({
                "datetime": row["datetime"].strftime("%Y-%m-%d %H:%M"),
                "order_id": int(row["order_id"]),
                "item_name": row["item_name"],
                "qty": int(row["qty"]),
                "line_total": float(row["line_total"]),
                "payment_method": row["payment_method"]
            })

        return jsonify({
            "total_revenue": float(total_revenue), # Matches React: statsData.total_revenue
            "total_orders": int(total_orders),     # Matches React: statsData.total_orders
            "items_sold": int(items_sold),         # Matches React: statsData.items_sold
            "alerts": 0,                           # Placeholder for Low Stock count
            "recent_orders": recent_list           # Matches React: statsData.recent_orders
        })

    except Exception as e:
        print(f"Dashboard Error: {e}")
        return jsonify({"error": str(e)}), 500