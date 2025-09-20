from app.hardware.pump import Pump
from app.clients.sqlite_client import SQliteClient
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

logger = logging.getLogger(__name__)

class SchedulerManager:
    def __init__(self, pump: Pump, sqlite_client: SQliteClient) -> None:
        self.scheduler = BackgroundScheduler()
        self.pump = pump
        self.sqlite_client = sqlite_client
        self.schedules = self.sqlite_client.fetch_all_schedules(self.sqlite_client.SCHEDULES_TABLE_NAME)
        self._add_jobs_from_store()
        self.scheduler.start()

    def _add_jobs_from_store(self):
        logger.info(self.schedules)
        for head, sched in self.schedules.items():
            if sched["total_dose"] is not None and sched["doses_per_day"] is not None:
                self._add_job(int(head), sched["total_dose"], sched["doses_per_day"])

    def _add_job(self, head, total_dose, doses_per_day):

        self.scheduler.add_job(
            self.pump.dose,
            args=[head, "Scheduled", total_dose / doses_per_day],
            trigger='interval',
            hours=24 / doses_per_day,
            id=f"scheduled_doser_{head}",
            replace_existing=True
        )

    def set_schedule(self, head, total_dose, doses_per_day):

        # Remove existing job for this head
        try:
            self.scheduler.remove_job(f"scheduled_doser_{head}")
        except JobLookupError:
            pass  # Job does not exist, nothing to remove
        
        # Update schedules dict and save
        self.sqlite_client.update_schedule(head, total_dose, doses_per_day)

        # Add new job
        self._add_job(head, total_dose, doses_per_day)
    
    def pause_schedule(self, head):
        job_id = f"scheduled_doser_{head}"
        try:
            self.scheduler.pause_job(job_id)
        except JobLookupError:
            pass  # Job does not exist

    def resume_schedule(self, head):
        job_id = f"scheduled_doser_{head}"
        try:
            self.scheduler.resume_job(job_id)
        except JobLookupError:
            pass  # Job does not exist

    def clear_schedule(self, head):
        job_id = f"scheduled_doser_{head}"
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            pass  # Job does not exist

        # Remove from schedules dict and save
        self.sqlite_client.update_schedule(head, None, None)

    def get_schedules(self):
        return self.sqlite_client.fetch_all_schedules(self.sqlite_client.SCHEDULES_TABLE_NAME)

    def get_jobs(self):
        jobs_list = []
        for job in self.scheduler.get_jobs():
            jobs_list.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time),
                "trigger": str(job.trigger),
                "args": job.args,
                "kwargs": job.kwargs
            })
        return {"jobs": jobs_list}

    def shutdown(self):
        self.scheduler.shutdown(wait=False)