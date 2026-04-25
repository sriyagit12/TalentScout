"""
Talent Scout Agent — FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --port 8000
"""
import logging
import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.scout import router as scout_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Talent Scout Agent",
    description="AI-powered candidate scouting, matching, and engagement.",
    version="1.0.0",
)

# CORS — open in dev; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scout_router)


@app.get("/")
def root():
    return {
        "name": "Talent Scout Agent",
        "docs": "/docs",
        "health": "/api/health",
    }


# Touch __init__.py imports for autodiscovery
__all__ = ["app"]
