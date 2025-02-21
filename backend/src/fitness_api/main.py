from fastapi import FastAPI
from fitness_api.api.v1.endpoints import whoop

app = FastAPI(title="Fitness Dashboard API")

# Include Whoop routes
app.include_router(
    whoop.router,
    prefix="/api/v1/whoop",
    tags=["whoop"]
)