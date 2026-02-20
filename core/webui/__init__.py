"""
MININA WebUI Modular
==================
Nueva estructura modular para la interfaz web de MININA.
Reemplaza al monolítico WebUI.py (5848 líneas).
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from core.config import get_settings
from core.logging_config import get_logger
from core.CortexBus import bus

from .routes import dashboard, pc_explorer, bot_config, llm_config, skills, chat, backup, logs, marketplace, credentials, memory, apis, works, auditoria
from .dependencies import get_state_manager
from .security import SecurityHeadersMiddleware, RateLimitMiddleware

logger = get_logger("MININA.WebUI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    logger.info("WebUI starting up")
    settings = get_settings()
    settings.ensure_directories()
    
    yield
    
    # Shutdown
    logger.info("WebUI shutting down")


def create_app() -> FastAPI:
    """
    Factory function to create FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title="MININA API",
        description="API REST para el Asistente Virtual MININA",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )
    
    # Security headers middleware
    if settings.WEBUI_ENABLE_SECURITY_HEADERS:
        app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS middleware
    if settings.WEBUI_ENABLE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.WEBUI_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Rate limiting middleware
    if settings.ENABLE_RATE_LIMITING:
        app.add_middleware(RateLimitMiddleware)
    
    # State manager dependency
    app.state.manager = get_state_manager()
    
    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static files mounted from {static_dir}")
    
    # Include routers
    app.include_router(dashboard.router, tags=["Dashboard"])
    app.include_router(pc_explorer.router, prefix="/api/pc", tags=["PC Explorer"])
    app.include_router(bot_config.router, prefix="/api/bot", tags=["Bot Configuration"])
    app.include_router(llm_config.router, prefix="/api/llm", tags=["LLM Configuration"])
    app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(backup.router, prefix="/api/backup", tags=["Backup"])
    app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
    app.include_router(marketplace.router, prefix="/api/marketplace", tags=["Marketplace"])
    app.include_router(credentials.router, prefix="/api/credentials", tags=["Credentials"])
    app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
    app.include_router(apis.router, prefix="/api/apis", tags=["APIs"])
    app.include_router(works.router, tags=["Works"])
    app.include_router(auditoria.router, tags=["Auditoría"])
    
    # Root endpoint serves the dashboard HTML
    @app.get("/")
    async def root():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "MININA Dashboard - Use /api/docs for API documentation"}
    
    logger.info("WebUI application created successfully")
    return app


async def run_web_server(host: str = "127.0.0.1", port: int = 8765):
    """Run the WebUI server with uvicorn."""
    app = create_app()
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
