from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.infrastructure.api.max_body_size_middleware import max_body_size_middleware
from src.infrastructure.api.rate_limiting import limiter
from src.infrastructure.api.v1.auth import router as auth_router
from src.infrastructure.api.v1.batches import router as batches_router
from src.infrastructure.api.v1.health import router as health_router
from src.infrastructure.api.v1.templates import router as templates_router
from src.infrastructure.config import settings
from src.infrastructure.windows_event_loop import ensure_windows_selector_event_loop

ensure_windows_selector_event_loop()

app = FastAPI(
    title="Formex API", version="0.1.0", swagger_ui_parameters={"persistAuthorization": True}
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(max_body_size_middleware)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")
app.include_router(batches_router, prefix="/api/v1")
