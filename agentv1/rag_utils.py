# rag_utils.py
from __future__ import annotations

import os
import pickle
import re
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
load_dotenv()

import numpy as np
from rank_bm25 import BM25Okapi
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# ---------- Config ----------
BASE_DIR = Path(__file__).resolve().parent
CHROMA_DB_PATH = (BASE_DIR / "chroma_db").as_posix()
BM25_DB_PATH   = (BASE_DIR / "bm25_db")
BM25_DB_PATH.mkdir(parents=True, exist_ok=True)

GEMINI_EMBED_MODEL = "models/text-embedding-004"
TOKEN_PATTERN = re.compile(r"\w+")

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not set. Add it to your environment or a .env file.")

# ---------- Embeddings (singleton) ----------
_embeddings = None
def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBED_MODEL,
            google_api_key=API_KEY,
        )
    return _embeddings

# ---------- Helpers ----------
def slug(s: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

def ensure_list(x):
    if x is None:
        return []
    if isinstance(x, (list, tuple, set)):
        return list(x)
    return [x]


def get_vector_store_for_course(course: str):
    """
    Loads the Chroma vector store for a specific course (collection is persisted per-course).
    """
    persist_directory = f"{CHROMA_DB_PATH}/{slug(course)}_collection"
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=get_embeddings(),
    )

def load_bm25_pkg(course: str) -> Dict[str, Any]:
    pkl = BM25_DB_PATH / f"{slug(course)}_bm25.pkl"
    if not pkl.exists():
        raise FileNotFoundError(f"No BM25 pickle found for course '{course}': {pkl}")
    with pkl.open("rb") as f:
        return pickle.load(f)  # dict with keys: bm25, tokens, chunks, metas

# ---------- Hybrid search ----------
def hybrid_search(
    query: str,
    courses,
    k_final: int = 6,
    k_bm25: int = 20,
    k_embed: int = 12,
    w_bm25: float = 0.25,
    w_emb: float = 0.75,
):
    """
    Hybrid search across one or multiple courses.

    courses: str | List[str]
    Returns: List[{"text", "meta", "score", "preview"}]
    """
    import numpy as np

    fused = {}  # key: (course_slug, chunk_id) -> score
    # Keep per-course bm25 packages for assembly later
    bm25_pkgs = {}  # course_slug -> pkg dict
    vector_stores = {}  # course_slug -> Chroma

    for course in courses:
        course = course[0]
        cslug = slug(course)

        # --- Load stores (skip missing gracefully) ---
        try:
            vs = get_vector_store_for_course(course)
            vector_stores[cslug] = vs
        except Exception as e:
            print(f"[hybrid] skip vectors for {course}: {e}")
            vs = None

        try:
            pkg = load_bm25_pkg(course)  # {bm25, tokens, chunks, metas}
            bm25_pkgs[cslug] = pkg
        except Exception as e:
            print(f"[hybrid] skip BM25 for {course}: {e}")
            pkg = None

        # --- BM25 per course ---
        if pkg is not None:
            bm25 = pkg["bm25"]
            chunks = pkg["chunks"]
            metas  = pkg["metas"]

            tokens = TOKEN_PATTERN.findall(query.lower())
            bm_scores = bm25.get_scores(tokens)  # np.ndarray
            if bm_scores.size:
                bm_range = np.ptp(bm_scores)
                bm_norm  = (bm_scores - bm_scores.min()) / (bm_range + 1e-9)
                top_idx  = np.argsort(bm_norm)[::-1][:k_bm25]
                for i in top_idx:
                    key = (cslug, int(i))
                    fused[key] = fused.get(key, 0.0) + w_bm25 * float(bm_norm[i])

        # --- Vector per course ---
        if vs is not None:
            hits = vs.similarity_search_with_relevance_scores(query, k=k_embed)
            if hits:
                emb_scores = np.array([float(s) for _, s in hits], dtype=float)
                emb_range  = np.ptp(emb_scores)
                emb_norm   = (emb_scores - emb_scores.min()) / (emb_range + 1e-9)
                for (doc, _), sc in zip(hits, emb_norm):
                    chunk_id = int(doc.metadata.get("chunk_id", -1))
                    if chunk_id >= 0:
                        key = (cslug, chunk_id)
                        fused[key] = fused.get(key, 0.0) + w_emb * float(sc)

    if not fused:
        return []

    # --- Global rank across all courses ---
    best = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:k_final]

    # --- Assemble results ---
    out = []
    for (cslug, idx), score in best:
        pkg = bm25_pkgs.get(cslug)
        if pkg is None:
            # Fall back to pulling the doc from the vector store if needed
            # but normally BM25 pkg should exist for assembly
            vs = vector_stores.get(cslug)
            doc, _ = vs.similarity_search_with_relevance_scores(query, k=1)[0] if vs else (None, None)
            if doc is None:
                # Skip if we can't assemble
                continue
            meta = dict(doc.metadata)
            text = doc.page_content
        else:
            text = pkg["chunks"][idx]
            meta = pkg["metas"][idx]

        # annotate course (in case it's missing)
        meta.setdefault("course", cslug)

        # Build preview skipping header (if present)
        hdr_len = int(meta.get("__header_len", 0))
        if len(text) > hdr_len:
            preview = text[hdr_len:hdr_len+400] + "..."
        else:
            preview = text[:400] + "..."

        out.append({
            "text": text,
            "meta": meta,
            "score": float(score),
            "preview": preview,
        })

    return out


def format_chunk(idx: int, item: Dict[str, Any]) -> str:
    course = item["meta"].get("course", "unknown")
    src    = item["meta"].get("file_path", item["meta"].get("source", "unknown"))
    score  = item["score"]
    text   = item.get("preview") or (item["text"][:400] + "...")
    return f"{idx}. [{course}] (score={score:.3f}) {src}\n{text}"

