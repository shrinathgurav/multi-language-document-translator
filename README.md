# 🌐 Multi-Language Document Translator

A free, easy-to-use web application that translates documents and images into your chosen language—without needing any paid cloud subscriptions or API keys.

Whether you have a multi-page PDF, a Word document, a plain text file, or a photo/scan of a printed page, this app reads the text (including text inside images), translates it cleanly sentence-by-sentence, shows you a live side-by-side preview, and lets you download the final result as a **TXT**, **DOCX**, or **PDF** file.

---

## ✨ Key Features

* **🌍 Multi-Language Support (14+ Languages + Auto-Detect)**
  * Translate between **English, Hindi, Marathi, Spanish, French, German, Arabic, Chinese, Japanese, Russian, Portuguese, Bengali, Tamil, and Telugu**.
  * Don't know the document's language? Select **Auto-Detect** and the app will figure it out automatically.

* **📂 Supports Multiple File Formats**
  * **PDFs (`.pdf`):** Handles normal selectable text PDFs, scanned image-only PDFs, and mixed PDFs containing both text and embedded diagrams/images.
  * **Word Documents (`.docx`):** Extracts paragraphs, tables, and even text hidden inside embedded images.
  * **Plain Text (`.txt`):** Reads standard UTF-8 text files directly.
  * **Images (`.png`, `.jpg`, `.jpeg`, `.webp`):** Uses built-in Optical Character Recognition (OCR) to read text directly off photos and screenshots.

* **📑 Smart PDF Page-Range Selection**
  * Working with a 100-page PDF? Pick the exact **Start Page** and **End Page** (for example, pages `3` to `7`) so you only translate the pages you need—saving time and avoiding network limits.

* **✂️ Intelligent Sentence-Aware Splitting & Page Packing**
  * Free translation websites limit requests to **5,000 characters** at a time.
  * The app packs consecutive short pages up to **4,800 characters** to minimize requests, and splits long pages at the **last complete sentence** before the limit (supporting English punctuation like `. ! ?` as well as Indian script endings like `।` and `॥`).

* **⚡ Live Streaming & Side-by-Side Comparison View**
  * Watch your translation appear **chunk-by-chunk in real time** as soon as each section finishes—no waiting in the dark for a huge file to complete.
  * Toggle **Side-by-Side Comparison View** in the sidebar to inspect the **Original Source Text** right next to the **Translated Text** so you can verify accuracy immediately.

* **⏹️ Stop Anytime & Partial-Progress Recovery**
  * Need to halt a large translation midway? Click **Stop Translation** at any time—the app cleanly stops after the current chunk, keeps all completed pages on screen, and lets you download everything translated up to that point.
  * Even if your internet drops mid-document, completed pages are automatically preserved for download.

* **🛡️ Built-In Rate-Limit Protection & Multi-Engine Fallback**
  * Automatically spaces out requests, takes periodic breathers on large files, caches already-translated sections, and switches seamlessly across **three free translation engines** (Google Translate Primary → Google Public GTX Endpoint → MyMemory Free API) if one engine temporarily slows down or blocks requests.
  * Includes an optional **Batch Mode** toggle in the sidebar for translating chunks in small groups.

* **💾 Multi-Format Download with Script-Accurate PDF Fonts**
  * Save your completed translation as **TXT**, **DOCX (Word)**, or **PDF**.
  * Automatically applies script-specific **Google Noto Sans** fonts and text shaping so complex scripts like **Devanagari (Hindi/Marathi)**, **Arabic**, **Bengali**, **Tamil**, and **Telugu** render clearly without broken boxes (`□□□`).

---

## 🗂️ Project Structure

```text
my-translator/
│
├── app.py                      # Main Streamlit web interface (UI, live preview, stop/resume, downloads)
├── config.py                   # App settings, character limits, language codes, and font paths
├── pyproject.toml              # Project dependencies managed by uv
│
├── core/                       # Core processing modules
│   ├── __init__.py
│   ├── extractor.py            # Reads text from PDF, DOCX, TXT, and images (via OCR)
│   ├── chunker.py              # Packs pages & splits cleanly at sentence endings under 4,800 chars
│   ├── translator.py           # Multi-engine free translator with rate-limit fallback & caching
│   └── exporter.py             # Generates downloadable TXT, DOCX, and Unicode PDF files
│
├── utils/                      # Helper utilities
│   ├── __init__.py
│   └── file_helpers.py         # Safe temporary file creation and cleanup
│
└── assets/                     # Unicode fonts for non-Latin PDF exports
    ├── NotoSans-Regular.ttf
    ├── NotoSansDevanagari-Regular.ttf
    ├── NotoSansArabic-Regular.ttf
    ├── NotoSansBengali-Regular.ttf
    ├── NotoSansTamil-Regular.ttf
    └── NotoSansTelugu-Regular.ttf
```

---

## 🛠️ Prerequisites (One-Time Setup)

Before running the app, make sure you have these three items ready on your computer:

1. **Python 3.10+** and **[`uv`](https://docs.astral.sh/uv/)** (fast Python package manager).
2. **Tesseract OCR Engine** *(required only if you want to extract text from images or scanned PDFs)*:
   * **Windows:** Download and install from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki). During setup, check **"Additional language data"** for languages like Hindi (`hin`) or Marathi (`mar`), and add `C:\Program Files\Tesseract-OCR` to your System `PATH`.
   * **Linux (Ubuntu/Debian):**
     ```bash
     sudo apt update && sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar
     ```
   * **macOS:**
     ```bash
     brew install tesseract tesseract-lang
     ```
3. **Google Noto Fonts (for PDF Export):**
   * Download the regular `.ttf` fonts from [Google Fonts (Noto)](https://fonts.google.com/noto) and place them inside the `assets/` folder so non-English PDF downloads display every character properly.

---

## 🚀 Installation & Running the App

1. **Navigate into your project folder:**
   ```bash
   cd my-translator
   ```

2. **Install all required Python packages with `uv`:**
   ```bash
   uv add streamlit deep-translator PyMuPDF python-docx pytesseract Pillow fpdf2 uharfbuzz requests
   ```

3. **Start the web application:**
   ```bash
   uv run streamlit run app.py
   ```

4. **Open your browser:**
   * The app will automatically open at **`http://localhost:8501`**.

---

## 📖 Step-by-Step Usage Examples

### Example 1: Translating Specific Pages of a Large English PDF into Marathi
1. Open the left **Sidebar** (click `>` in the top-left corner if it is collapsed).
2. Set **Source Language** to `English` (or `Auto-Detect`) and **Target Language** to `Marathi`.
3. Choose **Download Format** as `PDF` or `DOCX`.
4. Upload your PDF in the main window. The app will display the total page count.
5. Set **Start Page** to `1` and **End Page** to `5`.
6. Click **Start Translation**. Watch the side-by-side preview populate live, click **Stop Translation** anytime if you only need the first few sections, and click **Download** to save your file.

### Example 2: Extracting and Translating Text from a Photo or Scanned Document
1. In the sidebar, set **Source Language** to the language printed in the image (e.g., `Hindi`) so the OCR engine loads the matching script dictionary.
2. Set **Target Language** to `English`.
3. Upload a `.jpg`, `.png`, or scanned `.pdf` file.
4. Click **Start Translation**—the app automatically scans the image at 300 DPI, extracts the text, translates it, and lets you download the clean text file.

---

## ❓ Troubleshooting

* **Sidebar is hidden:** Click the small **`>`** arrow in the top-left corner of the browser window to expand the settings sidebar.
* **Scanned image text is inaccurate:** Select the exact **Source Language** instead of `Auto-Detect` so Tesseract OCR uses the right script model, and ensure that language's `.traineddata` pack is installed.
* **Boxes (`□□□`) appear in downloaded PDFs:** Verify that the matching Noto font file (e.g., `NotoSansDevanagari-Regular.ttf` for Hindi/Marathi) is saved inside the `assets/` folder and `uharfbuzz` is installed.
* **Rate-limit warnings on huge files:** Use the **Start Page / End Page** selector to translate documents in smaller ranges (e.g., 15–20 pages at a time) so free translation endpoints remain fast and responsive.
