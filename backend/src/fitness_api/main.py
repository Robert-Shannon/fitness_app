from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.fitness_api.api.v1.endpoints.auth import whoop as whoop_auth
from src.fitness_api.api.v1.endpoints.auth import users as users_auth
from src.fitness_api.api.v1.endpoints.auth import login as login_auth

app = FastAPI(
    title="Fitness Dashboard API",
    description="API for managing fitness data from various sources",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://localhost:19006"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Include the Whoop OAuth endpoints under the /api/v1/auth prefix.
app.include_router(
    whoop_auth.router,
    prefix="/api/v1/auth",
    tags=["auth"]
)

# Include the user creation endpoint (you can adjust the prefix if needed)
app.include_router(
    users_auth.router,
    prefix="/api/v1/auth",
    tags=["users"]
)

app.include_router(
    login_auth.router,
    prefix="/api/v1/auth",
    tags=["login"]
)