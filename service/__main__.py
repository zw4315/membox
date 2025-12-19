from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("MEMBOX_HOST", "127.0.0.1")
    port = int(os.getenv("MEMBOX_PORT", "8000"))
    reload = os.getenv("MEMBOX_RELOAD", "1") not in ("0", "false", "False")

    # 这里用 module:app 的形式，适配 python -m
    uvicorn.run("service.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()