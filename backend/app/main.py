from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import settings
from .db import db
from .routes import auth, projects, models, compiler, executions, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect DB
    await db.init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Compiler-driven SaaS Financial Modeling DSL Engine (Course: Principles of Compiler Design)",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(projects.router, prefix=settings.API_PREFIX)
app.include_router(models.router, prefix=settings.API_PREFIX)
app.include_router(compiler.router, prefix=settings.API_PREFIX)
app.include_router(executions.router, prefix=settings.API_PREFIX)
app.include_router(templates.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "primary_storage": "MongoDB Atlas" if db.use_mongo else "Local JSON Store",
        "fallback_storage": "Local JSON Store (Active & Ready)",
        "database_name": settings.DATABASE_NAME if db.use_mongo else "backend/data",
        "compiler": "ModelScript v2.0",
        "docs_url": "/docs"
    }

