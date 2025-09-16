from fastapi import FastAPI
from app.api.routes import get_router
from app.hardware.pump import Pump
from app.scheduler.jobs import SchedulerManager
from app.database.sqlite_client import SQliteClient

def create_app() -> FastAPI:
    # --- Initialize FastAPI app ---
    app = FastAPI()

    # --- Set up database client ---
    sqlite_client = SQliteClient()

    # --- Initialize hardware pump ---
    pump = Pump(sqlite_client)

    # --- Set up scheduler manager ---
    scheduler_manager = SchedulerManager(pump)

    # --- Register API routes ---
    router = get_router(pump, scheduler_manager, sqlite_client)
    app.include_router(router)

    # --- Graceful shutdown for scheduler ---
    @app.on_event("shutdown")
    def shutdown_event():
        scheduler_manager.shutdown()

    return app

app = create_app()