from pathlib import Path
import streamlit as st

from config import SUPPORTED_EXTENSIONS, EXPORT_FORMATS, LANGUAGES
from utils.file_helpers import save_uploaded_file_temp, cleanup_temp_file, get_file_extension
from core.extractor import extract_document_pages, get_pdf_page_count
from core.chunker import chunk_document_pages
from core.translator import DocumentTranslator
from core.exporter import generate_export_file


def _render_chunk_pair(
    container,
    page_num: str,
    chunk_num: int,
    source_text: str,
    translated_text: str,
    side_by_side: bool,
) -> None:
    """Renders a single chunk either side-by-side or translated-only inside the container."""
    with container:
        st.markdown(f"**[Page {page_num} • Part {chunk_num}]**")
        if side_by_side:
            col_src, col_tgt = st.columns(2)
            with col_src:
                st.caption("Source Text")
                st.info(source_text)
            with col_tgt:
                st.caption("Translated Text")
                st.success(translated_text)
        else:
            st.write(translated_text)
        st.divider()


def _rebuild_output_from_items(items: list) -> str:
    """Builds the formatted download text from all completed comparison items."""
    accumulated = {}
    for page_label, _, _, trans_text in items:
        accumulated.setdefault(str(page_label), []).append(trans_text)

    sections = []
    for page_label, parts in accumulated.items():
        sections.append(f"--- Page {page_label} ---\n{' '.join(parts)}")
    return "\n\n".join(sections)


def _request_stop() -> None:
    """Callback triggered when the Stop Translation button is clicked."""
    st.session_state.stop_requested = True
    st.session_state.stage = "idle"


st.set_page_config(
    page_title="Multi-Language Document Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌐 Multi-Language Document Translator")
st.caption("Supports PDF (including scanned & embedded images), DOCX, TXT, and Image files.")

# Initialize session state variables cleanly
defaults = {
    "stage": "idle",  # idle -> extracting -> translating
    "translated_output": "",
    "source_filename": "",
    "comparison_items": [],
    "pending_chunks": [],
    "extracted_page_count": 0,
    "current_chunk_idx": 0,
    "stop_requested": False,
    "translator_instance": None,
    "last_error": "",
    "job_params": {},
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

is_busy = st.session_state.stage in {"extracting", "translating"}

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

    st.divider()
    st.subheader("Display & Processing")

    side_by_side = st.checkbox(
        "Side-by-Side Comparison View",
        value=True,
        help="Displays original source text next to the translated output.",
    )
    

    use_batch_mode = st.checkbox(
        "Use Batch Mode (translate_batch)",
        value=False,
        help="Translates chunks in mini-batches instead of one-by-one.",
    )
    
    natural_tone = st.checkbox(
        "Natural Everyday Tone (Keep Technical Terms)",
        value=True,
        help="Keeps programming/technical English terms (like Python, SQL, Primary Key) intact so Marathi/Hindi translations read naturally instead of literal word-by-word.",
    )
    
    batch_size = 3
    if use_batch_mode:
        batch_size = st.slider("Chunks per batch", min_value=2, max_value=5, value=3)

# --- File Upload ---
uploaded_file = st.file_uploader(
    "Upload a document or image",
    type=SUPPORTED_EXTENSIONS,
)

if uploaded_file is not None:
    ext = get_file_extension(uploaded_file.name)
    start_page = 1
    end_page = None

    if ext == "pdf":
        preview_temp_path = save_uploaded_file_temp(uploaded_file)
        try:
            total_pdf_pages = get_pdf_page_count(preview_temp_path)
        finally:
            cleanup_temp_file(preview_temp_path)

        st.info(
            f"**Loaded PDF:** `{uploaded_file.name}` • **{total_pdf_pages} total page(s)** ({uploaded_file.size / 1024:.1f} KB)"
        )

        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input(
                "Start Page",
                min_value=1,
                max_value=total_pdf_pages,
                value=1,
                step=1,
            )
        with col2:
            end_page = st.number_input(
                "End Page",
                min_value=int(start_page),
                max_value=total_pdf_pages,
                value=total_pdf_pages,
                step=1,
            )
    else:
        st.info(f"**Loaded File:** `{uploaded_file.name}` ({uploaded_file.size / 1024:.1f} KB)")

    # --- Action Buttons ---
    btn_col1, btn_col2, _ = st.columns([1.4, 1.4, 4])
    with btn_col1:
        start_clicked = st.button(
            "Start Translation",
            type="primary",
            disabled=is_busy,
        )
    with btn_col2:
        st.button(
            "⏹ Stop Translation",
            type="secondary",
            on_click=_request_stop,
            disabled=not is_busy,
        )

    if start_clicked:
        st.session_state.translated_output = ""
        st.session_state.comparison_items = []
        st.session_state.pending_chunks = []
        st.session_state.extracted_page_count = 0
        st.session_state.current_chunk_idx = 0
        st.session_state.stop_requested = False
        st.session_state.last_error = ""
        st.session_state.source_filename = Path(uploaded_file.name).stem
        st.session_state.job_params = {
            "ext": ext,
            "src_label": source_label,
            "tgt_label": target_label,
            "start_page": int(start_page),
            "end_page": int(end_page) if end_page else None,
        }
        st.session_state.stage = "extracting"
        st.rerun()

# --- Stage 1: Extract & Chunk Document (runs independently of file_uploader widget state) ---
if st.session_state.stage == "extracting":
    if uploaded_file is None:
        st.session_state.last_error = "Uploaded file was lost before extraction. Please re-upload."
        st.session_state.stage = "idle"
        st.rerun()

    params = st.session_state.job_params
    src_google_code, src_ocr_code = LANGUAGES[params["src_label"]]
    tgt_google_code, _ = LANGUAGES[params["tgt_label"]]

    temp_path = None
    try:
        with st.spinner("Extracting text and running OCR on images..."):
            temp_path = save_uploaded_file_temp(uploaded_file)
            pages = extract_document_pages(
                temp_path,
                params["ext"],
                ocr_lang=src_ocr_code,
                start_page=params["start_page"],
                end_page=params["end_page"],
            )

        if not pages:
            st.session_state.last_error = "No readable text could be extracted from the selected page(s)."
            st.session_state.stage = "idle"
            st.rerun()
        else:
            chunks = chunk_document_pages(pages)
            st.session_state.extracted_page_count = len(pages)
            st.session_state.pending_chunks = chunks
            st.session_state.translator_instance = DocumentTranslator(
                source_lang=src_google_code,
                target_lang=tgt_google_code,
            )
            st.session_state.stage = "translating"
            st.rerun()
    except Exception as e:
        st.session_state.last_error = f"Extraction failed: {e}"
        st.session_state.stage = "idle"
        st.rerun()
    finally:
        cleanup_temp_file(temp_path)

# --- Stage 2: Translate One Chunk/Batch Per Pass & Paint Live UI Immediately ---
if st.session_state.stage == "translating" and not st.session_state.stop_requested:
    chunks = st.session_state.pending_chunks
    total_chunks = len(chunks)
    idx = st.session_state.current_chunk_idx
    translator = st.session_state.translator_instance

    st.success(
        f"Extracted {st.session_state.extracted_page_count} page(s) split into {total_chunks} sentence-aligned chunk(s)."
    )

    active_page = chunks[idx]["page_num"] if idx < total_chunks else ""
    st.progress(
        idx / total_chunks if total_chunks else 0,
        text=f"Translating chunk {min(idx + 1, total_chunks)} of {total_chunks} (Page {active_page})...",
    )

    st.subheader("Live Translated Output")
    live_container = st.container(border=True)
    for p_num, c_num, s_txt, t_txt in st.session_state.comparison_items:
        _render_chunk_pair(live_container, str(p_num), c_num, s_txt, t_txt, side_by_side)

    try:
        if use_batch_mode:
            batch_items = chunks[idx : idx + batch_size]
            batch_texts = [item["text"] for item in batch_items]
            translated_texts = translator.translate_batch_chunks(batch_texts)

            for item, trans_text in zip(batch_items, translated_texts):
                st.session_state.comparison_items.append(
                    (str(item["page_num"]), item["chunk_num"], item["text"], trans_text)
                )
            st.session_state.current_chunk_idx += len(batch_items)
        else:
            chunk_info = chunks[idx]
            translated_chunk = translator.translate_chunk(chunk_info["text"])
            st.session_state.comparison_items.append(
                (
                    str(chunk_info["page_num"]),
                    chunk_info["chunk_num"],
                    chunk_info["text"],
                    translated_chunk,
                )
            )
            st.session_state.current_chunk_idx += 1

        st.session_state.translated_output = _rebuild_output_from_items(
            st.session_state.comparison_items
        )

        if st.session_state.current_chunk_idx < total_chunks and not st.session_state.stop_requested:
            st.rerun()
        else:
            st.session_state.stage = "idle"
            st.rerun()

    except Exception as e:
        st.session_state.last_error = str(e)
        st.session_state.stage = "idle"
        st.rerun()

# --- Stage 3: Persistent Completed / Stopped / Error View ---
if st.session_state.stage == "idle":
    if st.session_state.last_error:
        st.error(f"An error occurred during processing: {st.session_state.last_error}")
        if st.session_state.translated_output:
            st.warning("Partial translation progress was saved! You can download the completed pages below.")
    elif st.session_state.stop_requested:
        st.warning("⏹ Translation stopped by user. Any pages completed before stopping are preserved below.")
    elif st.session_state.comparison_items:
        st.success(
            f"Extracted {st.session_state.extracted_page_count} page(s) split into {len(st.session_state.pending_chunks)} sentence-aligned chunk(s)."
        )
        st.progress(1.0, text="Translation complete!")

    if st.session_state.comparison_items:
        st.subheader("Live Translated Output")
        saved_container = st.container(border=True)
        for page_num, chunk_num, src_text, trans_text in st.session_state.comparison_items:
            _render_chunk_pair(
                saved_container,
                str(page_num),
                chunk_num,
                src_text,
                trans_text,
                side_by_side,
            )

# --- Download Section ---
if st.session_state.translated_output and st.session_state.stage == "idle":
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
