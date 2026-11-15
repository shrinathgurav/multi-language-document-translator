from pathlib import Path
import streamlit as st

from config import SUPPORTED_EXTENSIONS, EXPORT_FORMATS, LANGUAGES
from utils.file_helpers import save_uploaded_file_temp, cleanup_temp_file, get_file_extension
from core.extractor import extract_document_pages
from core.chunker import chunk_document_pages
from core.translator import DocumentTranslator
from core.exporter import generate_export_file


st.set_page_config(page_title="Multi-Language Document Translator", page_icon="🌐", layout="wide")

st.title("🌐 Multi-Language Document Translator")
st.caption("Supports PDF (including scanned & embedded images), DOCX, TXT, and Image files.")

# Initialize session state to preserve translated output across UI interactions
if "translated_output" not in st.session_state:
    st.session_state.translated_output = ""
if "source_filename" not in st.session_state:
    st.session_state.source_filename = ""

# --- Sidebar Settings ---
with st.sidebar:
    st.header("Translation Settings")

    source_label = st.selectbox(
        "Source Language (Document / OCR)",
        options=list(LANGUAGES.keys()),
        index=0,
    )

    target_languages = [lang for lang in LANGUAGES.keys() if lang != "Auto-Detect"]
    target_label = st.selectbox(
        "Target Language",
        options=target_languages,
        index=0,
    )

    export_format = st.selectbox(
        "Download Format",
        options=EXPORT_FORMATS,
        index=0,
    )

# --- File Upload ---
uploaded_file = st.file_uploader(
    "Upload a document or image",
    type=SUPPORTED_EXTENSIONS,
)

if uploaded_file is not None:
    st.info(f"**Loaded File:** `{uploaded_file.name}` ({uploaded_file.size / 1024:.1f} KB)")

    if st.button("Start Translation", type="primary"):
        st.session_state.translated_output = ""
        st.session_state.source_filename = Path(uploaded_file.name).stem

        src_google_code, src_ocr_code = LANGUAGES[source_label]
        tgt_google_code, _ = LANGUAGES[target_label]

        temp_path = None
        try:
            with st.spinner("Extracting text and running OCR on images..."):
                temp_path = save_uploaded_file_temp(uploaded_file)
                ext = get_file_extension(uploaded_file.name)
                pages = extract_document_pages(temp_path, ext, ocr_lang=src_ocr_code)

            if not pages:
                st.warning("No readable text could be extracted from this file.")
            else:
                chunks = chunk_document_pages(pages)
                total_chunks = len(chunks)

                st.success(f"Extracted {len(pages)} page(s) split into {total_chunks} sentence-aligned chunk(s).")

                translator = DocumentTranslator(
                    source_lang=src_google_code,
                    target_lang=tgt_google_code,
                )

                progress_bar = st.progress(0, text="Starting translation...")
                st.subheader("Live Translated Output")

                # Container where each chunk is appended live as soon as it finishes translating
                output_container = st.container(border=True)
                accumulated_pages = {}

                for idx, chunk_info in enumerate(chunks, start=1):
                    page_num = chunk_info["page_num"]
                    chunk_text = chunk_info["text"]

                    translated_chunk = translator.translate_chunk(chunk_text)

                    # Append immediately to the live UI container
                    with output_container:
                        st.markdown(f"**[Page {page_num} • Part {chunk_info['chunk_num']}]**")
                        st.write(translated_chunk)

                    # Store for final export
                    accumulated_pages.setdefault(page_num, []).append(translated_chunk)

                    progress = idx / total_chunks
                    progress_bar.progress(
                        progress,
                        text=f"Translated chunk {idx} of {total_chunks} (Page {page_num})...",
                    )

                # Combine all translated pages cleanly for saving
                final_sections = []
                for p_num in sorted(accumulated_pages.keys()):
                    page_body = " ".join(accumulated_pages[p_num])
                    final_sections.append(f"--- Page {p_num} ---\n{page_body}")

                st.session_state.translated_output = "\n\n".join(final_sections)
                progress_bar.progress(1.0, text="Translation complete!")

        except Exception as e:
            st.error(f"An error occurred during processing: {e}")
        finally:
            cleanup_temp_file(temp_path)

# --- Download Section ---
if st.session_state.translated_output:
    st.divider()
    st.subheader("Save Translated Document")
    
    tgt_google_code, _ = LANGUAGES[target_label]
    
    file_bytes, file_ext, mime_type = generate_export_file(
        st.session_state.translated_output,
        export_format,
        target_lang=tgt_google_code,
    )

    output_filename = f"{st.session_state.source_filename}_translated.{file_ext}"

    st.download_button(
        label=f"Download as {export_format}",
        data=file_bytes,
        file_name=output_filename,
        mime=mime_type,
        type="primary",
    )
