from fastapi import FastAPI
from .routes import router

def create_app() -> FastAPI:
    app = FastAPI(title="membox API", version="0.5")
    app.include_router(router)
    return app

app = create_app()
