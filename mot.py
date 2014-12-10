import RPi.GPIO as GPIO
import time

sensorPin = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensorPin, GPIO.IN)

prevState = False
currState = False

time.sleep(10)

print "start"

while True:
    time.sleep(2)
    currState = GPIO.input(sensorPin)
    if not prevState and currState:
        print "Motion was detected"
    prevState = currState
