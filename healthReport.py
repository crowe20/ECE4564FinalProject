##########################################################################
#
# This script will be called every minute by the cron daemon.
# It will send minutely messages to the Client to esnure that the Node
# is still online and still functioning properly.
#
##########################################################################

import pika

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

#publish a health message
channel.basic_publish(exchange="chat_room",
                      routing_key='',
                      body="Node1,1.2.3.4,Online")

#close broker and exit
msg_broker.close()
