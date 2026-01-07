import requests
import random

# Map codes to human readable statuses
CODIGO_ESTADO_MAP = {
    5: "Publicada",
    6: "Cerrada",
    7: "Desierta",
    8: "Adjudicada",
    18: "Revocada",
    19: "Suspendida"
}

def get_tenders(keyword="computacion", ticket=None, start_date=None, end_date=None, only_published=True):
    # FALLBACK MOCK DATA
    url = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
    
    if not ticket:
        print("[WARNING] No API Ticket provided. Using Mock Data.")
        return get_mock_data(keyword)

    if not start_date:
        import datetime
        start_date = datetime.date.today()
        end_date = start_date

    # Prepare logic to loop through dates
    import datetime
    all_tenders = []
    current_date = start_date
    
    # Safety: Limit range to 7 days to prevent API spam/ban
    if (end_date - start_date).days > 7:
        print("[WARN] Range too long, limiting to first 7 days.")
        end_date = start_date + datetime.timedelta(days=7)

    while current_date <= end_date:
        date_str = current_date.strftime("%d%m%Y")
        
        params = {
            "fecha": date_str,
            "ticket": ticket
        }
        
        try:
            # Short timeout for loops to be snappy
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                if "Listado" in data:
                    search_terms = [k.strip().lower() for k in keyword.split(",")]
                    
                    for item in data["Listado"]:
                        name = item.get("Nombre", "").lower()
                        desc = item.get("Descripcion", "").lower()
                        
                        match = False
                        # If keyword is empty string, match everything
                        if keyword.strip() == "":
                             match = True
                        else:
                            for term in search_terms:
                                if term and (term in name or term in desc):
                                    match = True
                                    break
                        
                        if match:
                            # Filter by CodigoEstado. 
                            codigo_estado = item.get("CodigoEstado")
                            
                            # If only_published is True, strictly require 5.
                            # If False, allow everything.
                            if not only_published or codigo_estado == 5:
                                t_obj = {
                                    "CodigoExterno": item.get("CodigoExterno"),
                                    "Nombre": item.get("Nombre"),
                                    "FechaCierre": item.get("FechaCierre"),
                                    "Organismo": item.get("Comprador", {}).get("NombreOrganismo", "Desconocido"),
                                    "Estado": CODIGO_ESTADO_MAP.get(codigo_estado, "Desconocido"), 
                                    "Link": f"https://www.google.com/search?q=site:mercadopublico.cl+%22{item.get('CodigoExterno')}%22",
                                    "FechaPublicacion": date_str
                                }
                                all_tenders.append(t_obj)
                            
        except Exception as e:
            print(f"[ERROR] Failed fetching {date_str}: {e}")
            # Continue to next day even if one fails
            
        current_date += datetime.timedelta(days=1)
        
    if not all_tenders and ticket:
         # If valid ticket but empty result after loop, implies no matches found.
         # DO NOT fallback to mock data, just return empty list so user knows there are no real results.
         print("[INFO] No tenders found via API for these criteria.")
         return []

         
    return all_tenders

def get_mock_data(keyword):
    return [
        {"CodigoExterno": "123-LP24-MOCK", "Nombre": "Licencia Software Antivirus (MOCK)", "FechaCierre": "2024-12-30", "Organismo": "Ministerio de Salud", "Estado": "Publicada"},
        {"CodigoExterno": "456-LQ24-MOCK", "Nombre": "Renovación Notebooks (MOCK)", "FechaCierre": "2024-11-15", "Organismo": "Municipalidad de Santiago", "Estado": "Cerrada"},
        {"CodigoExterno": "789-LR24-MOCK", "Nombre": "Servicio de Cloud Hosting (MOCK)", "FechaCierre": "2025-01-20", "Organismo": "SII", "Estado": "Publicada"},
        {"CodigoExterno": "999-XYZ-MOCK", "Nombre": f"Licitación {keyword} (MOCK)", "FechaCierre": "2025-02-01", "Organismo": "Gobierno Regional", "Estado": "Publicada"}
    ] 
