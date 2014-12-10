__author__ = 'Robert'

import os, sys
import server.py

def webserver():
    """Launch webserver"""
    server.server_main()

def client():
    """Launch client"""
    #CHRIS call client main function here

def __main__():
    #create second process
    pipein, pipeout = os.pipe()
    serverpid = os.fork()

    #pipe stdout of new process to stdin of original

    if serverpid == 0:
        clientpid = os.fork()
        if clientpid == 0:
            os.dup2(pipeout, sys.stdin)
            client()
        else:
            os.dup2(pipein, sys.stdout)
            webserver()
    else:
        while True:
            if raw_input("Enter q to stop.") =='q':
                break

__main__()