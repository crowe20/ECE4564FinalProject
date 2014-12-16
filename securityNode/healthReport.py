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
                              virtual_host="/2014/fall/observer",
                              credentials=pika.PlainCredentials("observer",
                                                                "N1ght|visi0N44",
                                                                True)))

#create the channel to be used
channel = msg_broker.channel()
channel.exchange_declare(exchange="msgexchange",
                         type="fanout")

#publish a health message specific to this node
#contains IP address of node as well as an arbitrary socket
#that its video server is listening on
channel.basic_publish(exchange="msgexchange",
                      routing_key='',
                      body="Node1,192.168.1.61:12894,Online")

#close broker and exit
msg_broker.close()
