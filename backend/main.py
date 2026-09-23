import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import load_environment
from .loader import DEFAULT_DATA_PATH, load_contractors
from .models import RecommendRequest, RecommendResponse
from .service import recommend


def create_app(data_path: Path | None = None) -> FastAPI:
    load_environment()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        path = data_path if data_path is not None else Path(os.getenv("CONTRACTORS_CSV", str(DEFAULT_DATA_PATH)))
        app.state.contractors = load_contractors(path)
        yield

    app = FastAPI(title="HackAlem Contractor Matching", version="0.1.0", lifespan=lifespan)
    origins = [v.strip() for v in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if v.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @app.get("/health")
    def health(request: Request):
        return {"status": "ok", "profiles": len(request.app.state.contractors)}

    @app.post("/recommend", response_model=RecommendResponse)
    def recommendations(body: RecommendRequest, request: Request) -> RecommendResponse:
        return recommend(request.app.state.contractors, body)

    return app


app = create_app()
