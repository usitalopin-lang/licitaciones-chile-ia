import requests
import json
import datetime

CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Config file not found.")
        return None

config = load_config()
ticket = config.get("api_ticket")

if not ticket:
    print("No ticket found in config.")
    exit()

date_str = "06012026" # User mentioned this date had issues
url = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
params = {
    "fecha": date_str,
    "ticket": ticket
}

print(f"Querying for date: {date_str}")
try:
    response = requests.get(url, params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Keys in response: {data.keys()}")
        
        if "Listado" in data:
            items = data["Listado"]
            print(f"Found {len(items)} items.")
            if items:
                print("Sample Item 1:")
                print(json.dumps(items[0], indent=2))
                
                # Check unique states
                states = set()
                for item in items:
                    states.add(item.get("CodigoEstado"))
                print(f"Unique CodigoEstados found: {states}")
        else:
            print("No 'Listado' in response.")
            print(json.dumps(data, indent=2))
    else:
        print("Request failed.")
except Exception as e:
    print(f"Error: {e}")
