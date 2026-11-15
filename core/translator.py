import random
import time
from deep_translator import GoogleTranslator


class DocumentTranslator:
    """Wrapper around the free Google Translate web endpoint with smart rate-limit handling."""

    def __init__(self, source_lang: str = "auto", target_lang: str = "en"):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)
        self._cache = {}

    def translate_chunk(self, text: str, retries: int = 5, base_delay: float = 5.0) -> str:
        """
        Translates a single text chunk (<= 5000 chars) using randomized pacing,
        in-memory caching, and exponential backoff on rate-limit errors.
        """
        cleaned = text.strip()
        if not cleaned:
            return ""

        # Return cached result immediately if this exact chunk was already translated
        cache_key = (self.source_lang, self.target_lang, cleaned)
        if cache_key in self._cache:
            return self._cache[cache_key]

        last_error = None
        for attempt in range(retries):
            try:
                # Re-instantiate occasionally on retries to refresh the underlying HTTP session
                if attempt > 0:
                    self.translator = GoogleTranslator(
                        source=self.source_lang, target=self.target_lang
                    )

                translated = self.translator.translate(cleaned)
                result = translated if translated else ""
                self._cache[cache_key] = result

                # Polite randomized delay (1.5s to 3.0s) to stay well under Google's rate threshold
                time.sleep(random.uniform(1.5, 3.0))
                return result

            except Exception as exc:
                last_error = exc
                error_msg = str(exc).lower()

                # Longer cooldown if Google explicitly blocks due to too many requests
                if "too many requests" in error_msg or "429" in error_msg:
                    wait_time = base_delay * (2 ** attempt) + random.uniform(1.0, 4.0)
                else:
                    wait_time = 2.0 * (attempt + 1)

                time.sleep(wait_time)

        raise RuntimeError(f"Translation failed after {retries} attempts: {last_error}")