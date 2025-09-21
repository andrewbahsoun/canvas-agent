# index_txt_records.py
from __future__ import annotations

import os
import re
import pickle
import hashlib
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple, Dict, Any

from dotenv import load_dotenv
load_dotenv()

import ast
from typing import List, Tuple

from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from rank_bm25 import BM25Okapi

from rag_utils import hybrid_search, format_chunk

# ---------- Config ----------
BASE_DIR = Path(__file__).resolve().parent
CHROMA_DB_PATH = (BASE_DIR / "chroma_db").as_posix()   # per-course folders live here
BM25_DB_PATH   = (BASE_DIR / "bm25_db")                # per-course bm25 pickles
BM25_DB_PATH.mkdir(parents=True, exist_ok=True)

GEMINI_EMBED_MODEL = "models/text-embedding-004"
TOKEN_PATTERN  = re.compile(r"\w+")
CHUNK_SIZE     = 1000
CHUNK_OVERLAP  = 200
STORE_TEXT_IN_CHROMA = True  # if False, we add only vectors + metadata

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not set. Add it to your environment or a .env file.")

# ---------- Data model ----------
@dataclass
class TxtRecord:
    file_name: str
    date: str
    course: str
    module: str
    file_path: str

# ---------- Utils ----------
def slug(s: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

def build_header(r: TxtRecord) -> str:
    return (
        f"# {r.file_name}\n"
        f"Date: {r.date}\n"
        f"Course: {r.course}\n"
        f"Module: {r.module}\n"
        f"Path: {r.file_path}\n\n"
    )

def read_text(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = (BASE_DIR / p).resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return p.read_text(encoding="utf-8", errors="ignore")

def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

def collection_count_safe(vector_store: Chroma) -> int:
    try:
        return vector_store._collection.count()  # type: ignore[attr-defined]
    except Exception:
        return len(vector_store.get().get("ids", []))

def dump_chunks_to_file(course: str, chunks: List[Document], out_dir: str = "./debug_chunks") -> None:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(out_dir) / f"{slug(course)}_chunks.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        for i, c in enumerate(chunks):
            f.write(f"===== CHUNK {i} =====\n")
            f.write(c.page_content)
            if not c.page_content.endswith("\n"):
                f.write("\n")
            f.write("\n")
    print(f"[debug] wrote {len(chunks)} chunks → {out_path}")

def chunk_text_fixed(text: str, size: int, overlap: int) -> List[str]:
    """Greedy fixed-size chunker: ~size chars per chunk (except the last)."""
    assert 0 <= overlap < size, "overlap must be in [0, size)"
    step = size - overlap
    n = len(text)
    chunks: List[str] = []
    i = 0
    while i < n:
        end = min(i + size, n)
        chunks.append(text[i:end])
        if end == n: break
        i += step
    return chunks

# ---------- Indexing ----------
def index_course(records: List[TxtRecord]) -> None:
    """
    Index all TXT records for a single course into its own Chroma collection
    and update a per-course BM25 pickle.
    """
    if not records:
        return

    course = records[0].course
    course_slug = slug(course)
    print(f"\n--- Processing course: {course} ---")

    collection_path = f"{CHROMA_DB_PATH}/{course_slug}_collection"
    bm25_file = BM25_DB_PATH / f"{course_slug}_bm25.pkl"

    embeddings = GoogleGenerativeAIEmbeddings(model=GEMINI_EMBED_MODEL, google_api_key=API_KEY)

    # Load/attach existing collection (for dedupe + append)
    if Path(collection_path).exists() and any(Path(collection_path).iterdir()):
        vector_store = Chroma(persist_directory=collection_path, embedding_function=embeddings)
        existing_meta = vector_store.get(include=["metadatas"]).get("metadatas", [])
        existing_keys = {m.get("source_key", "") for m in existing_meta if isinstance(m, dict)}
        print(f"Found existing collection with {len(existing_keys)} sources.")
    else:
        vector_store = None
        existing_keys = set()
        print("No existing collection - creating fresh.")

    new_chunks: List[Document] = []

    for r in records:
        raw_text = read_text(r.file_path)
        print(f"[index] {r.file_name} body_len={len(raw_text)}")

        source_key = f"{r.file_path}|{r.date}|{content_hash(raw_text)}"
        if source_key in existing_keys:
            continue

        base_meta = {
            "course": r.course,
            "module": r.module,
            "file_name": r.file_name,
            "date": r.date,
            "file_path": r.file_path,
            "source_key": source_key,
        }

        # Fixed-size chunking of BODY ONLY
        body_chunks = chunk_text_fixed(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)

        # Prepend header to EVERY chunk
        header = build_header(r)
        hdr_len = len(header)
        for body_part in body_chunks:
            page = header + body_part
            meta = dict(base_meta)
            meta["__header_len"] = hdr_len
            new_chunks.append(Document(page_content=page, metadata=meta))

    if not new_chunks:
        print("✓  No new TXT files to index for this course.")
        return

    print(f"Split into {len(new_chunks)} new chunks for course '{course}' (header added to each).")

    # Debug dump of final chunks (header+body)
    dump_chunks_to_file(course, new_chunks)

    # Assign stable chunk IDs
    start_id = collection_count_safe(vector_store) if vector_store else 0
    for i, c in enumerate(new_chunks, start=start_id):
        c.metadata["chunk_id"] = i

    # Append to Chroma
    if STORE_TEXT_IN_CHROMA:
        if vector_store:
            vector_store.add_documents(new_chunks)
        else:
            vector_store = Chroma.from_documents(new_chunks, embedding=embeddings, persist_directory=collection_path)
    else:
        texts = [c.page_content for c in new_chunks]
        ids   = [str(c.metadata["chunk_id"]) for c in new_chunks]
        metas = [c.metadata for c in new_chunks]
        embs  = embeddings.embed_documents(texts)
        if vector_store:
            vector_store.add(ids=ids, embeddings=embs, metadatas=metas)
        else:
            vector_store = Chroma(persist_directory=collection_path, embedding_function=embeddings)
            vector_store.add(ids=ids, embeddings=embs, metadatas=metas)

    print(f"   ✅  Vector store updated ({len(new_chunks)} chunks added)")

    # Update BM25 (header included in each chunk)
    toks_new = [TOKEN_PATTERN.findall(c.page_content.lower()) for c in new_chunks]

    if bm25_file.exists():
        with open(bm25_file, "rb") as f:
            payload = pickle.load(f)
        old_tokens = payload["tokens"] if "tokens" in payload else payload["bm25"].corpus
        old_chunks = payload["chunks"]
        old_metas  = payload["metas"]
    else:
        old_tokens, old_chunks, old_metas = [], [], []

    all_tokens = old_tokens + toks_new
    all_chunks = old_chunks + [c.page_content for c in new_chunks]
    all_metas  = old_metas  + [c.metadata for c in new_chunks]

    bm25 = BM25Okapi(all_tokens)
    with open(bm25_file, "wb") as f:
        pickle.dump({"bm25": bm25, "tokens": all_tokens, "chunks": all_chunks, "metas": all_metas}, f)
    print(f"   ✅  BM25 pickle updated → {bm25_file}")

# ---------- Batch API ----------
def index_all_txt_records(records: List[Tuple[str, str, str, str, str]]) -> None:
    """
    records: list of tuples (file_name, date, course, module, file_path)
    Groups by course and indexes into separate Chroma collections + BM25 pickles.
    """
    by_course: Dict[str, List[TxtRecord]] = defaultdict(list)
    for (file_name, date, course, module, file_path) in records:
        by_course[course].append(TxtRecord(file_name, date, course, module, file_path))

    for course, recs in by_course.items():
        index_course(recs)

# ---------- Optional: quick CLI ----------
if __name__ == "__main__":
# Read file_infos.txt (each line is a dict-like string)
    with open("scraper/file_infos.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Parse each line into a Python dict
    file_infos = [ast.literal_eval(line.strip()) for line in lines]

    # Convert into tuples (name, date, course, module, path)
    tuples: List[Tuple[str, str, str, str, str]] = [
        (
            fi["name"],
            fi["date"],
            fi["course"],
            fi["module"],
            fi["path"]
        )
        for fi in file_infos
    ]

    # Now index them
    index_all_txt_records(tuples)
    print("\nAll TXT records indexed successfully!")

