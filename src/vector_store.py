"""A small vector database layer with two interchangeable backends.

* ChromaStore : ChromaDB persistent client (used automatically when `chromadb` is installed).
* SimpleStore : numpy + JSON files, zero extra dependencies (fine for thousands of items).

Both expose: add (upsert), query, get, all, update_metadata, delete, clear, count.
Hits look like {"id", "text", "score" (cosine similarity), "metadata"}.
"""
import json
import os
from pathlib import Path

import numpy as np

from . import config


def _matches(meta: dict, where) -> bool:
    return all(meta.get(k) == v for k, v in (where or {}).items())


class SimpleStore:
    backend = "simple"

    def __init__(self, name, embedder, base_dir):
        self.name, self.embedder = name, embedder
        self.dir = Path(base_dir) / "simple" / name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ids, self.texts, self.metas = [], [], []
        self.vecs = np.zeros((0, 0), dtype=np.float32)
        self._embedder_name = embedder.name
        self._load()

    # ---------------- persistence
    def _load(self):
        f = self.dir / "docs.json"
        if not f.exists():
            return
        d = json.loads(f.read_text(encoding="utf-8"))
        self.ids, self.texts, self.metas = d["ids"], d["texts"], d["metas"]
        self.vecs = np.load(self.dir / "vecs.npy")
        if d.get("embedder") != self.embedder.name and self.ids:
            print(f"[vector_store:{self.name}] embedder changed ({d.get('embedder')} -> {self.embedder.name}); "
                  f"re-embedding {len(self.ids)} items")
            self.vecs = self.embedder.embed(self.texts)
            self._save()

    def _save(self):
        tmp = self.dir / "docs.json.tmp"
        tmp.write_text(json.dumps({"embedder": self.embedder.name, "ids": self.ids, "texts": self.texts,
                                   "metas": self.metas}, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.dir / "docs.json")
        np.save(self.dir / "vecs.npy", self.vecs)

    # ---------------- API
    def count(self):
        return len(self.ids)

    def add(self, ids, texts, metadatas=None):
        if not ids:
            return
        metadatas = metadatas or [{} for _ in ids]
        last = {i: (t, m) for i, t, m in zip(ids, texts, metadatas)}      # de-duplicate inside the batch
        ids = list(last)
        texts = [last[i][0] for i in ids]
        metadatas = [last[i][1] for i in ids]
        emb = self.embedder.embed(texts)
        if self.vecs.size == 0:
            self.vecs = np.zeros((0, emb.shape[1]), dtype=np.float32)
        index = {i: n for n, i in enumerate(self.ids)}
        fresh = []
        for j, (i, t, m) in enumerate(zip(ids, texts, metadatas)):
            if i in index:
                n = index[i]
                self.texts[n], self.metas[n], self.vecs[n] = t, dict(m), emb[j]
            else:
                self.ids.append(i); self.texts.append(t); self.metas.append(dict(m)); fresh.append(emb[j])
        if fresh:
            self.vecs = np.vstack([self.vecs, np.array(fresh, dtype=np.float32)])
        self._save()

    def _hit(self, n, score=None):
        return {"id": self.ids[n], "text": self.texts[n], "score": score, "metadata": dict(self.metas[n])}

    def query(self, text, k=5, where=None):
        if not self.ids:
            return []
        sims = self.vecs @ self.embedder.embed([text])[0]
        out = []
        for n in np.argsort(-sims):
            if where and not _matches(self.metas[n], where):
                continue
            out.append(self._hit(int(n), float(sims[n])))
            if len(out) >= k:
                break
        return out

    def get(self, id_):
        return self._hit(self.ids.index(id_)) if id_ in self.ids else None

    def all(self, where=None):
        return [self._hit(n) for n in range(len(self.ids)) if _matches(self.metas[n], where)]

    def update_metadata(self, id_, metadata):
        n = self.ids.index(id_)
        self.metas[n] = {**self.metas[n], **metadata}
        self._save()

    def delete(self, ids):
        drop = set(ids)
        keep = [n for n, i in enumerate(self.ids) if i not in drop]
        self.ids = [self.ids[n] for n in keep]
        self.texts = [self.texts[n] for n in keep]
        self.metas = [self.metas[n] for n in keep]
        self.vecs = self.vecs[keep] if keep else np.zeros((0, 0), dtype=np.float32)
        self._save()

    def clear(self):
        self.ids, self.texts, self.metas = [], [], []
        self.vecs = np.zeros((0, 0), dtype=np.float32)
        self._save()


def _clean_meta(m):
    out = {k: ("" if v is None else v) for k, v in dict(m).items()}
    return out or {"_": 1}


def _chroma_where(where):
    if not where:
        return None
    items = [{k: v} for k, v in where.items()]
    return items[0] if len(items) == 1 else {"$and": items}


class ChromaStore:
    backend = "chroma"

    def __init__(self, name, embedder, base_dir):
        import chromadb
        self.name, self.embedder = name, embedder
        self.cname = f"campus_{name}"
        self.client = chromadb.PersistentClient(path=str(Path(base_dir) / "chroma"))
        self.col = self.client.get_or_create_collection(
            self.cname, metadata={"hnsw:space": "cosine", "embedder": embedder.name})
        stored = (self.col.metadata or {}).get("embedder")
        if stored and stored != embedder.name and self.col.count():
            print(f"[vector_store:{name}] embedder changed ({stored} -> {embedder.name}); re-embedding")
            old = self.col.get(include=["documents", "metadatas"])
            self.client.delete_collection(self.cname)
            self.col = self.client.create_collection(
                self.cname, metadata={"hnsw:space": "cosine", "embedder": embedder.name})
            self._upsert(old["ids"], old["documents"], old["metadatas"])

    def _upsert(self, ids, texts, metas):
        if ids:
            self.col.upsert(ids=list(ids), documents=list(texts),
                            embeddings=self.embedder.embed(texts).tolist(),
                            metadatas=[_clean_meta(m) for m in metas])

    def count(self):
        return self.col.count()

    def add(self, ids, texts, metadatas=None):
        if not ids:
            return
        metadatas = metadatas or [{} for _ in ids]
        last = {i: (t, m) for i, t, m in zip(ids, texts, metadatas)}
        ids = list(last)
        self._upsert(ids, [last[i][0] for i in ids], [last[i][1] for i in ids])

    def query(self, text, k=5, where=None):
        n = self.col.count()
        if n == 0:
            return []
        r = self.col.query(query_embeddings=self.embedder.embed([text]).tolist(), n_results=min(k, n),
                           where=_chroma_where(where), include=["documents", "metadatas", "distances"])
        return [{"id": i, "text": d, "score": 1.0 - float(dist), "metadata": dict(m or {})}
                for i, d, m, dist in zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0])]

    def _hits(self, r):
        return [{"id": i, "text": d, "score": None, "metadata": dict(m or {})}
                for i, d, m in zip(r["ids"], r["documents"], r["metadatas"])]

    def get(self, id_):
        r = self.col.get(ids=[id_], include=["documents", "metadatas"])
        h = self._hits(r)
        return h[0] if h else None

    def all(self, where=None):
        return self._hits(self.col.get(where=_chroma_where(where), include=["documents", "metadatas"]))

    def update_metadata(self, id_, metadata):
        cur = self.get(id_)["metadata"]
        self.col.update(ids=[id_], metadatas=[_clean_meta({**cur, **metadata})])

    def delete(self, ids):
        if ids:
            self.col.delete(ids=list(ids))

    def clear(self):
        self.client.delete_collection(self.cname)
        self.col = self.client.create_collection(
            self.cname, metadata={"hnsw:space": "cosine", "embedder": self.embedder.name})


def _choose_backend(base_dir: Path, requested):
    if requested in ("chroma", "simple"):
        return requested
    flag = base_dir / "backend.txt"
    recorded = flag.read_text().strip() if flag.exists() else None
    if recorded == "simple":
        return "simple"
    try:
        import chromadb  # noqa: F401
        choice = "chroma"
    except Exception:
        if recorded == "chroma":
            print("[vector_store] ChromaDB data exists but chromadb is not importable; using the simple store")
        choice = "simple"
    if recorded is None:
        base_dir.mkdir(parents=True, exist_ok=True)
        flag.write_text(choice)
    return choice


def open_store(name, embedder, backend=None, base_dir=None):
    base_dir = Path(base_dir or config.VECTORDB_DIR)
    base_dir.mkdir(parents=True, exist_ok=True)
    chosen = _choose_backend(base_dir, backend or config.VECTOR_BACKEND)
    return (ChromaStore if chosen == "chroma" else SimpleStore)(name, embedder, base_dir)
