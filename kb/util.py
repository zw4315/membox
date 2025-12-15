from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def uuid4() -> str:
    return str(uuid.uuid4())

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def norm_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())
