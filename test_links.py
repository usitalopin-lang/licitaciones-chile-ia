import requests

def test_links():
    code = "1030177-1-LP26" # Use a real recent ID from previous output
    
    candidates = [
        f"https://www.mercadopublico.cl/Home/Busqueda?m=3&q={code}",
        f"https://www.mercadopublico.cl/Home/Busqueda?term={code}",
        f"https://www.mercadopublico.cl/Posk/Busqueda/Licitacion?termino={code}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"Testing links for {code}...\n")
    
    for url in candidates:
        try:
            print(f"Trying: {url}")
            resp = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
            print(f"Status: {resp.status_code}")
            print(f"Final URL: {resp.url}")
            
            # Check for error text in body
            if "Permiso" in resp.text:
                print("Result: PERMISSION DENIED ❌")
            elif "Error" in resp.text and "encuentra" in resp.text:
                 print("Result: NOT FOUND ❌")
            elif resp.status_code == 200:
                print("Result: SUCCESS (Maybe) ✅")
            else:
                print("Result: UNKNOWN ❓")
            print("-" * 20)
            
        except Exception as e:
            print(f"Error: {e}")
            print("-" * 20)

if __name__ == "__main__":
    test_links()
