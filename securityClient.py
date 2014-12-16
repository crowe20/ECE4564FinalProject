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
import traceback 
import subprocess 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.utils import formataddr
sender = "ece4564finalproj@gmail.com"
configName = 'exampleConfig.txt'	#configuration file name sender = 'ece4564finalproj@gmail.com' 
senderUserName = 'ece4564finalproj' 
senderPassword = 'finalproj'

#setup log file for current execution
#InitialTime = time.time()
logName = 'log.txt'

LOGFORMAT= ('%(levelname)s,%(asctime)s,%(funcName)s,%(message)s')

LOGGER = logging.getLogger(__name__)

global nodesIP
nodesIP = {}	
global nodesPORT
nodesPORT = {}
global nodesUPDATETIME
nodesUPDATETIME = {}
global nodesARCHIVE
nodesARCHIVE = {}
global nodesARCHIVEFILE
nodesARCHIVEFILE = {}
global nodesThread
nodesThread = {}
global receivers		#list of email recipients
receivers =[]
global ArchiveFilePath
ArchiveFilePath = ''
global HostIP
HostIP = ''
global alertTimes
alertTimes = []
global numStreams
numStreams = 0

mutexNodeIP = threading.Lock()
mutexNodeThread = threading.Lock()
mutexArchive = threading.Lock()

class AsynchConsumer(object):

	EXCHANGENAME = 'msgexchange' #variable
	EXCHANGETYPE = 'fanout'
	QUEUENAME = 'messages' 	#variable
	#ROUTINGKEY

	def __init__(self):
		self.connection = None
		self._channel = None
		self.closing = False
		self.ConsumerTag = None
		self.host = 'netapps.ece.vt.edu'
		self.virtualhost = '/2014/fall/observer'
		self.user = 'observer'
		self.password = 'N1ght|visi0N44'
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
			ipaddr = msg[1].split(':')[0].strip()
			port = msg[1].split(':')[1].strip()
			status = msg[2].strip()
			if status == "Online":
				changeNode(name, ipaddr, port)	
			elif status == "Motion":
				LOGGER.info('Motion alert received from name = %s',name)
				archiveTrue(name)
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
					text = "motion occured at this node: {0}\n".format(name)
					global HostIP
					text = text+"view at: {0}:8080/{1}".format(HostIP,name)
					body = MIMEText(text,'plain')
					msg.attach(body)
					server = smtplib.SMTP('smtp.gmail.com:587')
					server.starttls()
					server.login(senderUserName,senderPassword)
					server.sendmail(sender, receivers, msg.as_string())
					server.quit()
				
			elif status == 'Stop':
				archiveFalse(name)

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
		t = time.time()
		mutexNodeIP.acquire()
		names = nodesUPDATETIME.keys()
		mutexNodeIP.release()
		for name in names:
			mutexNodeIP.acquire()
			lastUpdate = nodesUPDATETIME[name]
			mutexNodeIP.release()
			if t - lastUpdate >180:
				LOGGER.info('Node %s is inactive', name)
				deleteNode(name)

def sockets(name,ip, port):
	global ArchiveFilePath
	# streamFile needs to be updated with increasing port numbers
	currPort = 25700+numStreams
	streamDir = ArchiveFilePath+'nodes/'+name+'/current'
	streamFile = ArchiveFilePath+'nodes/'+name+'/current/stream'+str(currPort)+'.h264'
	streamName = "stream"+str(currPort)+'.h264'
	if not os.path.exists(streamDir):
		os.makedirs(streamDir)
	stream = open(streamFile,'wb')
	command = "vlc --intf dummy %s :sout=#rtp{sdp=rtsp://:%s/%s} vlc://quit &"%(streamFile, currPort,streamName)
	#subprocess.call(command, shell=True)
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((ip,int(port)))
		print "starting"
		while os.stat(streamFile).st_size < (2**21):
			data = sock.recv(2**21)
			stream.write(data)
		print "done"
		subprocess.call(command, shell=True)
		while 1:
			data = sock.recv(2**15)
			stream.write(data)
			if nodesARCHIVE[name]:
				mutexArchive.acquire()
				nodesARCHIVEFILE[name].write(data)
				mutexArchive.release()

		sock.close()
	except Exception, local_exception:
		LOGGER.info("Local error: "+local_exception.message)
		print "Local error: "+local_exception.message
		print traceback.format_exc()


def reloadConfig():
	configFile = open(configName, 'r')
	global HostIP
	HostIP = configFile.readline().strip().split(':')[1].strip()
	global ArchiveFilePath
	ArchiveFilePath = configFile.readline().strip()
	Times = configFile.readline().split(';')[1].strip().split('+')	
	configFile.close()
	
	global alertTimes
	alertTimes=[]
	for time in Times:
		time = time[1:-1].split(',')
		alertTimes.append(time)

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
		curr = hour*60 + min
		start = startTimehr*60 + startTimeMin
		end = endTimehr*60 + endTimeMin
#		print curr, start, end
		if day == testDay:
			if start <= curr and curr <= end:
				retVal = True
				break
	return retVal

def changeNode(name, ipaddr, port):
	mutexNodeIP.acquire()
	nodesUPDATETIME[name] = time.time()
	if name in nodesIP:
		oldIp = nodesIP[name]
		if oldIp != ipaddr:
			LOGGER.info('Node %s updated its IP address from %s to %s',name,oldIp,ipaddr)
			nodesIP[name] = ipaddr
			nodesPORT[name] = port
			deleteThread(name)
			global numStreams
			addThread(name,ipaddr,port)
			numStreams = numStreams+1
			archiveFalse(name)

	else:
		LOGGER.info('New Node detected, name = %s, IP = %s',name, ipaddr)
		nodesIP[name] = ipaddr
		nodesPORT[name] = port
		global numStreams
		addThread(name, ipaddr, port)
		numStreams = numStreams+1
		archiveFalse(name)

	mutexNodeIP.release()

def deleteNode(name):
	mutexNodeIP.acquire()
	del nodesUPDATETIME[name]
	del nodesIP[name]
	del nodesPORT[name]
	deleteThread(name)
	mutexNodeIP.release()

def addThread(name, ip, port):
	mutexNodeThread.acquire()
	t = threading.Thread(target=sockets, args=(name,ip, port))
	t.start()
	nodesThread[name] = t	
	mutexNodeThread.release()

def deleteThread(name):
	mutexNodeThread.acquire()
	t = nodesThread[name]
	t.exit()
	del nodesThread[name] 
	mutexNodeThread.release()	

def archiveFalse(name):
	mutexArchive.acquire()
	nodesARCHIVE[name] = False
	try:
		print "closing ArchiveFile"+str(nodesARCHIVEFILE[name])
		nodesARCHIVEFILE[name].close()
	except:
		print "failed to close file"
		print traceback.format_exc()
		pass
	mutexArchive.release()

def archiveTrue(name):
	mutexArchive.acquire()
	nodesARCHIVE[name] = True
	currTime = time.time()
	archiveName = datetime.datetime.fromtimestamp(currTime).strftime('%Y-%m-%d_%H%M%S') +'.h264'
	archivefileDir = ArchiveFilePath + 'nodes/'+name+'/archive/'
	print "creating file archiveName"
	if not os.path.exists(archivefileDir):
		os.makedirs(archivefileDir)
	archive = open(archivefileDir+archiveName,'wb')
	header1 = "\x00\x00\x00\x01\x27\x64\x00\x28\xac\x2b\x40\x50\x1e\xd0\x0f\x12"
	header2 = "\x26\xa0\x00\x00\x00\x01\x28\xee\x02\x5c\xb0\x00\x00\x00\x01\x25\x88\x80"
	archive.write(header1)
	archive.write(header2)
	print "file made Successfully"
	nodesARCHIVEFILE[name] = archive
	mutexArchive.release()

def archiveGet(name):
	mutexArchive.acquire()
	toReturn1 = nodesARCHIVE[name]
	toReturn2 = nodesARCHIVEFILE[name]
	mutexArchive.release()
	return (toReturn1, toReturn2)

def main():

	print "configuring security system"
	reloadConfig()
	print "done Configuring"
	logging.basicConfig(filename = ArchiveFilePath+'log.txt', level=logging.INFO,format=LOGFORMAT)
	print "launching AMQP Thread"
	t1 = threading.Thread(target=asynchAMQP)
	t1.start()
	print "launched"
	print "launching Timet Thread"
	t2 = threading.Thread(target=timer)
	t2.start()
	print "launched"
	

if __name__=='__main__':

	main()
