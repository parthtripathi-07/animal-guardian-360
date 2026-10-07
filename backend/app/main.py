"""
FastAPI application factory, middleware, CORS, lifespan, and global exception handlers.
"""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select

from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.exceptions import AppException
from app.api.router import api_v1_router
from app.models.user import Role

# Logging setup
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("animal_guardian")

# Optional Sentry APM & Error Tracking
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=1.0 if settings.DEBUG else 0.1,
        )
        logger.info("Sentry observability initialized for environment '%s'", settings.ENVIRONMENT)
    except Exception as exc:
        logger.warning("Could not initialize Sentry: %s", exc)


async def init_default_roles():
    """Seed initial database roles if not already present."""
    roles = [
        ("user", "General public user who can report incidents and find lost pets"),
        ("hospital", "Verified veterinary hospital/clinic responding to SOS emergency dispatches"),
        ("admin", "Platform administrator managing cruelty reports, strikes, and fund allocations")
    ]
    async with AsyncSessionLocal() as session:
        for name, desc in roles:
            stmt = select(Role).where(Role.name == name)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                session.add(Role(name=name, description=desc))
        await session.commit()
    logger.info("Initialized default application roles (user, hospital, admin)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up %s in %s mode...", settings.APP_NAME, settings.ENVIRONMENT)
    # Ensure database schema is created (for dev/sqlite/tests)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_default_roles()
    yield
    # Shutdown actions
    logger.info("Shutting down %s...", settings.APP_NAME)
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready backend API for Animal Guardian 360° platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS configuration (supports localhost, 127.0.0.1, LAN WiFi IPs, and mobile devices)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        errors.append({
            "loc": [str(loc) for loc in err.get("loc", [])],
            "msg": err.get("msg", ""),
            "type": err.get("type", "")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "message": "Input validation failed. Please check the request parameters.",
            "details": errors
        }
    )


# Health check endpoint
@app.get("/health", tags=["System"], summary="Service health status")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }


# Include v1 API routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
