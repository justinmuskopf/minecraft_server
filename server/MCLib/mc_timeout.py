from threading import Timer
from time import sleep
from signal import signal, SIGALRM, alarm

class TimeoutSignal(Exception):
    @staticmethod
    def timeout_handler(signum, frame):
        raise TimeoutSignal

    @staticmethod
    def timeout(time):
        timeout = 10
        if time > 0:
            timeout = time
        alarm(timeout)

    @staticmethod
    def reset():
        alarm(0)

signal(SIGALRM, TimeoutSignal.timeout_handler)

"""

class TimeoutSignal(Exception):
    DEFAULT_TIMEOUT = 10
    
    def __init__(self, t = 0):
        self.timer = None
        if t > 0:
            self.DEFAULT_TIMEOUT = t

    def timeout_handler(self):
        raise TimeoutSignal

    def reset(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

    def timeout(self, t = 0):
        if self.timer:
            self.reset()

        timeout = self.DEFAULT_TIMEOUT
        if t > 0:
            timeout = t
        self.timer = Timer(timeout, self.timeout_handler)
        self.timer.start()
"""
