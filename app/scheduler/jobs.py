from app.hardware.pump import Pump
from app.scheduler.schedule_store import load_schedules, save_schedules

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

class SchedulerManager:
    def __init__(self, pump: Pump):
        self.scheduler = BackgroundScheduler()
        self.pump = pump
        self.schedules = load_schedules()
        self._add_jobs_from_store()
        self.scheduler.start()

    def _add_jobs_from_store(self):
        for head, sched in self.schedules.items():
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

        # Save new schedule
        self.schedules[str(head)] = {
            "total_dose": total_dose,
            "doses_per_day": doses_per_day
        }

        save_schedules(self.schedules)

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
        self.schedules.pop(str(head), None)
        save_schedules(self.schedules)

    def get_schedules(self):
        return self.schedules

    def get_jobs(self):
        return self.scheduler.get_jobs()

    def shutdown(self):
        self.scheduler.shutdown(wait=False)