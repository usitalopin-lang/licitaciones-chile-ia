import google.generativeai as genai
import json

CONFIG_FILE = "config.json"

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    api_key = config.get("gemini_key")
    if not api_key:
        print("No API Key found in config.json")
        exit()

    genai.configure(api_key=api_key)
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

except Exception as e:
    print(f"Error: {e}")
