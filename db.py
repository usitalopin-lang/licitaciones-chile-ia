import sqlite3
import json

DB_NAME = "tenders.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS favorites
                 (id TEXT PRIMARY KEY, title TEXT, date TEXT, score REAL, reason TEXT)''')
    conn.commit()
    conn.close()

def add_favorite(tender_data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO favorites VALUES (?, ?, ?, ?, ?)",
                  (tender_data['CodigoExterno'], tender_data['Nombre'], tender_data['FechaCierre'], tender_data.get('ai_score', 0), tender_data.get('ai_reason', '')))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_favorites():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM favorites")
    rows = c.fetchall()
    conn.close()
    return [{"CodigoExterno": r[0], "Nombre": r[1], "FechaCierre": r[2], "ai_score": r[3], "ai_reason": r[4]} for r in rows]

def remove_favorite(tender_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE id=?", (tender_id,))
    conn.commit()
    conn.close()
