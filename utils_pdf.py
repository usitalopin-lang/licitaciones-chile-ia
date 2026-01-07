from pypdf import PdfReader
import io

def extract_text_from_pdf(file_stream):
    """
    Extracts text from a PDF file stream (bytes).
    Returns string of text or None if error.
    """
    try:
        reader = PdfReader(file_stream)
        text = ""
        # Limit pages to not overwhelm the LLM context window
        max_pages = 5
        count = 0
        for page in reader.pages:
            text += page.extract_text() + "\n"
            count += 1
            if count >= max_pages:
                text += "\n[...Texto truncado después de 5 páginas...]"
                break
        return text
    except Exception as e:
        print(f"PDF Error: {e}")
        return None
