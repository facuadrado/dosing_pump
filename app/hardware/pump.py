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
    def __init__(self, sqlite_client):
        GPIO.setmode(GPIO.BCM)
        for head in PUMP_HEADS.values():
            GPIO.setup(head.pin_1, GPIO.OUT)
            GPIO.setup(head.pin_2, GPIO.OUT)
        self.sqlite_client = sqlite_client

    def dose(self, head_id: int, mode: str, ml: float):
        head = PUMP_HEADS[head_id]
        seconds = ml / head.calibration_ml_per_second

        GPIO.output(head.pin_1, GPIO.LOW)
        GPIO.output(head.pin_2, GPIO.HIGH)
        time.sleep(seconds)

        GPIO.output(head.pin_1, GPIO.LOW)
        GPIO.output(head.pin_2, GPIO.LOW)

        self.sqlite_client.insert_raw_entry(head_id, ml, mode)
        self.sqlite_client.insert_entry(head_id, ml)
        self.sqlite_client.update_remaining(head_id, ml)