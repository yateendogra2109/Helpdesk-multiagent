"""Chunk the documents in data/docs, embed them with Ollama and store them in ChromaDB.

Usage: python ingest.py [--reset]
"""
import argparse
import re

import chromadb
import requests
from pypdf import PdfReader

from helpdesk import config


def embed(texts: list[str]) -> list[list[float]]:
    r = requests.post(
        f"{config.OLLAMA_BASE}/api/embed",
        json={"model": config.EMBED_MODEL, "input": texts},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["embeddings"]


def read_pages(path):
    """Yield (page_number, text) for a document."""
    if path.suffix.lower() == ".pdf":
        for i, page in enumerate(PdfReader(str(path)).pages, start=1):
            yield i, page.extract_text() or ""
    else:
        yield 1, path.read_text(encoding="utf-8", errors="ignore")


def chunk(text: str, size: int, overlap: int):
    text = " ".join(text.split())
    start = 0
    while start < len(text):
        yield text[start:start + size]
        start += size - overlap


def chunk_markdown(text: str, size: int, overlap: int):
    """Section-aware chunks for markdown: every chunk starts with the document title and the
    section heading, so a section such as 'Revised policy' never shares a chunk with 'Existing policy'."""
    lines = text.strip().splitlines()
    title = lines[0].lstrip("# ").strip() if lines else ""
    sections = re.split(r"(?m)^(?=#{2,3} )", text)
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        heading = sec.splitlines()[0].lstrip("# ").strip() if sec.startswith("#") else ""
        prefix = f"[{title}] [{heading}] " if heading and heading != title else f"[{title}] "
        for piece in chunk(sec, size, overlap):
            yield prefix + piece


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="drop the collection first")
    args = ap.parse_args()

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    if args.reset:
        try:
            client.delete_collection(config.COLLECTION)
        except Exception:
            pass
    col = client.get_or_create_collection(config.COLLECTION, metadata={"hnsw:space": "cosine"})

    files = sorted(p for p in config.DOCS_DIR.rglob("*") if p.suffix.lower() in {".pdf", ".txt", ".md"})
    if not files:
        print(f"No documents found in {config.DOCS_DIR}. Add PDFs/txt/md files and re-run.")
        return

    for path in files:
        ids, docs, metas = [], [], []
        for page, text in read_pages(path):
            splitter = chunk_markdown if path.suffix.lower() == ".md" else chunk
            for n, piece in enumerate(splitter(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)):
                if len(piece.strip()) < 40:
                    continue
                ids.append(f"{path.name}:{page}:{n}")
                docs.append(piece)
                metas.append({"source": path.name, "page": page})
        if not docs:
            print(f"  skipped {path.name} (no text extracted; scanned PDF?)")
            continue
        for i in range(0, len(docs), 32):
            col.upsert(
                ids=ids[i:i + 32],
                documents=docs[i:i + 32],
                metadatas=metas[i:i + 32],
                embeddings=embed(docs[i:i + 32]),
            )
        print(f"  {path.name}: {len(docs)} chunks")
    print(f"Done. Collection size: {col.count()}")


if __name__ == "__main__":
    main()
