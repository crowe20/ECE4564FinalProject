##########################################################################
#
#Constantly poll a gpio pin, waiting for it to go high.
#When it does, send a message via amqp saying motion is detected
#
##########################################################################

import pika
import RPi.GPIO as GPIO
import time

sensorPin = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensorPin, GPIO.IN)

prevState = False
currState = False

time.sleep(5)

#connect to the message broker and login
msg_broker = pika.BlockingConnection(
    pika.ConnectionParameters(host="netapps.ece.vt.edu",
                              virtual_host="sandbox",
                              credentials=pika.PlainCredentials("ECE4564-Fall2014",
                                                                "13ac0N!",
                                                                True)))

#create the channel to be used
channel = msg_broker.channel()
channel.exchange_declare(exchange="chat_room",
                         type="fanout")

try:
    while True:
        time.sleep(2)
        currState = GPIO.input(sensorPin)
        if not prevState and currState:
            channel.basic_publish(exchange="chat_room",
                          routing_key='',
                          body="node1,10.0.0.18,Motion")
            time.sleep(60)
        prevState = currState
finally:
    #close broker and exit
    msg_broker.close()
