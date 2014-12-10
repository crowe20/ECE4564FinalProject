import socket

f = open("/home/pi/ECE4564/FinalProj/testCode/webserver/files/vid.h264","ab")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("node1.local",50000))

try:
	while True:
		data = s.recv(1024)
		if not data:
			break
		f.write(data)
finally:
	s.close()
	f.close()
