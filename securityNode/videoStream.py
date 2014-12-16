import socket
import time
import picamera

host = ''
port = 12894

with picamera.PiCamera() as camera:
    camera.resolution = (640, 480)
    camera.framerate = 24
    camera.vflip = True
    camera.hflip = True

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host,port))
    sock.listen(0)

    connection = sock.accept()[0].makefile('wb')

    camera.start_recording(connection, format='h264')

    while 1:
        camera.wait_recording(60)
