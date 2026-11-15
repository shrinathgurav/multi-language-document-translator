import re
from typing import List
from config import MAX_CHAR_LIMIT

SENTENCE_END_PATTERN = re.compile(r'(?<=[.!?।॥。！？])\s+')


def _split_into_sentences(text: str) -> List[str]:
    """Splits text into sentences across Latin and non-Latin punctuation."""
    sentences = SENTENCE_END_PATTERN.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


def chunk_page_text(page_text: str, max_chars: int = MAX_CHAR_LIMIT) -> List[str]:
    """Splits a single text block into chunks <= max_chars at sentence boundaries."""
    cleaned_text = page_text.strip()
    if not cleaned_text:
        return []
    if len(cleaned_text) <= max_chars:
        return [cleaned_text]

    sentences = _split_into_sentences(cleaned_text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            words = sentence.split(" ")
            temp_part = ""
            for word in words:
                if len(temp_part) + len(word) + 1 <= max_chars:
                    temp_part = f"{temp_part} {word}".strip()
                else:
                    if temp_part:
                        chunks.append(temp_part)
                    temp_part = word[:max_chars]
            if temp_part:
                current_chunk = temp_part
            continue

        candidate = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
        if len(candidate) <= max_chars:
            current_chunk = candidate
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def chunk_document_pages(
    pages: List[tuple[int, str]], max_chars: int = MAX_CHAR_LIMIT
) -> List[dict]:
    """
    Combines consecutive pages into full sentence-aligned chunks up to max_chars
    to minimize total API requests on large documents while tracking page ranges.
    """
    all_chunks = []
    buffer_text = ""
    start_page = None
    end_page = None
    chunk_counter = 1

    for page_num, page_text in pages:
        cleaned = page_text.strip()
        if not cleaned:
            continue

        if len(cleaned) > max_chars:
            if buffer_text:
                label = f"{start_page}" if start_page == end_page else f"{start_page}-{end_page}"
                all_chunks.append({
                    "page_num": label,
                    "chunk_num": chunk_counter,
                    "text": buffer_text.strip(),
                })
                chunk_counter += 1
                buffer_text = ""
                start_page = None
                end_page = None

            for sub_chunk in chunk_page_text(cleaned, max_chars=max_chars):
                all_chunks.append({
                    "page_num": str(page_num),
                    "chunk_num": chunk_counter,
                    "text": sub_chunk,
                })
                chunk_counter += 1
            continue

        separator = "\n\n" if buffer_text else ""
        candidate = f"{buffer_text}{separator}{cleaned}"

        if len(candidate) <= max_chars:
            if start_page is None:
                start_page = page_num
            end_page = page_num
            buffer_text = candidate
        else:
            label = f"{start_page}" if start_page == end_page else f"{start_page}-{end_page}"
            all_chunks.append({
                "page_num": label,
                "chunk_num": chunk_counter,
                "text": buffer_text.strip(),
            })
            chunk_counter += 1
            start_page = page_num
            end_page = page_num
            buffer_text = cleaned

    if buffer_text:
        label = f"{start_page}" if start_page == end_page else f"{start_page}-{end_page}"
        all_chunks.append({
            "page_num": label,
            "chunk_num": chunk_counter,
            "text": buffer_text.strip(),
        })

    return all_chunks
