import json
import os

SCHEDULE_PATH = "/mnt/schedules.json"

def load_schedules():
    if not os.path.exists(SCHEDULE_PATH):
        return {}
    with open(SCHEDULE_PATH, "r") as f:
        return json.load(f)

def save_schedules(schedules):
    with open(SCHEDULE_PATH, "w") as f:
        json.dump(schedules, f)