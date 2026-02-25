from PyPDF2 import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract full text from a PDF file.
    Returns empty string if extraction fails.
    """
    try:
        reader = PdfReader(file_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

        return text.strip()

    except Exception:
        return ""