import logging
from contextlib import asynccontextmanager

from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin_routes import admin_router
from app.api.routes import router
from app.config import settings
from app.database import Base, engine
from app.scheduler.jobs import scheduler, sync_all_skills

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Start scheduler
    scheduler.add_job(
        sync_all_skills,
        trigger=IntervalTrigger(hours=settings.sync_interval_hours),
        id="hourly_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with %dh interval", settings.sync_interval_hours)

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")


app = FastAPI(
    title="Agent Skills Hub API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"message": "Agent Skills Hub API", "docs": "/docs"}
