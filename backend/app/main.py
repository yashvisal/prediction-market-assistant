from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.services.markets import initialize_runtime


def parse_cors_origins() -> list[str]:
    return list(get_settings().backend_cors_origins)


app = FastAPI(
    title="World Signal Feed API",
    description="Topic-centric intelligence API built on top of Prediction Hunt signal inputs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    initialize_runtime()
