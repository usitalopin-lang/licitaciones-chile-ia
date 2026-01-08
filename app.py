import streamlit as st
import pandas as pd
import importlib
import mercado_logic
import analyst
importlib.reload(mercado_logic)
importlib.reload(analyst)
from mercado_logic import get_tenders
from analyst import analyze_tender
import db
import time
import io

# Config
st.set_page_config(page_title="Tender Vibe Assistant", page_icon="🚀", layout="wide")

# DB Init
db.init_db()

import json

CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback/Auto-create with user provided defaults so it always works
        default_data = {
            "api_ticket": "21D64027-871C-4D03-A1CA-90D62AACD9A4",
            "gemini_key": ""
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_data, f)
        return default_data

def save_config(t, k, user_email, last_keyword, last_profile):
    data = {"api_ticket": t, "gemini_key": k, "email_to": user_email, "last_keyword": last_keyword, "last_profile": last_profile}
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

config = load_config()
from utils_pdf import extract_text_from_pdf


def format_date(date_str):
    try:
        # Try parsing ISO format
        dt = datetime.datetime.fromisoformat(date_str)
        return dt.strftime("%d-%m-%Y %H:%M")
    except:
        return date_str

# Wrapper for caching to ensure IDs don't shift between runs
@st.cache_data(ttl=3600, show_spinner=False)
def cached_get_tenders(keyword, ticket, start_date, end_date, only_published=True):
    tenders = get_tenders(keyword, ticket=ticket, start_date=start_date, end_date=end_date, only_published=only_published)
    # Ensure Link exists for caching generated from older runs or if logic missed it
    for t in tenders:
        if "Link" not in t:
            # Fallback to Google Search because MP portal blocks external referrers/sessions
            t["Link"] = f"https://www.google.com/search?q=site:mercadopublico.cl+%22{t.get('CodigoExterno')}%22"
    return tenders

def to_excel(tenders_list):
    output = io.BytesIO()
    # Flatten data for nice Excel
    rows = []
    for t in tenders_list:
        # Get AI analysis if available
        ai_score = 0
        ai_reason = "No analizado"
        
        # Check session state
        ss_key = f"analysis_{t['CodigoExterno']}"
        if ss_key in st.session_state:
            res = st.session_state[ss_key]
            ai_score = res['score']
            ai_reason = res['reason']
        # Or check DB if favorited? (Optional, but let's stick to session state for now as it captures live analysis)
            

        rows.append({
            "ID": t['CodigoExterno'],
            "Nombre": t['Nombre'],
            "Organismo": t['Organismo'],
            "Fecha Cierre": t['FechaCierre'],
            "Estado": t.get('Estado', 'Desconocido'),
            "Link": t.get('Link', ''),
            "Score IA": ai_score,
            "Razón IA": ai_reason
        })
    
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Licitaciones')
    return output.getvalue()

# Sidebar
st.sidebar.title("🎛️ Filtros")

# 1. Main Inputs (Moved UP so they are available for saving)
# Load defaults from config if available
default_keyword = config.get("last_keyword", "Tecnología, Computación")
default_profile = config.get("last_profile", "Soy una empresa de tecnología que busca desarrollo de software. No vendo hardware.")

# Define inputs
keyword = st.sidebar.text_input("Palabras Clave (separar por comas)", value=default_keyword)
company_profile = st.sidebar.text_area("Perfil de mi Empresa / Criterios", value=default_profile)

import datetime
today = datetime.date.today()
# Default to looking at today, allow picking a range
date_range = st.sidebar.date_input("Rango de Fechas (Max 7 días)", (today, today))

start_date = today
end_date = today

if isinstance(date_range, tuple):
    if len(date_range) == 2:
        start_date = date_range[0]
        end_date = date_range[1]
    elif len(date_range) == 1:
        start_date = date_range[0]
        end_date = date_range[0]

show_favorites = st.sidebar.checkbox("⭐ Ver Favoritos")
filter_published = st.sidebar.checkbox("✅ Solo Publicadas (Nuevas)", value=True, help="Si se desmarca, mostrará también Adjudicadas, Cerradas, etc.")

st.sidebar.markdown("---")

# 2. Config Section (Now has access to 'keyword' and 'company_profile')
# Inputs with defaults
default_ticket = config.get("api_ticket", "")
default_key = config.get("gemini_key", "")
default_email_to = config.get("email_to", "")

# Collapsible configuration section for APIs
with st.sidebar.expander("🔐 Configurar APIs (Opcional)"):
    st.caption("Ingresa tus propias llaves si deseas.")
    st.markdown("[Obtener Ticket](https://api.mercadopublico.cl) | [Obtener Gemini Key](https://aistudio.google.com/app/apikey)")
    
    api_ticket = st.text_input("Mercado Público Ticket", value=default_ticket, type="password")
    gemini_key = st.text_input("Gemini API Key", value=default_key, type="password")

# Separate section for Email
with st.sidebar.expander("📧 Configurar Reportes"):
    st.caption("Recibe las licitaciones en tu correo.")
    email_to = st.text_input("Email Destinatario", value=default_email_to)

# Global Save Button
if st.sidebar.button("💾 Guardar Configuración"):
    save_config(api_ticket, gemini_key, email_to, keyword, company_profile)
    st.success("¡Configuración guardada!")

# Use config values if input is empty (fallback)
if not api_ticket:
    api_ticket = default_ticket
if not gemini_key:
    gemini_key = default_key

if not api_ticket:
    st.warning("⚠️ Modo Prueba")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Recargar"):
    st.cache_data.clear()
    st.rerun()

st.title("🚀 Asistente de Licitaciones - Vibe Edition")

if show_favorites:
    st.subheader("Tus Licitaciones Guardadas")
    favs = db.get_favorites()
    if favs:
        df_fav = pd.DataFrame(favs)
        st.dataframe(df_fav)
        
        # Helper to visualize delete buttons better
        st.write("Gestionar favoritos:")
        for idx, fav in enumerate(favs):
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.write(f"📌 {fav['Nombre']} ({fav['CodigoExterno']})")
            with col_b:
                if st.button(f"🗑️ Borrar", key=f"del_{fav['CodigoExterno']}_{idx}"):
                    db.remove_favorite(fav['CodigoExterno'])
                    st.rerun()
    else:
        st.info("No tienes favoritos aún.")

else:
    # Load Data
    st.write(f"Buscando licitaciones entre **{start_date} y {end_date}** para: **{keyword}**...")
    tenders = cached_get_tenders(keyword, ticket=api_ticket, start_date=start_date, end_date=end_date, only_published=filter_published)
    
    # BATCH ANALYSIS BUTTON
    if len(tenders) > 0:
        if st.button(f"⚡ Analizar Todo ({len(tenders)} licitaciones)"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, t in enumerate(tenders):
                # Check if already analyzed to save time
                key = f"analysis_{t['CodigoExterno']}"
                if key not in st.session_state:
                    status_text.text(f"Analizando {i+1}/{len(tenders)}: {t['Nombre']}...")
                    
                    # Call AI
                    analysis = analyze_tender(t['Nombre'], description=f"Organismo: {t['Organismo']}", criteria=company_profile, api_key=gemini_key)
                    st.session_state[key] = analysis
                    
                    time.sleep(1) # Polite delay for API
                
                progress_bar.progress((i + 1) / len(tenders))
            
            status_text.success("¡Análisis Completo!")
            # st.rerun() # Removed to prevent UI reset which hides results

    # General Export Button (always visible if results exist)
    if len(tenders) > 0:
        excel_data = to_excel(tenders)
        st.download_button(
            label="📥 Descargar Excel",
            data=excel_data,
            file_name=f"licitaciones_{keyword}_{start_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Display as Grid or Table
    for idx, t in enumerate(tenders):
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.subheader(f"{t['Nombre']}")
                st.caption(f"ID: {t['CodigoExterno']} | {t['Organismo']}")
                st.caption(f"📌 Estado: **{t.get('Estado', 'N/A')}** | Publicado: {t.get('FechaPublicacion', 'N/A')}")
                # Fallback link generation just in case
                link = t.get('Link', f"https://www.google.com/search?q=site:mercadopublico.cl+%22{t.get('CodigoExterno')}%22")
                st.markdown(f"[🔎 Buscar en Google (Ficha)]({link})")
            with col2:
                formatted_date = format_date(t['FechaCierre'])
                st.write(f"📅 **Cierre:**\n{formatted_date}")
            with col3:
                # PDF Uploader
                uploaded_pdf = st.file_uploader("📂 PDF", type="pdf", key=f"pdf_{t['CodigoExterno']}_{idx}", label_visibility="collapsed")
                
                # Unique key for analysis button
                if st.button("🤖 Analizar", key=f"btn_{t['CodigoExterno']}_{idx}"):
                    pdf_bytes = None
                    spinner_text = "🤖 Analizando licitación..."
                    
                    if uploaded_pdf:
                        # Use bytes directly for Gemini Vision (OCR)
                        pdf_bytes = uploaded_pdf.getvalue()
                        spinner_text = "🧠 Leyendo documento adjunto (PDF/Imagen) y analizando..."
                    
                    with st.spinner(spinner_text):
                        # Pass pdf_data instead of extra_context
                        analysis = analyze_tender(t['Nombre'], description=f"Organismo: {t['Organismo']}", criteria=company_profile, api_key=gemini_key, pdf_data=pdf_bytes)
                        st.session_state[f"analysis_{t['CodigoExterno']}"] = analysis
                
            # Analysis Result
            if f"analysis_{t['CodigoExterno']}" in st.session_state:
                res = st.session_state[f"analysis_{t['CodigoExterno']}"]
                score = res.get("score", 0)
                reason = res.get("reason", "No reason provided")
                
                # Visual feedback for PDF
                pdf_badge = ""
                if "[PDF]" in reason:
                    pdf_badge = "📄 **Análisis de PDF** | "
                    reason = reason.replace("[PDF]", "").strip()

                if score >= 70:
                    st.success(f"💡 Score: {score}/100 - {pdf_badge}{reason}")
                elif score >= 40:
                    st.warning(f"⚠️ Score: {score}/100 - {pdf_badge}{reason}")
                else:
                    st.info(f"❄️ Score: {score}/100 - {pdf_badge}{reason}")
                
                if st.button("⭐ Guardar Favorito", key=f"fav_{t['CodigoExterno']}"):
                    t_data = t.copy()
                    t_data['ai_score'] = res['score']
                    t_data['ai_reason'] = res['reason']
                    if db.add_favorite(t_data):
                        st.success("¡Guardado!")
                    else:
                        st.warning("Ya existe en favoritos")

# Footer
st.markdown("---")
st.caption("Powered by Vibe Coding 🚀 & Antigravity")


