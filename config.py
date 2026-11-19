# Safe character limit per chunk (prevents Google spam triggers and URL-length errors)
MAX_CHAR_LIMIT = 1800

# Supported upload file extensions
SUPPORTED_EXTENSIONS = ["pdf", "docx", "txt", "png", "jpg", "jpeg", "webp"]

# Supported export formats
EXPORT_FORMATS = ["TXT", "DOCX", "PDF"]

# Language mapping: Display Name -> (Google Translate Code, Tesseract OCR Code)
LANGUAGES = {
    "Auto-Detect": ("auto", "eng"),
    "English": ("en", "eng"),
    "Hindi": ("hi", "hin"),
    "Marathi": ("mr", "mar"),
    "Spanish": ("es", "spa"),
    "French": ("fr", "fra"),
    "German": ("de", "deu"),
    "Arabic": ("ar", "ara"),
    "Chinese (Simplified)": ("zh-CN", "chi_sim"),
    "Japanese": ("ja", "jpn"),
    "Russian": ("ru", "rus"),
    "Portuguese": ("pt", "por"),
    "Bengali": ("bn", "ben"),
    "Tamil": ("ta", "tam"),
    "Telugu": ("te", "tel"),
}

# Maps Google Translate target language codes to script-specific Unicode fonts
DEFAULT_FONT_PATH = "assets/NotoSans-Regular.ttf"

TARGET_FONTS = {
    "hi": ("NotoSansDevanagari", "assets/NotoSansDevanagari-Regular.ttf"),
    "mr": ("NotoSansDevanagari", "assets/NotoSansDevanagari-Regular.ttf"),
    "ar": ("NotoSansArabic", "assets/NotoSansArabic-Regular.ttf"),
    "bn": ("NotoSansBengali", "assets/NotoSansBengali-Regular.ttf"),
    "ta": ("NotoSansTamil", "assets/NotoSansTamil-Regular.ttf"),
    "te": ("NotoSansTelugu", "assets/NotoSansTelugu-Regular.ttf"),
}
