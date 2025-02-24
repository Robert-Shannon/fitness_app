from fastapi import FastAPI
from .api.v1.endpoints.auth import whoop as whoop_auth

app = FastAPI(
    title="Fitness Dashboard API",
    description="API for managing fitness data from various sources",
    version="1.0.0"
)

# Include routers
app.include_router(
    whoop_auth.router,
    prefix="/api/v1/auth",
    tags=["auth"]
)
