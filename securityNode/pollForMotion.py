##########################################################################
#
#Constantly poll a gpio pin, waiting for it to go high.
#When it does, send a message via amqp saying motion is detected
#
##########################################################################

import pika
import RPi.GPIO as GPIO
import time

sensorPin = 23 #gpio pin on pi to poll

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensorPin, GPIO.IN)

currState = False

prev = False
motion = 0
still = 0

time.sleep(5) #let motion detector stabalize

#connect to the message broker and login
msg_broker = pika.BlockingConnection(
    pika.ConnectionParameters(host="netapps.ece.vt.edu",
                              virtual_host="/2014/fall/observer",
                              credentials=pika.PlainCredentials("observer",
                                                                "N1ght|visi0N44",
                                                                True)))

#create the channel to be used
channel = msg_broker.channel()
channel.exchange_declare(exchange="msgexchange",
                         type="fanout")


try:
    while True:
        time.sleep(2)
        currState = GPIO.input(sensorPin)
        if currState:
            motion += 1
            still = 0
        else:
            still += 1
            motion = 0
        if motion == 1 and not prev:
            channel.basic_publish(exchange="msgexchange",
                          routing_key='',
                          body="Node1,192.168.1.61:12894,Motion")
            print "Started"
            prev = True
        if still == 10 and prev:
            channel.basic_publish(exchange="msgexchange",
                          routing_key='',
                          body="Node1,192.168.1.61:12894,Stop")
            print "Stopped"
            prev = False
finally:
    #close broker and exit
    msg_broker.close()
