import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from mercado_logic import get_tenders
from analyst import analyze_tender

# Consts
CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def send_email(subject, html_body, to_email, config):
    sender_email = config.get("email_user")
    password = config.get("email_pass")
    
    if not sender_email or not password:
        print("❌ Error: Email credentials not found in config.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_body, 'html'))

    try:
        # Connect to Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"✅ Email sent successfully to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def run_digest():
    config = load_config()
    ticket = config.get("api_ticket")
    gemini_key = config.get("gemini_key")
    
    # Use config values or fallback
    target_keyword = config.get("last_keyword", "computacion")
    target_profile = config.get("last_profile", "Empresa de tecnología general")
    target_email = config.get("email_to") or config.get("email_user") # Fallback to self if no recipient configured
    
    print(f"Fetching tenders for today (Keyword: {target_keyword})...")
    # Default uses today's date if not specified
    tenders = get_tenders(keyword=target_keyword, ticket=ticket) 
    
    if not tenders:
        print("No tenders found today.")
        return

    print(f"found {len(tenders)} tenders. Analyzing for profile: {target_profile[:30]}...")
    
    analyzed_results = []
    
    # Analyze first 5 to avoid quota limits/spamming for demo
    limit = 5
    for i, t in enumerate(tenders[:limit]):
        print(f"Analyzing {i+1}/{limit}: {t['Nombre']}...")
        analysis = analyze_tender(t['Nombre'], description=f"Organismo: {t['Organismo']}", criteria=target_profile, api_key=gemini_key)
        
        # Add analysis to tender object
        t['Score'] = analysis['score']
        t['Reason'] = analysis['reason']
        
        # Ensure Link is present (using our Google Search strategy)
        t['Link'] = f"https://www.google.com/search?q=site:mercadopublico.cl+%22{t.get('CodigoExterno')}%22"
        
        analyzed_results.append(t)
        
    # Generate HTML
    html = """
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #2E86C1;">📊 Reporte Diario de Licitaciones</h2>
        <p>Aquí tienes el resumen de las licitaciones más relevantes de hoy:</p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 10px; border: 1px solid #ddd;">Score</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Nombre</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Cierre</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Link</th>
            </tr>
    """
    
    for t in analyzed_results:
        color = "green" if t['Score'] >= 70 else "orange" if t['Score'] >= 40 else "red"
        html += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; color: {color}; font-weight: bold;">{t['Score']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <b>{t['Nombre']}</b><br>
                    <small>{t['Organismo']}</small><br>
                    <i>{t['Reason']}</i>
                </td>
                <td style="padding: 10px; border: 1px solid #ddd;">{t['FechaCierre']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;"><a href="{t['Link']}">Ver Ficha</a></td>
            </tr>
        """
        
    html += """
        </table>
        <p><i>Generado por Tender Vibe Assistant 🤖</i></p>
    </body>
    </html>
    """
    
    # Send
    date_str = datetime.datetime.now().strftime("%d-%m-%Y")
    send_email(f"Licitaciones del Día ({date_str}) - {target_keyword}", html, target_email, config)

if __name__ == "__main__":
    run_digest()
