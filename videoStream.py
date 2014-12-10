import socket
import time
import picamera

host = ''
port = 50000

with picamera.PiCamera() as camera:
    camera.resolution = (640, 480)
    camera.framerate = 24

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host,port))
    sock.listen(0)

    connection = sock.accept()[0].makefile('wb')

    try:
        camera.start_recording(connection, format='h264')
        camera.wait_recording(10)
        camera.stop_recording()
    finally:
        connection.close()
        sock.close()
        camera.close() #get rid of if causing problems
