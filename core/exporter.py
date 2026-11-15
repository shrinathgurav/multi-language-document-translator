import io
import os
from docx import Document
from fpdf import FPDF
from config import DEFAULT_FONT_PATH, TARGET_FONTS


def export_to_txt(translated_text: str) -> bytes:
    """Exports translated string as UTF-8 encoded TXT bytes."""
    return translated_text.encode("utf-8")


def export_to_docx(translated_text: str) -> bytes:
    """Exports translated string into an in-memory DOCX file."""
    doc = Document()
    for paragraph in translated_text.split("\n"):
        doc.add_paragraph(paragraph)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def export_to_pdf(translated_text: str, target_lang: str = "en") -> bytes:
    """
    Exports translated string into an in-memory PDF file using a script-appropriate
    Unicode font and HarfBuzz text shaping for complex Indic/Arabic scripts.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Enable HarfBuzz text shaping for proper Devanagari/Arabic glyph rendering
    try:
        pdf.set_text_shaping(True)
    except Exception:
        pass

    font_family, font_path = TARGET_FONTS.get(
        target_lang, ("NotoSans", DEFAULT_FONT_PATH)
    )

    if os.path.exists(font_path):
        pdf.add_font(font_family, "", font_path)
        pdf.set_font(font_family, size=11)
        use_unicode = True
    elif os.path.exists(DEFAULT_FONT_PATH):
        pdf.add_font("NotoSans", "", DEFAULT_FONT_PATH)
        pdf.set_font("NotoSans", size=11)
        use_unicode = True
    else:
        pdf.set_font("Helvetica", size=11)
        use_unicode = False

    for line in translated_text.split("\n"):
        if not use_unicode:
            line = line.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 7, text=line)

    return bytes(pdf.output())


def generate_export_file(
    translated_text: str, export_format: str, target_lang: str = "en"
) -> tuple[bytes, str, str]:
    """
    Returns (file_bytes, file_extension, mime_type) for the chosen output format.
    """
    fmt = export_format.upper()
    if fmt == "TXT":
        return export_to_txt(translated_text), "txt", "text/plain"
    elif fmt == "DOCX":
        return (
            export_to_docx(translated_text),
            "docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    elif fmt == "PDF":
        return export_to_pdf(translated_text, target_lang=target_lang), "pdf", "application/pdf"
    else:
        raise ValueError(f"Unsupported export format: {export_format}")
