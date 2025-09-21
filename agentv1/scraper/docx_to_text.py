# docx_to_text.py
# pip install python-docx

import io, os, re, datetime
from pathlib import Path
from typing import List, Iterable, Union

# Correct python-docx imports:
from docx import Document as load_document          # loader function
from docx.document import Document as DocxDocument  # class for isinstance checks
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

# ---------- Extraction ----------

def _is_heading(p: Paragraph) -> int:
    """Return heading level 1..9 if paragraph style is Heading N, else 0."""
    name = (p.style.name or "").strip() if p.style else ""
    if name.startswith("Heading"):
        parts = name.split()
        if len(parts) == 2 and parts[1].isdigit():
            lvl = int(parts[1])
            if 1 <= lvl <= 9:
                return lvl
    return 0

def _is_list(p: Paragraph) -> bool:
    """
    Heuristic: treat paragraphs with list-related styles or numbering props as list items.
    python-docx doesn't expose list level directly; use style + numPr presence.
    """
    name = (p.style.name or "").lower() if p.style else ""
    if any(k in name for k in ("list", "bullet", "number")):
        return True
    # Fallback: inspect underlying XML for numbering (numPr)
    try:
        return p._p.pPr is not None and p._p.pPr.numPr is not None
    except Exception:
        return False

def _list_level(p: Paragraph) -> int:
    """
    Best-effort indent level based on left indent in twips (1 level ≈ 360 twips ~ 0.25in).
    """
    try:
        ppr = p._p.pPr
        if ppr is not None and ppr.ind is not None and ppr.ind.left is not None:
            left = int(ppr.ind.left)
            return max(0, min(6, left // 360))
    except Exception:
        pass
    return 0

def _paragraph_to_lines(p: Paragraph) -> List[str]:
    text = (p.text or "").replace("\r", "\n").strip()
    if not text:
        return []
    h = _is_heading(p)
    if h:
        hashes = "#" * min(6, h)
        return [f"{hashes} {text}"]
    if _is_list(p):
        lvl = _list_level(p)
        prefix = ("- " if lvl == 0 else "  " * lvl + "- ")
        return [prefix + text]
    return [text]

def _iter_block_items(parent) -> Iterable[Union[Paragraph, Table]]:
    """
    Yield paragraphs and tables in document order for Document or _Cell.
    """
    if isinstance(parent, DocxDocument):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        # Fallback for sections etc.
        parent_elm = parent._element

    for child in parent_elm.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, parent)
        elif child.tag.endswith("}tbl"):
            yield Table(child, parent)

def _table_to_lines(tbl: Table) -> List[str]:
    lines = []
    for row in tbl.rows:
        cells = []
        for cell in row.cells:
            cell_text = "\n".join((para.text or "").strip() for para in cell.paragraphs).strip()
            cell_text = cell_text.replace("\r", "\n")
            cells.append(cell_text)
        line = "\t".join(s for s in cells if s is not None).strip()
        if line:
            lines.append(line)
    return lines

def docx_bytes_to_text(buf: io.BytesIO) -> str:
    """Extract human-visible text from DOCX (in-memory) similarly to your PPTX routine."""
    buf.seek(0)
    doc = load_document(buf)  # use loader function
    out_lines: List[str] = []

    for block in _iter_block_items(doc):
        if isinstance(block, Paragraph):
            out_lines.extend(_paragraph_to_lines(block))
        elif isinstance(block, Table):
            out_lines.extend(_table_to_lines(block))

    flat = [ (ln or "").strip() for ln in out_lines if (ln or "").strip() ]
    return "\n".join(flat).strip()

# ---------- Cleaning (same vibe as your PPTX cleaner) ----------

_LIGATURE_MAP = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
    "–": "-", "—": "-", "−": "-", "“": '"', "”": '"', "’": "'", "‘": "'",
    "•": "-", "·": "·"
}

def clean_for_embeddings(raw: str) -> str:
    t = raw or ""
    for k, v in _LIGATURE_MAP.items():
        t = t.replace(k, v)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n\s*\d+\s*\n", "\n", t)                            # remove isolated page numbers
    t = re.sub(r"(?<![.!?;:])\n(?!\n|# |- )", " ", t)                # join hard wraps
    t = re.sub(r"\n{3,}", "\n\n", t)                                 # collapse 3+ newlines → 2
    t = re.sub(r"[ \t]{2,}", " ", t)                                 # trim repeated spaces/tabs
    return t.strip()

# ---------- Save helper (mirrors your PDF/PPTX versions) ----------

def save_docx_bytes_as_txt(buf: io.BytesIO, docx_filename: str, output_dir: str = ".",
                           include_header: bool = True) -> str:
    """
    Convert DOCX bytes to cleaned .txt for embeddings.
    """
    base = os.path.splitext(os.path.basename(docx_filename))[0]
    out_path = str(Path(output_dir) / f"{base}.txt")

    text = docx_bytes_to_text(buf)
    text = clean_for_embeddings(text)

    if include_header:
        today = datetime.date.today().isoformat()
        header = f"{base}\nDate: {today}\n\n"
        text = header + text

    os.makedirs(output_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return out_path

# ---------- Example usage ----------

# if __name__ == "__main__":
#     # Load a .docx into memory (no temp files)
#     sample = "Example.docx"
#     if not Path(sample).exists():
#         print(f"[!] Put '{sample}' next to this script to run the demo.")
#     else:
#         with open(sample, "rb") as f:
#             docx_buf = io.BytesIO(f.read())

#         # Preview first 2k chars
#         preview = docx_bytes_to_text(docx_buf)
#         print(preview[:2000])

#         # Save to .txt (named after the .docx)
#         out_txt = save_docx_bytes_as_txt(docx_buf, sample)
#         print(f"Saved text file at: {out_txt}")
