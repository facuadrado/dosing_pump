from fastapi import FastAPI, HTTPException, Response, BackgroundTasks
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.responses import JSONResponse, PlainTextResponse
import RPi.GPIO as GPIO
import time
import os
import csv
from datetime import datetime
import csv
import json

#================================ CONSTANTS ================================#
PIN_1 = "pin_1"
PIN_2 = "pin_2"
PRIMER_ML = 5.0

#================================ PUMP SETTINGS & DECLARATION ================================#
DOSER_LEFT_PIN_1 = 17
DOSER_LEFT_PIN_2 = 22
DOSER_RIGHT_PIN_1 = 23
DOSER_RIGHT_PIN_2 = 24

DOSER_GPIO_MAP = {
    1: {
        PIN_1: DOSER_LEFT_PIN_1,
        PIN_2: DOSER_LEFT_PIN_2
    },
    2: {
        PIN_1: DOSER_RIGHT_PIN_1,
        PIN_2: DOSER_RIGHT_PIN_2
    }
}

LEFT_FLOW_RATE_ML_PER_SECOND = 1.40
RIGHT_FLOW_RATE_ML_PER_SECOND = 1.34

PUMP_CALIBRATION_ML_PER_SECOND = {
    1: LEFT_FLOW_RATE_ML_PER_SECOND,
    2: RIGHT_FLOW_RATE_ML_PER_SECOND
}

LEFT_DAILY_SCHEDULED_DOSE = 10
LEFT_DOSES_PER_DAY = 2

RIGHT_DAILY_SCHEDULED_DOSE = 10

# Initializing GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DOSER_GPIO_MAP[1][PIN_1], GPIO.OUT)
GPIO.setup(DOSER_GPIO_MAP[1][PIN_2], GPIO.OUT)
GPIO.setup(DOSER_GPIO_MAP[2][PIN_1], GPIO.OUT)
GPIO.setup(DOSER_GPIO_MAP[2][PIN_2], GPIO.OUT)

#================================ CSV Dosing Data ================================#
SAVE_DIRECTORY = "/mnt"
FILE_NAME = "doser_data.csv"
HEADER = ["Date", "Pump", "Time", "mL", "Mode"]
csv_file = os.path.join(SAVE_DIRECTORY, FILE_NAME)

def record_data_csv(doser_id: int, mode: str, ml: float):
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    time_string = now.strftime("%H:%M:%S")
    
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            writer.writerow(HEADER)
        writer.writerow([date_string, doser_id, time_string, ml, mode])

def dose(doser_id: int, mode: str, ml: float):
    seconds = ml / PUMP_CALIBRATION_ML_PER_SECOND[doser_id]
    pin_1 = DOSER_GPIO_MAP[doser_id][PIN_1]
    pin_2 = DOSER_GPIO_MAP[doser_id][PIN_2]
    
    GPIO.output(pin_1, GPIO.LOW)
    GPIO.output(pin_2, GPIO.HIGH)
    time.sleep(seconds)
    GPIO.output(pin_1, GPIO.LOW)
    GPIO.output(pin_2, GPIO.LOW)
    
    record_data_csv(doser_id, mode, ml)

scheduler = BackgroundScheduler()
scheduler.add_job(dose, args=[2, "Scheduled", LEFT_DAILY_SCHEDULED_DOSE/LEFT_DOSES_PER_DAY], trigger='interval', hours=24/LEFT_DOSES_PER_DAY, id='scheduled_dose')
scheduler.start()

#================================ Fast API ================================#

app = FastAPI()

# Endpoint to manually dose for x mL
@app.post("/dose/{doser_id}")
async def send_dose_task(doser_id: int, ml: float, background_tasks: BackgroundTasks):
    """
    Manually start the dosing process for a specific amount of mL.
    
    Args:
    - doser_id: The id of the doser to activate (e.g., 1 or 2).
    - mL: The amount of mL the pump will dose.
    
    Returns:
    - A success message with the amount of liquid in (mL).
    """
    if doser_id not in DOSER_GPIO_MAP:
        raise HTTPException(status_code=400, detail="Invalid doser ID.")
    
    UPPER_LIMIT = 20
    if not (0 < ml <= UPPER_LIMIT):
        raise HTTPException(status_code=400, 
                            detail=f"Invalid dosing amount. Must be greater than 0mL and smaller/equal to {UPPER_LIMIT}mL."
                            )
    background_tasks.add_task(dose, doser_id, "Manual", ml)
    return PlainTextResponse(content=f"Sent dose command for {ml}mL on doser {doser_id}.", status_code=200)

# Endpoint to prime the doser for 5mL
@app.post("/prime/{doser_id}")
async def send_prime_task(doser_id: int, background_tasks: BackgroundTasks):
    """
    Prime the pump to distribute 5mL to get the liquid flowing.
    
    Args:
    - doser_id: The id of the doser to activate (e.g., 1 or 2).

    Returns:
    - A success message indicating the pump was primed.
    """
    if doser_id not in DOSER_GPIO_MAP:
        raise HTTPException(status_code=400, detail="Invalid doser ID.")
    
    ml = PRIMER_ML
    background_tasks.add_task(dose, doser_id, "Priming", ml)
    return PlainTextResponse(content=f"Sent command to prime {ml}mL on doser {doser_id}.", status_code=200)

@app.get("/dosing-report")
def get_dosing_report():
    """
    Get CSV dosing report as JSON

    Returns:
    - A JSON representation of the dosing report data.
    """
    # Check if file exists
    file_exists = os.path.isfile(csv_file)
    if not file_exists:
        raise HTTPException(status_code=404, detail="CSV file not found!")

    # Read and parse CSV file
    try:
        with open(csv_file, "r") as file:
            reader = csv.DictReader(file)
            csv_data = [row for row in reader]  # Convert CSV rows to list of dictionaries

        # Return the CSV content as JSON
        return JSONResponse(
            content=csv_data,
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")

@app.get("/jobs")
def list_obs():
    """
    Get Scheduled report

    Returns:
    - A JSON object showing next dose for each schedule.
    """
    try:
        # Fetch jobs from scheduler
        jobs = scheduler.get_jobs()
        job_data = [
            {
                "id": job.id,
                "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                if job.next_run_time else None
            }
            for job in jobs
        ]

        # Return as JSON response
        return JSONResponse(
            content=job_data,
            status_code=200
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving jobs: {str(e)}"
        )

# Shutdown scheduler on application shutdown
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)
