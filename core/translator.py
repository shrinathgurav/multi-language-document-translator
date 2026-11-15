import base64
import random
import re
import time
from typing import List
from urllib.parse import quote
import requests


TECH_TERMS_PATTERN = re.compile(
    r"\b(Python|Pandas|NLTK|SQL|PL/SQL|Oracle|Oracle XE|DataFrame|DataFrames|"
    r"Primary Key|Foreign Key|Schema|Table|Tables|Database|Record|Attribute|"
    r"Normalization|1NF|2NF|3NF|ER model|API|CSV|PDF|DOCX|TXT|OCR|NLP|"
    r"Tokenizer|Tokenizing|Stemming|Lemmatization|Stopwords|n-grams|"
    r"VARCHAR2|NUMBER|DATE|SYSDATE|IDENTITY|NOT NULL|DEFAULT|CREATE TABLE|"
    r"SELECT|INSERT|UPDATE|DELETE|JOIN|INDEX|TRIGGER|PROCEDURE|FUNCTION)\b"
)


class DocumentTranslator:
    """
    Fast, resilient free translator with Natural Everyday Tone support
    (preserves technical English terms cleanly inside Marathi/Indic sentences).
    """

    CLIENTS5_URL = base64.b64decode(
        "aHR0cHM6Ly9jbGllbnRzNS5nb29nbGUuY29tL3RyYW5zbGF0ZV9hL3Q="
    ).decode()

    GTX_URL = base64.b64decode(
        "aHR0cHM6Ly90cmFuc2xhdGUuZ29vZ2xlYXBpcy5jb20vdHJhbnNsYXRlX2Evc2luZ2xl"
    ).decode()

    LINGVA_MIRRORS = [
        "https://lingva.ml",
        "https://plausibility.cloud",
    ]

    def __init__(
        self,
        source_lang: str = "auto",
        target_lang: str = "en",
        natural_tone: bool = True,
    ):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.natural_tone = natural_tone
        self._cache = {}
        self._engine = "clients5"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })

    @staticmethod
    def _protect_terms(text: str) -> tuple[str, dict]:
        """Replaces technical terms with numeric markers so Google keeps them in English."""
        placeholders = {}

        def _repl(match):
            token = f"[[{len(placeholders)}]]"
            placeholders[token] = match.group(0)
            return token

        return TECH_TERMS_PATTERN.sub(_repl, text), placeholders

    @staticmethod
    def _restore_terms(text: str, placeholders: dict) -> str:
        """Restores original English technical terms cleanly into the translated output."""
        for token, original in placeholders.items():
            # Handle cases where translation engines add spaces around brackets like [[ 0 ]]
            idx = token.strip("[]")
            text = re.sub(rf"\[\s*\[\s*{idx}\s*\]\s*\]", original, text)
        return text

    def _translate_via_clients5(self, text: str) -> str:
        """Primary: Google Chrome built-in translator POST endpoint."""
        params = {
            "client": "dict-chrome-ex",
            "sl": self.source_lang,
            "tl": self.target_lang,
        }
        response = self.session.post(
            self.CLIENTS5_URL,
            params=params,
            data={"q": text},
            timeout=12,
        )
        if response.status_code == 429:
            raise RuntimeError("HTTP_429_BLOCKED")
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            parts = []
            for item in data:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, list) and item and isinstance(item[0], str):
                    parts.append(item[0])
            return "".join(parts).strip()
        return str(data).strip()

    def _translate_via_gtx(self, text: str) -> str:
        """Fallback 1: Google public GTX POST endpoint."""
        params = {
            "client": "gtx",
            "sl": self.source_lang,
            "tl": self.target_lang,
            "dt": "t",
        }
        response = self.session.post(
            self.GTX_URL,
            params=params,
            data={"q": text},
            timeout=12,
        )
        if response.status_code == 429:
            raise RuntimeError("HTTP_429_BLOCKED")
        response.raise_for_status()
        data = response.json()

        parts = [seg[0] for seg in data[0] if seg and seg[0]]
        return "".join(parts).strip()

    def _translate_via_lingva(self, text: str) -> str:
        """Fallback 2: Public Lingva Translate proxy mirrors in URL-safe sub-chunks."""
        sub_chunks = []
        current = ""
        for word in text.split(" "):
            if len(current) + len(word) + 1 <= 850:
                current = f"{current} {word}".strip()
            else:
                if current:
                    sub_chunks.append(current)
                current = word[:850]
        if current:
            sub_chunks.append(current)

        last_err = None
        for base_url in self.LINGVA_MIRRORS:
            try:
                translated_parts = []
                for sub in sub_chunks:
                    encoded = quote(sub, safe="")
                    url = f"{base_url}/{self.source_lang}/{self.target_lang}/{encoded}"
                    resp = self.session.get(url, timeout=15)
                    resp.raise_for_status()
                    payload = resp.json()
                    if "translation" in payload:
                        translated_parts.append(payload["translation"].strip())
                    time.sleep(0.4)
                return " ".join(translated_parts).strip()
            except Exception as exc:
                last_err = exc
                continue

        raise RuntimeError(f"All fallback mirrors failed: {last_err}")

    def translate_chunk(self, text: str, retries: int = 3) -> str:
        """Translates a chunk with optional natural-tone technical term preservation."""
        cleaned = text.strip()
        if not cleaned:
            return ""

        cache_key = (self.source_lang, self.target_lang, self.natural_tone, cleaned)
        if cache_key in self._cache:
            return self._cache[cache_key]

        prepared_text = cleaned
        placeholders = {}
        if self.natural_tone and self.target_lang != "en":
            prepared_text, placeholders = self._protect_terms(cleaned)

        last_error = None
        for attempt in range(retries):
            try:
                if self._engine == "clients5":
                    raw_translated = self._translate_via_clients5(prepared_text)
                elif self._engine == "gtx":
                    raw_translated = self._translate_via_gtx(prepared_text)
                else:
                    raw_translated = self._translate_via_lingva(prepared_text)

                result = (
                    self._restore_terms(raw_translated, placeholders)
                    if placeholders
                    else raw_translated
                )
                self._cache[cache_key] = result
                time.sleep(random.uniform(0.6, 1.2))
                return result

            except Exception as exc:
                last_error = exc
                if "HTTP_429_BLOCKED" in str(exc) or "429" in str(exc):
                    if self._engine == "clients5":
                        self._engine = "gtx"
                        continue
                    elif self._engine == "gtx":
                        self._engine = "lingva"
                        continue
                time.sleep(0.8 * (attempt + 1))

        raise RuntimeError(f"Translation failed after {retries} attempts: {last_error}")

    def translate_batch_chunks(self, texts: List[str], retries: int = 3) -> List[str]:
        """Translates a list of chunks sequentially using the active fast engine."""
        return [self.translate_chunk(t, retries=retries) for t in texts]
