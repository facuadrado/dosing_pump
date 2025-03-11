from fastapi import FastAPI, HTTPException, Response, BackgroundTasks
from apscheduler.schedulers.background import BackgroundScheduler
import RPi.GPIO as GPIO
import time
import os
import csv
from datetime import datetime

# CSV Dosing Data
SAVE_DIRECTORY = "/mnt"
FILE_NAME = "doser_data.csv"
HEADER = ["Date", "Time", "ml", "Mode"]
csv_file = os.path.join(SAVE_DIRECTORY, FILE_NAME)

# Raspberry Pi PIN declarations
DOSER_PIN_1 = 17
DOSER_PIN_2 = 22

# Initializing GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DOSER_PIN_1, GPIO.OUT)
GPIO.setup(DOSER_PIN_2, GPIO.OUT)

DAILY_SCHEDULED_DOSE = 6
FLOW_RATE_ML_PER_SECOND = 1

def record_data_csv(mode: str, ml: float):
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    time_string = now.strftime("%H:%M:%S")
    
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            writer.writerow(HEADER)
        writer.writerow([date_string, time_string, ml, mode])

def dose(mode: str, ml: float):
    seconds = ml / FLOW_RATE_ML_PER_SECOND
    
    GPIO.output(DOSER_PIN_1, GPIO.LOW)
    GPIO.output(DOSER_PIN_2, GPIO.HIGH)
    time.sleep(seconds)
    GPIO.output(DOSER_PIN_1, GPIO.LOW)
    GPIO.output(DOSER_PIN_2, GPIO.LOW)
    
    record_data_csv(mode, ml)

scheduler = BackgroundScheduler()
scheduler.add_job(record_data_csv, args=["Scheduled", DAILY_SCHEDULED_DOSE/24], trigger='interval', hours=1, id='scheduled_dose')
scheduler.start()

app = FastAPI()

# Endpoint to manually dose for x mL
@app.get("/doser/dose")
async def send_dose_task(ml: float, background_tasks: BackgroundTasks):
    """
    Manually start the dosing process for a specific amount of mL.
    
    Args:
    - mL: The amount of mL the pump will dose.
    
    Returns:
    - A success message with the amount of liquid in (mL).
    """
    UPPER_LIMIT = 10
    if not (0 < ml < UPPER_LIMIT):
        raise HTTPException(status_code=400, 
                            detail=f"Invalid dosing amount. Must be greater than 0mL and smaller/equal to {UPPER_LIMIT}mL."
                            )
    background_tasks.add_task(dose, "Manual", ml)
    return {"message": f"Sent dose command for {ml} mL."}

# Endpoint to stop the doser manually
@app.get("/doser/prime")
async def send_prime_task(background_tasks: BackgroundTasks):
    """
    Prime the pump by running it for 5 seconds to get the liquid flowing.
    
    Returns:
    - A success message indicating the pump was primed.
    """
    seconds = 5
    ml = seconds * FLOW_RATE_ML_PER_SECOND
    background_tasks.add_task(dose, "Priming", ml)
    return {"message": f"Sent command to prime for {seconds} seconds."}

# Endpoint to get dosing report
@app.get("/dosing-report")
def get_dosing_report():
    """
    Get CSV dosing report
    
    Returns:
    - A plain text with the dosing report data.
    """
    # Check if file exists
    file_exists = os.path.isfile(csv_file)
    if not file_exists:
        raise HTTPException(status_code=404, detail="CSV file not found!")

    # Read CSV file
    with open(csv_file, "r") as file:
        csv_content = file.read()
    
    # Return the CSV content as plain text
    return Response(status_code=200, content=csv_content, media_type="text/csv")

# Shutdown scheduler on application shutdown
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)
