from fastapi import APIRouter, HTTPException, BackgroundTasks, Body, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from app.hardware.pump import PUMP_HEADS

def get_router(pump, scheduler_manager, sqlite_client):
    router = APIRouter()

    @router.post(
        "/dose/{doser_id}",
        summary="Send a manual dose command",
        description="Send a manual dose command to a specific doser head."
    )
    async def send_dose_task(doser_id: int, ml: float, background_tasks: BackgroundTasks):
        """
        Send a manual dose command to the specified doser head.
        """
        if doser_id not in PUMP_HEADS:
            raise HTTPException(status_code=400, detail="Invalid doser ID.")

        UPPER_LIMIT = 20
        if not (0 < ml <= UPPER_LIMIT):
            raise HTTPException(status_code=400, detail=f"Invalid dosing amount. Must be greater than 0mL and smaller/equal to {UPPER_LIMIT}mL.")
        
        background_tasks.add_task(pump.dose, doser_id, "Manual", ml)
        return PlainTextResponse(content=f"Sent dose command for {ml}mL on doser {doser_id}.", status_code=200)

    @router.post(
        "/prime/{doser_id}",
        summary="Prime a doser head",
        description="Prime the specified doser head with a fixed amount."
    )
    async def send_prime_task(doser_id: int, background_tasks: BackgroundTasks):
        """
        Prime the specified doser head with a fixed amount.
        """
        if doser_id not in PUMP_HEADS:
            raise HTTPException(status_code=400, detail="Invalid doser ID.")
        
        ml = 5.0
        background_tasks.add_task(pump.dose, doser_id, "Primer", ml)
        return PlainTextResponse(content=f"Sent command to prime {ml}mL on doser {doser_id}.", status_code=200)

    @router.get(
        "/logs",
        summary="Get raw dose reports",
        description="Fetch all raw dosing report logs."
    )
    def get_logs(raw: bool = Query(False)):
        """
        Fetch all raw dosing report logs.
        """
        table_name = sqlite_client.RAW_LOGS_TABLE_NAME if raw else sqlite_client.LOGS_TABLE_NAME
        logs = sqlite_client.fetch_all(table_name)
        return JSONResponse(content=logs, status_code=200)

    @router.post(
        "/schedule",
        summary="Set dosing schedule",
        description="Set a dosing schedule for a specific head."
    )
    def set_schedule(
        head: int = Body(...),
        total_dose: float = Body(...),
        doses_per_day: int = Body(...)
    ):
        """
        Set a dosing schedule for a specific head.
        """
        if head not in [1, 2]:
            raise HTTPException(status_code=400, detail="Invalid head. Must be 1 or 2.")

        if total_dose <= 0 or doses_per_day <= 0:
            raise HTTPException(status_code=400, detail="Dose and doses per day must be positive.")
        
        scheduler_manager.set_schedule(head, total_dose, doses_per_day)
        return PlainTextResponse(content=f"Schedule set for head {head}.", status_code=200)

    @router.get(
        "/schedules",
        summary="Get all schedules",
        description="Get all current dosing schedules."
    )
    def get_schedules():
        """
        Get all current dosing schedules.
        """
        return JSONResponse(content=scheduler_manager.get_schedules(), status_code=200)

    @router.post(
        "/schedule/pause/{head}",
        summary="Pause schedule",
        description="Pause the dosing schedule for a specific head."
    )
    def pause_schedule(head: int):
        """
        Pause the dosing schedule for a specific head.
        """
        scheduler_manager.pause_schedule(head)
        return PlainTextResponse(content=f"Paused schedule for head {head}.", status_code=200)

    @router.post(
        "/schedule/resume/{head}",
        summary="Resume schedule",
        description="Resume the dosing schedule for a specific head."
    )
    def resume_schedule(head: int):
        """
        Resume the dosing schedule for a specific head.
        """
        scheduler_manager.resume_schedule(head)
        return PlainTextResponse(content=f"Resumed schedule for head {head}.", status_code=200)

    @router.post(
        "/schedule/clear/{head}",
        summary="Clear schedule",
        description="Clear the dosing schedule for a specific head."
    )
    def clear_schedule(head: int):
        """
        Clear the dosing schedule for a specific head.
        """
        scheduler_manager.clear_schedule(head)
        return PlainTextResponse(content=f"Cleared schedule for head {head}.", status_code=200)

    return router