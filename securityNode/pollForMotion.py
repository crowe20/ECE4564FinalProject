##########################################################################
#
#Constantly poll a gpio pin, waiting for it to go high.
#When it does, send a message via amqp saying motion is detected
#
#After 20 seconds of no motion, send a message via amqp saying that
#there is no longer any motion in the room
#
##########################################################################

import pika
import RPi.GPIO as GPIO
import time

sensorPin = 23 #gpio pin on pi to poll

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensorPin, GPIO.IN)

#initial declarations
currState = False
prev = False

#cycle counters
motion = 0
still = 0

time.sleep(60) #let motion detector stabalize and server get running

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
        currState = GPIO.input(sensorPin) #read pin
        if currState:     		  #motion has been detected
            motion += 1   		  #increment motion cycle counter
            still = 0     		  #reset still cycle counter
        else:
            still += 1    		  #increment still cycle counter
            motion = 0    		  #reset motion cycle counter
        if motion == 1 and not prev:      #publish single motion message
            channel.basic_publish(exchange="msgexchange",
                          routing_key='',
                          body="Node1,192.168.1.61:12894,Motion")
            prev = True
        if still == 10 and prev:         #publish stop method
            channel.basic_publish(exchange="msgexchange",
                          routing_key='',
                          body="Node1,192.168.1.61:12894,Stop")
            prev = False
finally:
    #close broker and exit
    msg_broker.close()
