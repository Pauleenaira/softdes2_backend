import os
import pandas as pd
from flask import Blueprint, request, jsonify

report_bp = Blueprint('reports', __name__)

# ================= BACKEND =================
# LOAD CSV DATA WITH ABSOLUTE PATH AND DATE FIX
def load_data():
    # Set up absolute path to prevent "File Not Found" errors
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(basedir, "data", "monthly_Sales.csv")
    
    try:
        df = pd.read_csv(csv_path)
        df = df.dropna()

        # 🔥 THE FIX: Added dayfirst=True and errors='coerce' to handle DD/MM/YYYY
        df["datetime"] = pd.to_datetime(df["datetime"], dayfirst=True, errors='coerce')
        
        # Remove any rows where the date couldn't be parsed
        df = df.dropna(subset=['datetime'])
        
        return df
    except Exception as e:
        print(f"Error loading report data: {e}")
        return pd.DataFrame() # Return empty if file fails

# ================= BACKEND =================
# DEFAULT REPORT (KPI)
@report_bp.route('/', methods=['GET'])
def get_reports():
    df = load_data()
    if df.empty:
        return jsonify({"total_sales": 0, "total_orders": 0, "avg_order": 0, "top_category": "N/A"})

    total_sales = df["line_total"].sum()
    total_orders = df["order_id"].nunique()
    avg_order = total_sales / total_orders if total_orders else 0
    
    # Calculate top category
    cat_counts = df["category"].value_counts()
    top_category = cat_counts.idxmax() if not cat_counts.empty else "N/A"

    return jsonify({
        "total_sales": float(total_sales),
        "total_orders": int(total_orders),
        "avg_order": float(avg_order),
        "top_category": top_category
    })

# ================= BACKEND =================
# DATE FILTER REPORT
@report_bp.route('/range', methods=['GET'])
def report_by_range():
    start = request.args.get("start")
    end = request.args.get("end")

    df = load_data()
    if df.empty:
        return jsonify({"total_sales": 0, "total_orders": 0, "avg_order": 0, "top_category": "N/A"})

    df["date_only"] = df["datetime"].dt.date

    # Filter by range if dates are provided
    if start and end:
        filtered = df[
            (df["date_only"] >= pd.to_datetime(start).date()) &
            (df["date_only"] <= pd.to_datetime(end).date())
        ]
    else:
        filtered = df

    total_sales = filtered["line_total"].sum()
    total_orders = filtered["order_id"].nunique()
    avg_order = total_sales / total_orders if total_orders else 0

    cat_counts = filtered["category"].value_counts()
    top_category = cat_counts.idxmax() if not cat_counts.empty else "N/A"

    return jsonify({
        "total_sales": float(total_sales),
        "total_orders": int(total_orders),
        "avg_order": float(avg_order),
        "top_category": top_category
    })

# ================= BACKEND =================
# DAILY SUMMARY (TABLE DATA)
@report_bp.route('/daily', methods=['GET'])
def daily_summary():
    df = load_data()
    if df.empty:
        return jsonify([])

    df["date_only"] = df["datetime"].dt.date
    grouped = df.groupby("date_only")

    result = []
    for date, group in grouped:
        total_sales = group["line_total"].sum()
        total_orders = group["order_id"].nunique()
        cat_counts = group["category"].value_counts()
        top_cat = cat_counts.idxmax() if not cat_counts.empty else "N/A"

        result.append({
            "date": str(date),
            "orders": int(total_orders),
            "total_sales": float(total_sales),
            "top_category": top_cat,
            "avg_handling": "02:15" # Placeholder for demo
        })

    # Sort latest first
    result = sorted(result, key=lambda x: x["date"], reverse=True)
    return jsonify(result)

# ================= BACKEND =================
# CHART DATA
@report_bp.route('/chart', methods=['GET'])
def chart_data():
    range_type = request.args.get("range", "7")
    df = load_data()
    if df.empty:
        return jsonify([])

    df["date_only"] = df["datetime"].dt.date
    
    # Use the max date in the dataset as "today" for historical CSV data
    latest_date = df["date_only"].max()

    if range_type == "1":
        start = latest_date
    elif range_type == "3":
        start = latest_date - pd.Timedelta(days=3)
    elif range_type == "7":
        start = latest_date - pd.Timedelta(days=7)
    elif range_type == "30":
        start = latest_date - pd.Timedelta(days=30)
    else:
        start = latest_date - pd.Timedelta(days=7)

    filtered = df[df["date_only"] >= start]
    grouped = filtered.groupby("date_only")["line_total"].sum().reset_index()

    result = [
        {
            "date": str(row["date_only"]),
            "sales": float(row["line_total"])
        }
        for _, row in grouped.iterrows()
    ]

    return jsonify(result)