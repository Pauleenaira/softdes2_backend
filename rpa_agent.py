import requests
import time

API_URL = "http://127.0.0.1:5000/api"

def run_automation_cycle():
    print("🤖 Bot: Checking inventory levels...")
    
    # 1. Ask the POS for the low-stock list
    try:
        response = requests.get(f"{API_URL}/inventory/reorder-list")
        reorder_list = response.json()
        
        if not reorder_list:
            print("🤖 Bot: Everything looks good. No reorders needed.")
            return

        for item in reorder_list:
            print(f"🤖 Bot: Starting reorder for {item['item_name']}...")
            
            # 2. SIMULATE THE WORK (In real life, this would use Selenium to log into a website)
            # We will simulate a "Supplier Email" being sent
            task_msg = f"Automatically sent PO to {item['supplier']} for {item['reorder_qty']} {item['unit']} of {item['item_name']}."
            
            # 3. REPORT BACK TO THE DASHBOARD
            requests.post(f"{API_URL}/rpa/log", json={
                "bot_name": "Inventory-Master-V1",
                "task_description": task_msg,
                "status": "Completed"
            })
            
            print(f"✅ Bot: Successfully reordered {item['item_name']}")

    except Exception as e:
        print(f"❌ Bot Error: {e}")

if __name__ == "__main__":
    # Run once every 60 seconds (for testing)
    while True:
        run_automation_cycle()
        time.sleep(60)