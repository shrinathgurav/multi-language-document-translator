import io
from typing import List
import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import pytesseract


def _ocr_image(image: Image.Image, ocr_lang: str = "eng") -> str:
    """Runs Tesseract OCR on a PIL Image and returns cleaned text."""
    try:
        text = pytesseract.image_to_string(image, lang=ocr_lang)
        return text.strip()
    except pytesseract.TesseractError:
        # Fallback to default English model if requested language pack is missing
        text = pytesseract.image_to_string(image, lang="eng")
        return text.strip()


def extract_from_image(file_path: str, ocr_lang: str = "eng") -> List[str]:
    """Extracts text from standalone image files (PNG, JPG, WEBP)."""
    with Image.open(file_path) as img:
        text = _ocr_image(img, ocr_lang=ocr_lang)
    return [text] if text else []


def extract_from_txt(file_path: str) -> List[str]:
    """Extracts text from plain UTF-8 text files."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read().strip()
    return [content] if content else []


def extract_from_docx(file_path: str, ocr_lang: str = "eng") -> List[str]:
    """Extracts paragraphs, tables, and embedded images from DOCX files."""
    doc = Document(file_path)
    parts = []

    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text.strip())

    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                parts.append(row_text)

    # Extract embedded images inside the DOCX archive
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_bytes = rel.target_part.blob
            with Image.open(io.BytesIO(image_bytes)) as img:
                ocr_text = _ocr_image(img, ocr_lang=ocr_lang)
                if ocr_text:
                    parts.append(ocr_text)

    full_text = "\n".join(parts).strip()
    return [full_text] if full_text else []


def extract_from_pdf(file_path: str, ocr_lang: str = "eng") -> List[str]:
    """
    Extracts text page-by-page using PyMuPDF (language-neutral Unicode).
    Handles both selectable text, embedded images, and fully scanned pages.
    Returns a list of strings (one string per page).
    """
    pages_text = []
    pdf_doc = fitz.open(file_path)

    for page in pdf_doc:
        page_content = []
        raw_text = page.get_text("text").strip()

        if len(raw_text) >= 20:
            # Page has selectable Unicode text
            page_content.append(raw_text)

            # Also OCR any embedded images on this page (e.g., diagrams or scanned blocks)
            seen_xrefs = set()
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                base_image = pdf_doc.extract_image(xref)
                image_bytes = base_image["image"]
                with Image.open(io.BytesIO(image_bytes)) as img:
                    # Skip tiny icons/bullets
                    if img.width >= 50 and img.height >= 50:
                        img_text = _ocr_image(img, ocr_lang=ocr_lang)
                        if img_text:
                            page_content.append(img_text)
        else:
            # Scanned/image-only page: render entire page at 300 DPI for OCR
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            with Image.open(io.BytesIO(img_bytes)) as page_img:
                scanned_text = _ocr_image(page_img, ocr_lang=ocr_lang)
                if scanned_text:
                    page_content.append(scanned_text)

        combined_page = "\n".join(page_content).strip()
        if combined_page:
            pages_text.append(combined_page)

    pdf_doc.close()
    return pages_text


def extract_document_pages(file_path: str, extension: str, ocr_lang: str = "eng") -> List[str]:
    """Main router that returns extracted text grouped by page/section."""
    if extension == "pdf":
        return extract_from_pdf(file_path, ocr_lang=ocr_lang)
    elif extension == "docx":
        return extract_from_docx(file_path, ocr_lang=ocr_lang)
    elif extension == "txt":
        return extract_from_txt(file_path)
    elif extension in {"png", "jpg", "jpeg", "webp"}:
        return extract_from_image(file_path, ocr_lang=ocr_lang)
    else:
        raise ValueError(f"Unsupported file format: .{extension}")
