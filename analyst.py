import google.generativeai as genai
import json

def analyze_tender(title, description="", criteria="", api_key=None, extra_context="", pdf_data=None):
    # 1. Fallback to Mock if no key
    if not api_key:
        print("[INFO] No API Key provided, using mock analysis.")
        return _mock_analysis()

    # 2. Try Gemini with Fallback Models
    # Prioritizing High Quality Flash 2.0 now that Billing is active
    models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-2.0-flash-lite']
    
    # 3. Prompt Engineering
    context_criteria = f"Criterios/Perfil de la Empresa: {criteria}" if criteria else "Perfil general de tecnología."
    
    # Text-based extra context (deprecated for PDF but kept for compatibility)
    pdf_instruction = ""
    if extra_context:
        pdf_instruction = f"CONTEXTO ADICIONAL (TEXTO): {extra_context[:10000]}\n"
    
    # Vision/PDF instruction
    if pdf_data:
        pdf_instruction += "\n[ADJUNTO PDF: Analiza VISUALMENTE este documento escaneado para extraer requisitos técnicos, fechas y detalles.]"

    prompt = f"""
    ROL: Eres un experto analista de licitaciones públicas en CHILE (Mercado Público).
    IDIOMA: Tu idioma nativo es ESPAÑOL. NO hablas ni entiendes inglés para la salida.
    
    TAREA:
    {context_criteria}
    Evalúa la siguiente licitación y determina si es una buena oportunidad.
    Si hay un documento adjunto (PDF/Imagen), LEELO VISUALMENTE y úsalo para mejorar tu análisis.
    
    DATOS DE LA LICITACIÓN:
    ===
    Título: {title}
    Descripción: {description}
    ===
    
    {pdf_instruction}
    
    FORMATO DE SALIDA (OBLIGATORIO):
    Responde ÚNICAMENTE un objeto JSON válido.
    Campo "reason": DEBE ser en ESPAÑOL. Si usaste el PDF, comienza con "[PDF] ".
    
    {{ "score": int, "reason": "str (Resumen en Español de 20 palabras)" }}
    """

    for model_name in models_to_try:
        # Retry loop for EACH model
        max_retries = 5
        base_delay = 3 # Start with 3 seconds
        
        for attempt in range(max_retries):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                
                # Construct Payload
                content_parts = [prompt]
                if pdf_data:
                    content_parts.append({
                        "mime_type": "application/pdf",
                        "data": pdf_data
                    })
                
                response = model.generate_content(content_parts)
                text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(text)
                
                return {
                    "score": data.get("score", 0),
                    "reason": data.get("reason", "Sin razón clara")
                }
            except Exception as e:
                error_str = str(e)
                # If it's a Quota/Rate Limit error, we WAIT and RETRY
                if "ResourceExhausted" in error_str or "429" in error_str:
                    wait_time = base_delay * (attempt + 1) # 3, 6, 9, 12, 15...
                    print(f"[WARN] Quota hit on {model_name}. Waiting {wait_time}s... ({attempt+1}/{max_retries})")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    # If it's another error (e.g. model not found), try the next model in the list
                    print(f"[WARN] Failed with {model_name} (Non-Quota): {e}")
                    break # Break inner loop to try next model
        
    # If we get here, it means ALL models failed after ALL retries
    print("[ERROR] AI capabilities exhausted.")
    return {
        "score": 0,
        "reason": "⚠️ IA Ocupada (Tráfico Alto). Espera 1 min e intenta de nuevo."
    }

def _heuristic_analysis(title, description, criteria):
    """
    Local logic to simulate AI when API fails.
    Checks for keyword overlap between criteria and tender.
    """
    import string
    
    text_to_scan = (title + " " + description).lower()
    criteria_lower = criteria.lower() if criteria else "tecnologia"
    
    # Remove punctuation from criteria
    translator = str.maketrans('', '', string.punctuation)
    criteria_clean = criteria_lower.translate(translator)
    
    # Common stop words to ignore in profile analysis to avoid generic matches
    stop_words = {"empresa", "busca", "somos", "para", "donde", "pero", "fines", "vendo", "hago", "tener"}
    
    # Extract meaningful keywords (len > 3 and not in stop_words)
    keywords = [w for w in criteria_clean.split() if len(w) > 3 and w not in stop_words]
    
    matches = [w for w in keywords if w in text_to_scan]
    unique_matches = list(set(matches))
    
    score = 0
    reason = ""
    
    if len(unique_matches) > 0:
        # Simple scoring: more matches = higher score. Capped at 95.
        score = min(30 + (len(unique_matches) * 15), 95)
        # Show which specific words from the profile matched
        match_str = ", ".join(unique_matches[:5])
        reason = f"Coincidencia Perfil (Offline): {match_str}"
    else:
        score = 10
        reason = "Sin coincidencias con Perfil (Offline mode)"
        
    return {"score": score, "reason": reason}

def _mock_analysis():
    # Helper for completely disconnected mode
    import random
    score = random.randint(60, 99)
    return {"score": score, "reason": "Modo Prueba Aleatorio"}
