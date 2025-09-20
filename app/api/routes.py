from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from fastapi.responses import JSONResponse
from app.hardware.pump import PUMP_HEADS
from typing import Optional

def get_router(pump, scheduler_manager, sqlite_client):
    router = APIRouter()

    @router.post(
            "/remaining/{head}",
            summary="Update remaining liquid",
            description="Update the remaining liquid amount for a specific doser head."
    )
    def set_remaining(head: int, ml: float):
        """
        Set the remaining liquid amount for a specific doser head.
        """
        if head not in PUMP_HEADS:
            raise HTTPException(status_code=400, detail="Invalid head. Must be 1 or 2.")
        
        if ml < 0:
            raise HTTPException(status_code=400, detail="Remaining amount cannot be negative.")
        
        sqlite_client.set_remaining(head, ml)
        return JSONResponse(content=f"Set remaining amount for head {head} to {ml}mL.", status_code=200)

    @router.get(
        "/remaining",
        summary="Get remaining liquid amounts",
        description="Get the remaining liquid amounts for all doser heads."
    )
    def get_remaining():
        """
        Get the remaining liquid amounts for all doser heads.
        """
        remaining = sqlite_client.get_remaining()
        return JSONResponse(content=remaining, status_code=200)
    
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
        return JSONResponse(content=f"Sent dose command for {ml}mL on doser {doser_id}.", status_code=200)

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
        return JSONResponse(content=f"Sent command to prime {ml}mL on doser {doser_id}.", status_code=200)

    @router.get(
        "/logs",
        summary="Get raw dose reports",
        description="Fetch all raw dosing report logs."
    )
    def get_logs(raw: Optional[bool] = False, days: Optional[int] = 7):
        """
        Fetch all raw dosing report logs.
        """
        table_name = sqlite_client.RAW_LOGS_TABLE_NAME if raw else sqlite_client.LOGS_TABLE_NAME
        logs = sqlite_client.fetch_all_logs(table_name=table_name, days=days)
        return JSONResponse(content=logs, status_code=200)
    
    @router.get(
        "/totals",
        summary="Get total dosed amounts",
        description="Get the total dosed amounts for each head, including today's total."
    )
    def get_totals():
        """
        Get the total dosed amounts for each head, including today's total.
        """
        totals = sqlite_client.get_todays_total()
        return JSONResponse(content=totals, status_code=200)

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
        return JSONResponse(content=f"Schedule set for head {head}.", status_code=200)

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
    
    @router.get(
        "/jobs",
        summary="Get all jobs",
        description="Get all current dosing jobs."
    )
    def get_jobs():
        """
        Get all current job schedules.
        """
        return JSONResponse(content=scheduler_manager.get_jobs(), status_code=200)

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
        return JSONResponse(content=f"Paused schedule for head {head}.", status_code=200)

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
        return JSONResponse(content=f"Resumed schedule for head {head}.", status_code=200)

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
        return JSONResponse(content=f"Cleared schedule for head {head}.", status_code=200)

    return router