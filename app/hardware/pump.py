from dataclasses import dataclass
import RPi.GPIO as GPIO
import time

@dataclass(frozen=True)
class PumpHead:
    pin_1: int
    pin_2: int
    calibration_ml_per_second: float

PUMP_HEADS = {
    1: PumpHead(pin_1=17, pin_2=22, calibration_ml_per_second=1.40),
    2: PumpHead(pin_1=23, pin_2=24, calibration_ml_per_second=1.34)
}

class Pump:
    def __init__(self, doseing_db_client):
        GPIO.setmode(GPIO.BCM)
        for head in PUMP_HEADS.values():
            GPIO.setup(head.pin_1, GPIO.OUT)
            GPIO.setup(head.pin_2, GPIO.OUT)
        self.db = doseing_db_client

    def dose(self, doser_id: int, mode: str, ml: float):
        head = PUMP_HEADS[doser_id]
        seconds = ml / head.calibration_ml_per_second

        GPIO.output(head.pin_1, GPIO.LOW)
        GPIO.output(head.pin_2, GPIO.HIGH)
        time.sleep(seconds)

        GPIO.output(head.pin_1, GPIO.LOW)
        GPIO.output(head.pin_2, GPIO.LOW)

        self.db.insert_entry(doser_id, ml, mode)