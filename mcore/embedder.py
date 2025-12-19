from __future__ import annotations

import re
import numpy as np
import hashlib

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")

def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())

def hashed_bow_embedding(text: str, dim: int = 768) -> np.ndarray:
    v = np.zeros(dim, dtype=np.float32)
    for tok in _tokenize(text):
        h = hashlib.blake2b(tok.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(h[:4], "little") % dim
        sign = 1.0 if (h[4] & 1) == 0 else -1.0
        v[idx] += sign
    n = float(np.linalg.norm(v))
    if n > 0:
        v /= n
    return v
