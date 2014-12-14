import pika	#INSTALLED LIBRARY
import logging
import time
import threading
import datetime
import socket
import sys
import readline
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

configName = 'exampleConfig.txt'	#configuration file name
sender = 'ece4564finalproj@gmail.com'
senderUserName = 'ece4564finalproj'
senderPassword = 'finalproj'

#setup log file for current execution
InitialTime = time.time()
InitialTimeString = datetime.datetime.fromtimestamp(InitialTime).strftime('%Y-%m-%d_%H%M%S') +'.log'

LOGFORMAT= ('%(levelname)s,%(asctime)s,%(funcName)s,%(message)s')

LOGGER = logging.getLogger(__name__)

nodesIP = {}	
nodesUPDATETIME = {}
receivers = []		#list of email recipients
ArchiveFilePath = ''
alertTimes = []

class AsynchConsumer(object):

	EXCHANGENAME = 'chat_room' #variable
	EXCHANGETYPE = 'fanout'
	QUEUENAME = 'text' 	#variable
	#ROUTINGKEY

	def __init__(self):
		self.connection = None
		self._channel = None
		self.closing = False
		self.ConsumerTag = None
		self.host = 'netapps.ece.vt.edu'
		self.virtualhost = 'sandbox'
		self.user = 'ECE4564-Fall2014'
		self.password = '13ac0N!'
	def connect(self):
		LOGGER.info('Connecting to %s',self.host)	
		return pika.SelectConnection(pika.ConnectionParameters(host=self.host,
                              						virtual_host=self.virtualhost,
                              						credentials=pika.PlainCredentials(self.user,
                                                               						self.password,
                                                                					True)),
						self.on_connection_open,
						stop_ioloop_on_close=False)
	def close_connection(self):
		
		LOGGER.info('Closing Connection')
		self.connection.close()

	def add_on_connection_close_callback(self):
		
		LOGGER.info('Adding connection close callback')
		self.connection.add_on_close_callback(self.on_connection_closed)

	def on_connection_closed(self,connection, replyCode, replyText):
		
		self._channel = None
		if self.closing:
			self.connection.ioloop.stop()
		else:
			LOGGER.warning('Connection closed, reopening ins 5 seconds: (%s) %s',
					replyCode, replyText)
			self.connection.add_timeout(5,self.reconnect)

	def on_connection_open(self, unused_connection):
		
		LOGGER.info('Connection Opened')
		self.add_on_connection_close_callback()
		self.open_channel()

	def reconnect(self):
		
		self.connection.ioloop.stop()

		if not self.closing:
			self.connection = self.connect()
			self.connection.ioloop.start()

	def add_on_channel_close_callback(self):

		LOGGER.info('Adding channel close callback')
		self._channel.add_on_close_callback(self.on_channel_closed)

	def on_channel_closed(self, channel, replyCode, replyText):
		
		LOGGER.warning('Channel %i was closed: (%s) %s',
				channel, replyCode, replyText)
		self.connection.close()

	def on_channel_open(self, newchannel):

		LOGGER.info('Channel opened')
		self._channel = newchannel
		self.add_on_channel_close_callback()
		self.setup_exchange(self.EXCHANGENAME)

	def setup_exchange(self, exchangeName):
		
		LOGGER.info('Declaring exchange %s',exchangeName)
		self._channel.exchange_declare(self.on_exchange_declareok,
						exchangeName,
						self.EXCHANGETYPE)

	def on_exchange_declareok(self, unusedFrame):
		
		LOGGER.info('Exchange Declared')
		self.setup_queue(self.QUEUENAME)

	def setup_queue(self, queueName):
	
		LOGGER.info('Declaring Queue %s',queueName)
		self._channel.queue_declare(self.on_queue_declareok, queueName)

	def on_queue_declareok(self, methodFrame):

		LOGGER.info('Binding %s to %s',self.EXCHANGENAME, self.QUEUENAME)
		self._channel.queue_bind(self.on_bindok,self.QUEUENAME,self.EXCHANGENAME)
		
	def add_on_cancel_callback(self):
		
		LOGGER.info('Adding Consumer cancellation callback')
		self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

	def on_consumer_cancelled(self, method_frame):
		
		LOGGER.info('Consumer was cancelled remotely, shutting down: %r', method_frame)
		if self._channel:
			self._channel.close()

	def acknowledge_message(self, deliveryTag):
		
		LOGGER.info('Acknowledge message %s', deliveryTag)
		self._channel.basic_ack(deliveryTag)


	def on_message(self,unused_channel,basic_deliver,properties,body):
		
		LOGGER.info('Received message # %s from %s: %s', basic_deliver.delivery_tag,properties.app_id,body)
		#THIS IS WHERE WE MANIPULATE MESSAGES
		#output(body)
		msg = body.split(',')
		if( len(msg)!=3):
			print 'Bad Message'
		else:
			name = msg[0]
			ipaddr = msg[1]
			status = msg[2]
			if status == "Online":
				nodesUPDATETIME[name] = time.time()
				if name in nodesIP:
					oldIp = nodesIP[name]
					if oldIp != ipaddr:
						LOGGER.info('Node %s updated its IP address from %s to %s',name,oldIp,ipaddr)
						nodesIP[name] = ipaddr
				else:
					LOGGER.info('New Node detected, name = %s, IP = %s',name, ipaddr)
					nodesIP[name] = ipaddr
					
			elif status == "Motion":
				LOGGER.info('Motion alert received from name = %s',name)
				#send email alert
				if not inRange():
					configFile = open(configName,'r')
					for i in range(3):
					#skip to lines of file needed
						configFile.readline()
					receivers = []
					names = []
					for entry in configFile:
						if entry[0] == '#':
							pass
						else:
							entry = entry.split(',')
							receivers.append(entry[0].strip())
							names.append(entry[1])
					configFile.close()
					#print receivers
					#print names
					msg = MIMEMultipart()
					msg['From'] = formataddr(('SYSTEM ADMINISTRATOR',sender))
					for i in range(len(names)):
						msg['To'] = formataddr((names[i],receivers[i]))
					msg['Subject'] = "MOTION ALERT"
					text = "motion occured at this node: {0}".format(name)
					body = MIMEText(text,'plain')
					msg.attach(body)
					server = smtplib.SMTP('smtp.gmail.com:587')
					server.starttls()
					server.login(senderUserName,senderPassword)
					server.sendmail(sender, receivers, msg.as_string())
					server.quit()

		self.acknowledge_message(basic_deliver.delivery_tag)
	
	def on_cancelok(self,unused_frame):
		
		LOGGER.info('RabbitMQ acknowledged the cancellation of the consumer')
		self.close_channel()
	
	def stop_consuming(self):

		if self._channel:
			LOGGER.info('sending a Basic.Cancel RPC command to RabbitMQ')
			self._channel.basic_cancel(self.on_cancelok,self.ConsumerTag)

	def start_consuming(self):
	
		LOGGER.info('Issuing consumer related RPC commands')
		self.ConsumerTag=self._channel.basic_consume(self.on_message, self.QUEUENAME)

	def on_bindok(self, unused_frame):
	
		LOGGER.info('Queue bound')
		self.start_consuming()

	def close_channel(self):

		LOGGER.info('Closing Channel')
		self._channel.close()

	def open_channel(self):
		
		LOGGER.info('Creating New Channel')
		self.connection.channel(on_open_callback=self.on_channel_open)

	def run(self):
	
		self.connection = self.connect()
		self.connection.ioloop.start()
		
	def stop(self):

		LOGGER.info('Stopping')
		self.closing = True
		self.stop_consuming()
		self.connection.ioloop.start()
		LOGGER.info('Stopped')

def asynchAMQP():
	
	example = AsynchConsumer()
	
	try:
		example.run()
	except KeyboardInterrupt:
		example.stop()

def timer():
	i=0
	while True:
		time.sleep(15.0)
		#LOGGER.info('%s',i)
		t = time.time()
		#TimeString = datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d_%H%M%S')
		#print(TimeString)
		names = nodesUPDATETIME.keys()
		for name in names:
			lastUpdate = nodesUPDATETIME[name]
			if t - lastUpdate >180:
				LOGGER.info('Node %s is inactive', name)
				del nodesUPDATETIME[name]
				del nodesIP[name]

def sockets(data):
	if data:
		host = "node1.local"
		port = 50000
		#filename ="/home/pi/ECE4564/FinalProj/testCode/webserver/files/node/{1}/"
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((host,port))
			data = sock.recv(4096)
			print data
			sock.close()
		except Exception, local_exception:
			LOGGER.info("Local error: "+local_exception.message)
			print "Local error: "+local_exception.message


def reloadConfig():
	configFile = open(configName, 'r')
	configFile.readline()
	ArchiveFilePath = configFile.readline().strip()
	Times = configFile.readline().split(';')[1].strip().split('+')	
	configFile.close()
	
	#print Times
	global alertTimes
	alertTimes=[]
	for time in Times:
		time = time[1:-1].split(',')
		alertTimes.append(time)
	 
	#	print time
	#test = open(os.path.join(ArchiveFilePath,'test.txt'),'w')
	#test.write('test')

def inRange():
	#print 'inRangeFunctionCalled'
	retVal = False
	day = datetime.datetime.now().strftime('%A').lower()
	hour = int(datetime.datetime.now().hour)
#	hour = 22
	min = int(datetime.datetime.now().minute)
#	min = 00
	#print "entering loop"
	global alertTimes
	#print alertTimes
	for time in alertTimes:
	#	print time
		testDay = time[0].lower()
		startTime = datetime.datetime.strptime(time[1].strip(),'%H:%M')
		endTime = datetime.datetime.strptime(time[2].strip(),'%H:%M')
		
		startTimehr = int(startTime.strftime('%H'))
		startTimeMin = int(startTime.strftime('%M'))
		
		endTimehr = int(endTime.strftime('%H'))
		endTimeMin = int(endTime.strftime('%M'))
#		print day, testDay
#		print hour, min
#		print startTimehr, startTimeMin
#		print endTimehr, endTimeMin
		if day == testDay:
			
			if startTimehr == hour and startTimeMin <= min:
				if endTimehr == hour and endTimeMin >= min:
					retVal = True
					break
				elif endTimehr > hour:
					retVal = True
					break
			if startTimehr < hour and endTimehr > hour:
				retVal = True
				break
			if endTimehr == hour and endTimeMin >= min:
				if startTimehr == hour and startTimeMin <= min:
					retVal = True
					break 	
				elif startTimehr < hour:
					retVal = True
					break
	return retVal

def main():

	print "configuring security system"
	reloadConfig()
	print "done Configuring"
#	test = inRange()
#	if test:
#		print "inRange"
	logging.basicConfig(filename = InitialTimeString, level=logging.INFO,format=LOGFORMAT)
	t1 = threading.Thread(target=asynchAMQP)
	t1.start()
#	t2 = threading.Thread(target=timer)
#	t2.start()

	

if __name__=='__main__':

	main()
