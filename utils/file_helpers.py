import os
import tempfile
from pathlib import Path


def save_uploaded_file_temp(uploaded_file) -> str:
    """Saves a Streamlit UploadedFile to a temporary file and returns its path."""
    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name


def cleanup_temp_file(file_path: str) -> None:
    """Safely removes a temporary file if it exists."""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass


def get_file_extension(filename: str) -> str:
    """Returns the lowercase file extension without the leading dot."""
    return Path(filename).suffix.lower().lstrip(".")
