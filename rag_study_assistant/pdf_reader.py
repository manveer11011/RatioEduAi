"""PDF text extraction with optional OCR fallback for scanned pages."""

from pathlib import Path

# Threshold: if page text has fewer chars, treat as scanned and try OCR
_MIN_TEXT_CHARS_PER_PAGE = 50


def _ocr_page_image(pix) -> str:
    """Run EasyOCR on a PyMuPDF pixmap. Returns extracted text."""
    try:
        import easyocr
        import numpy as np
    except ImportError:
        return ""

    # Lazy init reader (heavy first-time load)
    if not hasattr(_ocr_page_image, "_reader"):
        _ocr_page_image._reader = easyocr.Reader(["en"], gpu=False, verbose=False)

    reader = _ocr_page_image._reader

    # Convert pixmap to numpy array (RGB) - PyMuPDF pix.samples is raw bytes
    samples = pix.samples
    n = pix.n
    arr = np.frombuffer(samples, dtype=np.uint8).reshape((pix.height, pix.width, n))
    if n == 4:
        arr = arr[:, :, :3]  # Drop alpha for EasyOCR

    results = reader.readtext(arr)
    return " ".join(r[1] for r in results if r[1]) if results else ""


def extract_text_from_pdf(path: Path | str, use_ocr: bool | None = None) -> str:
    """
    Extract text from a PDF file.
    Uses PyMuPDF for native text. If use_ocr is True and a page yields very little text,
    falls back to EasyOCR for that page (scanned/image pages).
    """
    import config

    path = Path(path)
    if not path.is_file() or path.suffix.lower() != ".pdf":
        return ""

    use_ocr = use_ocr if use_ocr is not None else config.use_ocr_for_pdf()

    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            return ""

    parts = []
    try:
        doc = pymupdf.open(path)
        for page in doc:
            text = page.get_text().strip()
            if use_ocr and len(text) < _MIN_TEXT_CHARS_PER_PAGE:
                # Likely scanned; render page and run OCR
                pix = page.get_pixmap(dpi=150, alpha=False)
                ocr_text = _ocr_page_image(pix)
                if ocr_text:
                    text = ocr_text
            if text:
                parts.append(text)
        doc.close()
    except Exception:
        return ""

    return "\n\n".join(parts) if parts else ""
