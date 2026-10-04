import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError

from backend.app.config import settings
from backend.app.errors import (
    NaviGoException,
    navigo_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from backend.app.db.client import init_db
from backend.app.routers import (
    health, destinations, weather, places, trips,
    vision, reports, alerts, chat, voice, internal_cron,
    businesses, reviews, admin, me
)

# Setup logging
logging.basicConfig(
    level=logging.INFO if settings.app_env == "prod" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("navigo.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NaviGo server in %s mode (PORT=%s)...", settings.app_env, settings.port)
    init_db()
    yield
    logger.info("NaviGo server shutting down...")

app = FastAPI(
    title="NaviGo API",
    description="Multimodal AI Tourism Platform for Northern Pakistan",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = settings.cors_origins
if not origins or "*" in origins or settings.app_env == "dev":
    cors_origins = ["*"]
else:
    cors_origins = origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(NaviGoException, navigo_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include Routers
app.include_router(health.router, prefix="/api")
app.include_router(destinations.router, prefix="/api")
app.include_router(weather.router, prefix="/api")
app.include_router(places.router, prefix="/api")
app.include_router(trips.router, prefix="/api")
app.include_router(vision.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(internal_cron.router, prefix="/api")
app.include_router(businesses.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(me.router, prefix="/api")

# Static Frontend Mounting
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.isdir(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    if os.path.isdir(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.isdir(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")

    @app.get("/")
    async def serve_index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "NaviGo API running. Frontend index.html not yet built."}

    # Service Worker route for Push Notifications
    @app.get("/sw.js")
    async def serve_sw():
        sw_file = os.path.join(FRONTEND_DIR, "sw.js")
        if os.path.exists(sw_file):
            return FileResponse(sw_file, media_type="application/javascript")
        return FileResponse(os.path.join(FRONTEND_DIR, "js", "sw.js"), media_type="application/javascript") if os.path.exists(os.path.join(FRONTEND_DIR, "js", "sw.js")) else ("// SW", 200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port, reload=(settings.app_env == "dev"))
