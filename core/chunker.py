import re
from typing import List
from config import MAX_CHAR_LIMIT

# Matches standard Latin punctuation (., !, ?) as well as Devanagari Danda (।, ॥) and CJK sentence endings
SENTENCE_END_PATTERN = re.compile(r'(?<=[.!?।॥。！？])\s+')


def _split_into_sentences(text: str) -> List[str]:
    """Splits text into sentences across Latin and non-Latin punctuation."""
    sentences = SENTENCE_END_PATTERN.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


def chunk_page_text(page_text: str, max_chars: int = MAX_CHAR_LIMIT) -> List[str]:
    """
    Splits a single page's text into chunks strictly <= max_chars.
    Splits at the last complete sentence boundary before max_chars.
    """
    cleaned_text = page_text.strip()
    if not cleaned_text:
        return []

    if len(cleaned_text) <= max_chars:
        return [cleaned_text]

    sentences = _split_into_sentences(cleaned_text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Handle edge case where a single sentence itself exceeds max_chars
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            # Hard-split oversized sentence at the last space before max_chars
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

        # Check if adding the next sentence stays within the limit
        candidate = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
        if len(candidate) <= max_chars:
            current_chunk = candidate
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def chunk_document_pages(pages: List[str], max_chars: int = MAX_CHAR_LIMIT) -> List[dict]:
    """
    Processes all extracted pages and returns a list of chunk dictionaries
    containing page metadata and sentence-aligned text chunks.
    """
    all_chunks = []
    for page_idx, page_text in enumerate(pages, start=1):
        page_chunks = chunk_page_text(page_text, max_chars=max_chars)
        for chunk_idx, chunk_text in enumerate(page_chunks, start=1):
            all_chunks.append({
                "page_num": page_idx,
                "chunk_num": chunk_idx,
                "text": chunk_text,
            })
    return all_chunks
