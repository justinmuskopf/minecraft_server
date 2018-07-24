from subprocess import Popen, PIPE, STDOUT
from sys import stdout, exit
from MCLib import ServerHandler

DEBUG_LOG = 'debug_log.txt'

def main(handler):
    handler.startServer()

if __name__ == "__main__":
    check = Popen(['netstat', '-lnp'], stdout = PIPE, stderr = PIPE)
    out, err = check.communicate()
    if 'java' in out and '25565' in out:
        print("Server already running... Exiting")
        exit(0)
    
    handler = ServerHandler()
    try:
        main(handler)
    except KeyboardInterrupt:
        handler.stopServer()
        exit(0)
