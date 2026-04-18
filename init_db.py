import sqlite3
import pandas as pd
import os

def setup_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    db_path = os.path.join(data_dir, "cafe.db")
    
    # Define where the CSVs are located
    csv_inventory_path = os.path.join(base_dir, "cafe_ingredients_inventory.csv")
    csv_sales_path = os.path.join(data_dir, "monthly_Sales.csv") # <-- Your new path!
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ==========================================
    # 1. SETUP INVENTORY TABLE
    # ==========================================
    cursor.execute('DROP TABLE IF EXISTS inventory')
    cursor.execute('''
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT UNIQUE, category TEXT,
            unit TEXT, current_stock INTEGER, reorder_level INTEGER, reorder_qty INTEGER,
            status TEXT, supplier TEXT
        )
    ''')

    if os.path.exists(csv_inventory_path):
        print(f"Deploying with Inventory CSV data from: {csv_inventory_path}")
        raw_df = pd.read_csv(csv_inventory_path)
        clean_df = raw_df.dropna(subset=['ingredient_name', 'stock_qty', 'reorder_level'])
        clean_df.loc[:, 'supplier'] = clean_df['supplier'].fillna('Unknown')
        clean_df.loc[:, 'unit'] = clean_df['unit'].fillna('pcs')
        clean_df.loc[:, 'ingredient_name'] = clean_df['ingredient_name'].astype(str).str.strip()
        clean_df = clean_df.drop_duplicates(subset=['ingredient_name'], keep='first')
        
        for _, row in clean_df.iterrows():
            stock = int(float(row['stock_qty']))
            reorder_lvl = int(float(row['reorder_level']))
            reorder_amt = int(float(row.get('reorder_qty', 0))) 
            
            status = "Normal"
            if stock <= 0: status = "Out of Stock"
            elif stock <= (reorder_lvl * 0.25): status = "Critical"
            elif stock <= reorder_lvl: status = "Low"

            cursor.execute('''
                INSERT INTO inventory (item_name, category, unit, current_stock, reorder_level, reorder_qty, status, supplier)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row['ingredient_name'], row['storage_type'], row['unit'], stock, reorder_lvl, reorder_amt, status, row['supplier']))
        print(f"Success! {len(clean_df)} inventory items synced.")
    else:
        print(f"Warning: {csv_inventory_path} not found.")

    # ==========================================
    # 2. SETUP SALES TABLE (NEW!)
    # ==========================================
    cursor.execute('DROP TABLE IF EXISTS sales')
    cursor.execute('''
        CREATE TABLE sales (
            order_id INTEGER, order_line_id INTEGER, datetime TEXT,
            item_id TEXT, item_name TEXT, category TEXT, size TEXT,
            qty INTEGER, unit_price REAL, addons TEXT,
            addons_total REAL, line_total REAL, payment_method TEXT,
            time_of_order TEXT
        )
    ''')

    if os.path.exists(csv_sales_path):
        print(f"Deploying with Sales CSV data from: {csv_sales_path}")
        sales_df = pd.read_csv(csv_sales_path)
        
        # Preprocessing: Drop rows with missing critical sales data
        sales_df = sales_df.dropna(subset=['order_id', 'item_name', 'qty', 'line_total'])
        
        # Fill missing text fields with empty strings or defaults
        sales_df['addons'] = sales_df['addons'].fillna('None')
        sales_df['payment_method'] = sales_df['payment_method'].fillna('Cash')
        sales_df['addons_total'] = sales_df['addons_total'].fillna(0.0)

        # The Magic Trick: Instantly inject the whole dataframe into SQLite!
        sales_df.to_sql('sales', conn, if_exists='append', index=False)
        print(f"Success! {len(sales_df)} sales records synced to SQLite.")
    else:
        print(f"Warning: {csv_sales_path} not found. Ensure it is in the backend/data/ folder.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()