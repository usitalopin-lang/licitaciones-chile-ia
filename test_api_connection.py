import requests
import json
from datetime import datetime

CONFIG_FILE = "config.json"

def test_connection():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        ticket = config.get("api_ticket")
    except:
        print("Config error")
        return

    # Use today's date
    date_str = datetime.now().strftime("%d%m%Y")
    
    url = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
    params = {
        "ticket": ticket,
        "fecha": date_str,
        "estado": "publicada" 
    }
    
    print(f"Connecting to {url} with date={date_str}...")
    try:
        # 30 second timeout
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success! Head of response:")
            print(str(response.json())[:300])
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    test_connection()
