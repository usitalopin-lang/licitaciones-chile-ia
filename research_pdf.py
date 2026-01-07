import requests
import json
import datetime

def research_pdf_links():
    date_str = datetime.date.today().strftime("%d%m%Y")
    ticket = "21D64027-871C-4D03-A1CA-90D62AACD9A4" 
    
    url_list = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
    
    # 1. Fetch List
    print(f"Fetching List for {date_str}...")
    try:
        resp = requests.get(url_list, params={"fecha": date_str, "ticket": ticket}, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"List Fetch Error: {e}")
        return

    if "Listado" not in data or not data["Listado"]:
        print("No tenders found.")
        return

    item = data["Listado"][0]
    code = item["CodigoExterno"]
    print(f"Targeting: {code}")

    # 2. Fetch Detail
    print(f"Fetching Detail for {code}...")
    try:
        resp_det = requests.get(url_list, params={"codigo": code, "ticket": ticket}, timeout=10)
        print(f"Status: {resp_det.status_code}")
        
        if resp_det.status_code == 200:
            full_data = resp_det.json()
            # Save to file to inspect manually if needed
            with open("debug_tender.json", "w", encoding="utf-8") as f:
                json.dump(full_data, f, indent=2, ensure_ascii=False)
            print("Saved debug_tender.json")
            
            if "Listado" in full_data and full_data["Listado"]:
                detail = full_data["Listado"][0]
                print(f"Keys in Detail: {list(detail.keys())}")
                if "Adjuntos" in detail:
                    print(f"Adjuntos: {detail['Adjuntos']}")
                else:
                    print("No 'Adjuntos' key.")
        else:
            print(f"Error Body: {resp_det.text}")

    except Exception as e:
        print(f"Detail Fetch Error: {e}")

if __name__ == "__main__":
    research_pdf_links()
