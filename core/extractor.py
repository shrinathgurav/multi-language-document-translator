import io
import os
import re
import shutil
from typing import List
import fitz  # PyMuPDF
from docx import Document
from PIL import Image, ImageOps
import pytesseract

# Auto-detect Tesseract on Windows if not yet in current process PATH
if shutil.which("tesseract") is None:
    for candidate_path in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]:
        if os.path.exists(candidate_path):
            pytesseract.pytesseract.tesseract_cmd = candidate_path
            break


def _clean_pdf_line_breaks(text: str) -> str:
    """
    Merges artificial mid-sentence line breaks into flowing paragraphs while
    keeping headings, bullet points, numbered items, and code lines separate.
    """
    lines = text.splitlines()
    merged = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            merged.append("")
            continue

        # Keep headings (Title Case / short lines without ending punctuation), bullets, and code separate
        is_bullet_or_code = bool(
            re.match(
                r"^(\•|\-|\*|\d+[\.\)]|import |from |CREATE |SELECT |INSERT |UPDATE |DELETE |ALTER |DROP )",
                stripped,
            )
        )
        is_short_heading = (
            len(stripped) < 65
            and not stripped.endswith((".", ",", ";", "।", "॥"))
            and stripped[0].isupper()
        )

        if is_bullet_or_code or is_short_heading:
            merged.append(stripped)
        elif merged and merged[-1] and not merged[-1].endswith((".", "!", "?", ":", ";", "।", "॥")):
            merged[-1] = f"{merged[-1]} {stripped}"
        else:
            merged.append(stripped)

    # Collapse multiple blank lines into clean paragraph breaks
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(merged))
    return cleaned.strip()


def _is_tesseract_available() -> bool:
    """Checks whether tesseract executable is accessible."""
    cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
    return shutil.which(cmd) is not None or os.path.exists(cmd)


def _preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Converts image to grayscale and boosts contrast for sharper OCR accuracy."""
    gray = ImageOps.grayscale(image)
    enhanced = ImageOps.autocontrast(gray, cutoff=2)
    return enhanced


def _ocr_image(image: Image.Image, ocr_lang: str = "eng", strict: bool = False) -> str:
    """Runs Tesseract OCR with image preprocessing and layout segmentation."""
    if not _is_tesseract_available():
        if strict:
            raise RuntimeError(
                "Tesseract OCR is not installed or not found on PATH. "
                "Please install Tesseract OCR (see INSTALLATION.md)."
            )
        return ""

    processed_img = _preprocess_for_ocr(image)
    # --oem 3: Default LSTM neural engine | --psm 3: Automatic page layout segmentation
    custom_config = r"--oem 3 --psm 3"

    try:
        raw_ocr = pytesseract.image_to_string(processed_img, lang=ocr_lang, config=custom_config)
    except pytesseract.TesseractError:
        raw_ocr = pytesseract.image_to_string(processed_img, lang="eng", config=custom_config)

    # Filter out noisy OCR lines that contain mostly symbols or single random characters
    clean_lines = []
    for line in raw_ocr.splitlines():
        s = line.strip()
        if len(s) < 2:
            continue
        alnum_count = sum(c.isalnum() for c in s)
        if alnum_count / len(s) >= 0.5:
            clean_lines.append(s)

    return _clean_pdf_line_breaks("\n".join(clean_lines))


def extract_from_image(file_path: str, ocr_lang: str = "eng") -> List[tuple[int, str]]:
    """Extracts text from standalone image files (PNG, JPG, WEBP)."""
    with Image.open(file_path) as img:
        text = _ocr_image(img, ocr_lang=ocr_lang, strict=True)
    return [(1, text)] if text else []


def extract_from_txt(file_path: str) -> List[tuple[int, str]]:
    """Extracts text from plain UTF-8 text files."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read().strip()
    return [(1, content)] if content else []


def extract_from_docx(file_path: str, ocr_lang: str = "eng") -> List[tuple[int, str]]:
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

    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_bytes = rel.target_part.blob
            with Image.open(io.BytesIO(image_bytes)) as img:
                if img.width >= 120 and img.height >= 120:
                    ocr_text = _ocr_image(img, ocr_lang=ocr_lang, strict=False)
                    if ocr_text:
                        parts.append(ocr_text)

    full_text = "\n\n".join(parts).strip()
    return [(1, full_text)] if full_text else []


def extract_from_pdf(
    file_path: str,
    ocr_lang: str = "eng",
    start_page: int = 1,
    end_page: int | None = None,
    trim_headers_footers: bool = True,
) -> List[tuple[int, str]]:
    """
    Extracts text for a 1-based page range using PyMuPDF.
    Clips top/bottom 7% margins to remove running headers & page numbers,
    skips decorative logos, and preprocesses scanned pages before OCR.
    """
    pages_text = []
    pdf_doc = fitz.open(file_path)
    total_pages = len(pdf_doc)

    start_idx = max(0, start_page - 1)
    end_idx = min(total_pages, end_page) if end_page else total_pages

    for page_idx in range(start_idx, end_idx):
        page = pdf_doc[page_idx]
        actual_page_num = page_idx + 1
        page_content = []

        # Define main content bounding box (exclude top 7% header and bottom 7% footer)
        rect = page.rect
        if trim_headers_footers and rect.height > 200:
            margin_y = rect.height * 0.07
            content_clip = fitz.Rect(rect.x0, rect.y0 + margin_y, rect.x1, rect.y1 - margin_y)
        else:
            content_clip = rect

        raw_text = _clean_pdf_line_breaks(page.get_text("text", clip=content_clip).strip())

        if len(raw_text) >= 25:
            page_content.append(raw_text)

            # Only OCR meaningful embedded content images (skip logos, banners, and tiny icons)
            seen_xrefs = set()
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                base_image = pdf_doc.extract_image(xref)
                image_bytes = base_image["image"]
                with Image.open(io.BytesIO(image_bytes)) as img:
                    aspect_ratio = max(img.width, img.height) / max(1, min(img.width, img.height))
                    if img.width >= 150 and img.height >= 150 and aspect_ratio < 4.5:
                        img_text = _ocr_image(img, ocr_lang=ocr_lang, strict=False)
                        if img_text:
                            page_content.append(img_text)
        else:
            # Scanned/image-only page: render clipped main body at 300 DPI for clean OCR
            pix = page.get_pixmap(dpi=300, clip=content_clip)
            img_bytes = pix.tobytes("png")
            with Image.open(io.BytesIO(img_bytes)) as page_img:
                scanned_text = _ocr_image(page_img, ocr_lang=ocr_lang, strict=True)
                if scanned_text:
                    page_content.append(scanned_text)

        combined_page = "\n\n".join(page_content).strip()
        if combined_page:
            pages_text.append((actual_page_num, combined_page))

    pdf_doc.close()
    return pages_text


def get_pdf_page_count(file_path: str) -> int:
    """Returns the total number of pages in a PDF file."""
    with fitz.open(file_path) as doc:
        return len(doc)


def extract_document_pages(
    file_path: str,
    extension: str,
    ocr_lang: str = "eng",
    start_page: int = 1,
    end_page: int | None = None,
    trim_headers_footers: bool = True,
) -> List[tuple[int, str]]:
    """Main router returning (page_number, text) tuples."""
    if extension == "pdf":
        return extract_from_pdf(
            file_path,
            ocr_lang=ocr_lang,
            start_page=start_page,
            end_page=end_page,
            trim_headers_footers=trim_headers_footers,
        )
    elif extension == "docx":
        return extract_from_docx(file_path, ocr_lang=ocr_lang)
    elif extension == "txt":
        return extract_from_txt(file_path)
    elif extension in {"png", "jpg", "jpeg", "webp"}:
        return extract_from_image(file_path, ocr_lang=ocr_lang)
    else:
        raise ValueError(f"Unsupported file format: .{extension}")
