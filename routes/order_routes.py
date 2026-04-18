# backend/routes/order_routes.py
import os
import csv
from datetime import datetime
from flask import Blueprint, request, jsonify

order_bp = Blueprint("orders", __name__)

CSV_HEADERS = [
    "order_id",
    "order_line_id",
    "datetime",
    "item_id",
    "item_name",
    "category",
    "size",
    "qty",
    "unit_price",
    "addons",
    "addons_total",
    "line_total",
    "payment_method",
    "time_of_order",
]


def get_csv_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "monthly_Sales.csv")


def get_next_order_id():
    csv_path = get_csv_path()
    if not os.path.exists(csv_path):
        return 1

    max_order_id = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                oid = int(row.get("order_id", 0))
                if oid > max_order_id:
                    max_order_id = oid
            except ValueError:
                continue
    return max_order_id + 1


@order_bp.route("/", methods=["POST"])
def create_order():
    """
    Expected JSON body from frontend:
    {
      "items": [
        {
          "id": "...",
          "name": "Matcha",
          "size": "grande",
          "addons": [{ "name": "Oreo", "price": 10 }, ...],
          "unitPrice": 58,
          "qty": 2
        },
        ...
      ],
      "total": 250.0,
      "cash": 300.0,
      "change": 50.0,
      "table": "Walk-in",
      "payment_method": "Cash"
    }
    """
    try:
        data = request.get_json(force=True, silent=False)

        items = data.get("items", [])
        total = float(data.get("total", 0))
        cash = float(data.get("cash", 0))
        change = float(data.get("change", 0))
        table = data.get("table", "Walk-in")
        payment_method = data.get("payment_method", "Cash")

        if not items:
            return jsonify({"error": "Cart is empty"}), 400

        order_id = get_next_order_id()
        now = datetime.now()
        dt_str = now.strftime("%Y-%m-%d %H:%M:%S")
        time_str = now.strftime("%H:%M:%S")

        csv_path = get_csv_path()
        file_exists = os.path.exists(csv_path)

        rows_to_write = []
        line_index = 1

        for item in items:
            name = item.get("name", "")
            size = item.get("size", "")
            qty = int(item.get("qty", 1))
            unit_price = float(item.get("unitPrice", 0))

            # addons: list of { name, price }
            addons_list = item.get("addons", []) or []
            addons_names = ", ".join(a.get("name", "") for a in addons_list)
            addons_total = sum(float(a.get("price", 0)) for a in addons_list)

            line_total = unit_price * qty

            # You said item_id matters, but you didn't give IDs per menu item.
            # We'll generate a simple one: f"{order_id}-{line_index}"
            item_id = f"{order_id}-{line_index}"

            row = {
                "order_id": str(order_id),
                "order_line_id": str(line_index),
                "datetime": dt_str,
                "item_id": item_id,
                "item_name": name,
                "category": table,  # you can change this if you have real category
                "size": size,
                "qty": str(qty),
                "unit_price": f"{unit_price:.2f}",
                "addons": addons_names,
                "addons_total": f"{addons_total:.2f}",
                "line_total": f"{line_total:.2f}",
                "payment_method": payment_method,
                "time_of_order": time_str,
            }
            rows_to_write.append(row)
            line_index += 1

        # Append to CSV
        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            if not file_exists:
                writer.writeheader()
            for row in rows_to_write:
                writer.writerow(row)

        return jsonify(
            {
                "success": True,
                "order_id": order_id,
                "total": total,
                "cash": cash,
                "change": change,
                "lines_written": len(rows_to_write),
            }
        ), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@order_bp.route("/", methods=["GET"])
def list_orders():
    """
    Simple list of order_ids and totals (for future use).
    """
    try:
        csv_path = get_csv_path()
        if not os.path.exists(csv_path):
            return jsonify([])

        orders = {}
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                oid = row.get("order_id")
                if not oid:
                    continue
                line_total = float(row.get("line_total", 0))
                dt = row.get("datetime")

                if oid not in orders:
                    orders[oid] = {
                        "order_id": oid,
                        "datetime": dt,
                        "total": 0.0,
                    }
                orders[oid]["total"] += line_total
                # latest datetime
                if dt and orders[oid]["datetime"]:
                    if dt > orders[oid]["datetime"]:
                        orders[oid]["datetime"] = dt

        return jsonify(list(orders.values()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500