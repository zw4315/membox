from __future__ import annotations

def print_kv(d: dict) -> None:
    print("  " + " ".join([f"{k}={v}" for k, v in d.items()]))
