import io, os, re, pdfplumber 

def extract_with_fallback(buf: io.BytesIO, min_chars: int = 30) -> str:
    """
    Try to extract text with pdfplumber. If a page yields less than `min_chars`,
    fall back to OCR for that page.
    """
    buf.seek(0)
    all_text = []
    with pdfplumber.open(buf) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            if len(text.strip()) < min_chars:
                print("THIS IS AN IMAGE, RETURNING")
                return None
            all_text.append(text.strip())

    return "\n\n".join(all_text)

def save_pdf_bytes_as_txt(buf: io.BytesIO, pdf_filename: str, output_dir: str = ".") -> str:
    base = os.path.splitext(os.path.basename(pdf_filename))[0]
    txt_path = os.path.join(output_dir, f"{base}.txt")
    text = extract_with_fallback(buf, min_chars=30)
    if text is not None:
        text = clean_for_embeddings(text)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        return txt_path
    else: 
        return None

# Ligature/encoding fixes + cleanup for embeddings
_LIGATURE_MAP = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
    "–": "-", "—": "-", "−": "-", "“": '"', "”": '"', "’": "'", "‘": "'",
    "•": "-", "·": "·"  # keep middle dot if it’s meaningful
}

def clean_for_embeddings(raw: str) -> str:
    t = raw

    # Fix common ligatures / punctuation first
    for k, v in _LIGATURE_MAP.items():
        t = t.replace(k, v)

    # Some broken extractions swap ligatures for odd ASCII (rare but possible).
    # If you saw '>' where 'ff' should be, patch it here as a last resort:
    t = re.sub(r'(?<=sti)>ness', 'ffness', t)  # optional targeted fix

    # Normalize newlines
    t = t.replace("\r\n", "\n").replace("\r", "\n")

    # Remove page-number-only lines (tune as needed)
    t = re.sub(r"\n\s*\d+\s*\n", "\n", t)

    # De-hyphenate across line breaks: 'comput-\ners' -> 'computers'
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)

    # Join hard wraps inside paragraphs: if no sentence punctuation, merge line
    t = re.sub(r"(?<![.!?;:])\n(?!\n)", " ", t)

    # Collapse 3+ newlines to 2 (paragraph breaks)
    t = re.sub(r"\n{3,}", "\n\n", t)

    # Fix split digits like "001 1" -> "0011"
    t = re.sub(r"(?<=\d)\s+(?=\d)", "", t)

    # Collapse extra spaces
    t = re.sub(r"[ \t]{2,}", " ", t).strip()
    return t

# Example: load local PDF file into memory
# with open("CENG330 Mini Project Report.pdf", "rb") as f:
#     buf = io.BytesIO(f.read())


# Save as .txt file
# out_path = save_pdf_bytes_as_txt(buf, "test.txt")
# print(f"Saved text file at: {out_path}")


#files need name, date appended to top 
