from __future__ import annotations

import sqlite3
import numpy as np

def _vec_to_blob(v: np.ndarray) -> bytes:
    v = np.asarray(v, dtype=np.float32)
    return v.tobytes()

def _blob_to_vec(b: bytes, dim: int) -> np.ndarray:
    v = np.frombuffer(b, dtype=np.float32)
    if v.size != dim:
        out = np.zeros(dim, dtype=np.float32)
        n = min(dim, v.size)
        out[:n] = v[:n]
        return out
    return v

def upsert_embeddings(conn: sqlite3.Connection, items: list[tuple[str, str, int, np.ndarray]]) -> None:
    now = conn.execute("SELECT datetime('now')").fetchone()[0]
    for chunk_id, model, dim, vec in items:
        blob = _vec_to_blob(vec)
        conn.execute(
            "INSERT INTO embedding(chunk_id, embedding_model, embedding_dim, vec, created_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(chunk_id) DO UPDATE SET embedding_model=excluded.embedding_model, embedding_dim=excluded.embedding_dim, vec=excluded.vec, created_at=excluded.created_at",
            (chunk_id, model, dim, blob, now),
        )
    conn.commit()

def fetch_all_embeddings(conn: sqlite3.Connection, model_name: str) -> tuple[list[str], int, np.ndarray]:
    rows = conn.execute("SELECT chunk_id, embedding_dim, vec FROM embedding WHERE embedding_model=?", (model_name,)).fetchall()
    if not rows:
        return [], 0, np.zeros((0, 0), dtype=np.float32)
    dim = int(rows[0]["embedding_dim"])
    ids = []
    mat = np.zeros((len(rows), dim), dtype=np.float32)
    for i, r in enumerate(rows):
        ids.append(r["chunk_id"])
        mat[i, :] = _blob_to_vec(r["vec"], dim)
    return ids, dim, mat

def cosine_topk(query: np.ndarray, ids: list[str], mat: np.ndarray, k: int = 10) -> list[tuple[str, float]]:
    if mat.size == 0:
        return []
    q = np.asarray(query, dtype=np.float32)
    n = float(np.linalg.norm(q))
    if n > 0:
        q = q / n
    sims = mat @ q
    if k >= sims.shape[0]:
        idx = np.argsort(-sims)
    else:
        idx = np.argpartition(-sims, k)[:k]
        idx = idx[np.argsort(-sims[idx])]
    return [(ids[i], float(sims[i])) for i in idx]
