# 🛠️ Installation & Setup Guide — Multi-Language Document Translator

This guide walks you through setting up the **Multi-Language Document Translator** on your computer from scratch, including **Python**, the **`uv` package manager**, **Tesseract OCR** (for reading scanned PDFs and images), and **Unicode fonts** (for exporting multi-language PDFs).

---

## 📋 1. System Prerequisites

Before starting, ensure your computer meets these basic requirements:
* **Operating System:** Windows 10/11, macOS, or Linux (Ubuntu/Debian)
* **Python:** Version **3.10 or higher**
* **Internet Connection:** Required to install packages and connect to free translation endpoints

---

## ⚡ 2. Install the `uv` Package Manager

This project uses **`uv`** for fast dependency management and virtual environments.

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh | iex"
```

### macOS / Linux
```bash
curl -LsSf https://astral.sh | sh
```

*(Restart your terminal after installation and verify by running `uv --version`.)*

---

## 🔍 3. Install Tesseract OCR (Required for Images & Scanned PDFs)

Tesseract is the free Optical Character Recognition (OCR) engine that reads text inside photos, screenshots, and scanned PDF pages.

### A. Windows Installation
1. **Download the Installer:**
   * Visit the official [UB-Mannheim Tesseract Wiki](https://github.com) and download the latest 64-bit Windows installer (e.g., `tesseract-ocr-w64-setup-5.4.0.20240606.exe`).
2. **Select Additional Languages During Setup:**
   * Run the installer. When you reach the **Choose Components** screen, expand **"Additional language data (download)"**.
   * Check the boxes for any languages you plan to extract from images (for example, **Hindi** `hin` and **Marathi** `mar`). English (`eng`) is included by default.
   * Keep the default destination folder: `C:\Program Files\Tesseract-OCR`.
3. **Add Tesseract to System `PATH`:**
   * Press the **Windows Key**, type **`Environment Variables`**, and click **Edit the system environment variables**.
   * Click **Environment Variables...** at the bottom.
   * Under **System variables**, select **`Path`** and click **Edit...**
   * Click **New** and paste:
     ```text
     C:\Program Files\Tesseract-OCR
     ```
   * Click **OK** on all windows to save.
4. **Refresh `PATH` & Verify in PowerShell:**
   * Open a **new PowerShell window** (or close and reopen VS Code) and run:
     ```powershell
     tesseract --version
     ```
   * *(Tip: If you don't want to close your current PowerShell session, run this command to reload `PATH` immediately:)*
     ```powershell
     \$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
     tesseract --version
     ```
   * Check installed language packs anytime with:
     ```powershell
     tesseract --list-langs
     ```

### B. Linux (Ubuntu / Debian)
Install Tesseract and the required language packs directly via `apt`:
```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar tesseract-ocr-ara tesseract-ocr-spa tesseract-ocr-fra
tesseract --version
```

### C. macOS (Homebrew)
Install Tesseract along with all extra language packs using Homebrew:
```bash
brew install tesseract tesseract-lang
tesseract --version
```

---

## 🔤 4. Set Up Unicode Fonts (For Multi-Language PDF Downloads)

Standard PDF fonts cannot display non-Latin scripts like Devanagari (Hindi/Marathi) or Arabic. To avoid blank boxes (`□□□`) in exported PDFs:

1. Create an `assets` folder inside your project directory (`my-translator/assets/`).
2. Download the regular `.ttf` fonts from [Google Fonts (Noto)](https://google.com) and save them inside `assets/`:
   * `NotoSans-Regular.ttf` *(English, Spanish, French, German, Russian)*
   * `NotoSansDevanagari-Regular.ttf` *(Hindi, Marathi)*
   * `NotoSansArabic-Regular.ttf` *(Arabic)*
   * `NotoSansBengali-Regular.ttf` *(Bengali)*
   * `NotoSansTamil-Regular.ttf` *(Tamil)*
   * `NotoSansTelugu-Regular.ttf` *(Telugu)*

---

## 📦 5. Install Project Dependencies & Launch

1. **Open your terminal inside the project folder:**
   ```powershell
   cd D:\Learnings\python\my-translator
   ```

2. **Initialize `uv` (if starting from scratch) and install all libraries:**
   ```powershell
   uv add streamlit deep-translator PyMuPDF python-docx pytesseract Pillow fpdf2 uharfbuzz requests
   ```

3. **Verify that all core modules import cleanly:**
   ```powershell
   uv run python -c "from core.extractor import extract_document_pages, get_pdf_page_count; from core.chunker import chunk_document_pages; from core.translator import DocumentTranslator; from core.exporter import generate_export_file; print('ALL MODULES READY')"
   ```

4. **Start the Streamlit Web Application:**
   ```powershell
   uv run streamlit run app.py
   ```

5. **Open in Browser:**
   * Navigate to **`http://localhost:8501`** if it does not open automatically.

---

## 🩺 Quick Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **`tesseract is not recognized`** | Restart your terminal or VS Code so Windows loads the updated `PATH`, or run the `$env:Path` refresh snippet in Section 3A. |
| **Missing OCR language error** | Re-run the Tesseract installer on Windows and check the missing language under *Additional language data*, or run `sudo apt install tesseract-ocr-<lang>` on Linux. |
| **Boxes (`□□□`) in downloaded PDF** | Ensure the matching `NotoSans*.ttf` font file is saved in `assets/` and `uharfbuzz` is installed via `uv add uharfbuzz`. |
