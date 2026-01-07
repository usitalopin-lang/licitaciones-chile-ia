import requests
import datetime
import json
from mercado_logic import get_tenders

CONFIG_FILE = "config.json"

def debug_run():
    # Load ticket
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        ticket = config.get("api_ticket")
    except:
        print("Config load failed")
        return

    # Define range (User's case: Today 2026-01-06)
    start_date = datetime.date(2026, 1, 6)
    end_date = datetime.date(2026, 1, 6)
    keyword = "Tecnología" # With accent
    
    print(f"Testing range: {start_date} to {end_date} with keyword '{keyword}'")
    print(f"Ticket: {ticket[:10]}...")
    
    # Run the function
    tenders = get_tenders(keyword, ticket, start_date=start_date, end_date=end_date)
    
    print(f"\nTotal Tenders Found: {len(tenders)}")
    for t in tenders[:3]:
        print(f" - {t['Nombre']} ({t['FechaPublicacion']})")

if __name__ == "__main__":
    debug_run()
