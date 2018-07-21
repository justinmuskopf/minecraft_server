from subprocess import Popen, PIPE, STDOUT
from time import sleep, time
from datetime import date
from sys import stdout, exit
import signal
import re

def printFlush(msg):
    print('>>> ' + msg)
    stdout.flush()

class Server:

    ADMINS = [
        'KILA_GODZ',
        'iLikeYoBraids'
    ]

    def __init__(self):
        self.today = date.today()
        self.WAIT_FOR_STARTED = 5
        self.CMD = ['java', '-Xmx2048m', '-Xms1024m', '-jar', 'server.jar', 'nogui']
        self.CMD_WAIT = 3
        self.process = None

    def restartNeeded(self):
        if date.today() != self.today:
            return True
        return False

    def writeToProcess(self, msg):
        self.process.stdin.write(msg + "\n")

    def say(self, msg):
        self.writeToProcess("say {}".format(msg))

    def save(self):
        self.say("Saving Server...")
        self.writeToProcess("save-all")

    def stop(self):
        if not self.process:
            return
        
        self.save()
        sleep(self.CMD_WAIT)
            
        stdout = self.process.communicate("stop\n")[0]
        print stdout
        sleep(self.CMD_WAIT)
        self.process = None

    def changeWeather(self, weather):
        self.writeToProcess("weather {}".format(weather))

    def changeTime(self, time):
        self.writeToProcess("time set {}".format(time))

    def teleport(self, player):
        pass
    
    def message(self, player, msg):
        self.writeToProcess("tell {} {}".format(player, msg))

    def start(self):
        self.today = date.today()
        self.process = Popen(self.CMD, stdin = PIPE, stdout = PIPE, stderr = STDOUT)
        sleep(self.WAIT_FOR_STARTED)

    def restart(self, warnTime = 0):
        if warnTime > 0:
            self.say("Restarting Server in {} seconds!".format(self.WARNING_TIME))
            sleep(self.WARNING_TIME)
        self.stop()
        self.start()

    def readLine(self):
        return self.process.stdout.readline().strip()

    def isAdmin(self, player):
        if player in self.ADMINS:
            return True
        return False

class ServerHandler():
    SAVE_INTERVAL = 15 * 60
    WARNING_TIME = 60
    CMD_PATTERN = r'^\[(?:\d{2}:){2}\d{2}\] \[.*\]: <(.*)> (.*)$'
    def __init__(self, server = None):
        if server:
            if type(server) != Server:
                raise TypeError
            self.server = server
        else:
            self.server = Server()
        self.lastSave = 0
        self.COMMANDS = {
                'clear': {
                    'func': self.changeWeatherTo,
                    'desc': '!clear: Changes the weather to clear'
                },
                'rain': {
                    'func': self.changeWeatherTo,
                    'desc': '!rain: Changes the weather to raining'
                },
                'thunder': {
                    'func': self.changeWeatherTo,
                    'desc': '!thunder: Changes the weather to thunderstorming'
                },
                'restart': {
                    'func': self.restartServerCmd,
                    'desc': '!restart: Saves and restarts the server'
                },
                'save': {
                    'func': self.saveServerCmd,
                    'desc': '!save: Saves the server'
                },
                'day': {
                    'func': self.changeTimeTo,
                    'desc': '!day: Sets the time to day time'
                },
                'night': {
                    'func': self.changeTimeTo,
                    'desc': '!night: Sets the time to night time'
                },
                'help': {
                    'func': self.sendHelp,
                    'desc': '!help: Displays this help message'
                }
        }


    def printLine(self, line):
        print(line)
        stdout.flush()

    def changeWeatherTo(self, player, args):
        self.server.changeWeather(args[0])

    def changeTimeTo(self, player, args):
        self.server.changeTime(args[0])

    def sendHelp(self, player, args):
        if len(args) > 1:
            helpStr = ""
            try:
                helpStr = self.COMMANDS[args[1]]['desc']
            except KeyError:
                self.server.say("help: No such function '{}' found".format(args[1]))
            else:
                self.server.say(helpStr)
        else:
            for k, cmd in self.COMMANDS.iteritems():
                self.server.say(cmd['desc'])

    def restartServer(self):
        self.server.restart()
    def restartServerCmd(self, player, args):
        self.restartServer()

    def saveServer(self):
        printFlush("Saving server...")
        self.server.save()
        self.lastSave = time()
    def saveServerCmd(self, player, args):
        self.saveServer()

    def handleCommand(self, player, cmd):
        if not self.server.isAdmin(player):
            self.server.message(player, "You don't have access to that command!")
            return

        args = cmd.split(' ')
        try:
            func = self.COMMANDS[args[0]]['func']
        except KeyError:
            msg = "Function '{}' not found!".format(args[0])
            self.server.message(player, msg)
            printFlush(msg)
        else:
            func(player, args)

    def routine(self):
        while True:
            if self.server.restartNeeded():
                self.restartServer()
            if time() > (self.lastSave + self.SAVE_INTERVAL):
                self.saveServer()

            line = self.server.readLine()
            if not line:
                continue

            self.printLine(line)
            match = re.match(self.CMD_PATTERN, line)
            if match:
                player, cmd = match.group(1, 2)
                if cmd and cmd[0] == '!':
                    self.handleCommand(player, cmd[1:].lower())

    def startServer(self):
        printFlush("Starting server...")
        self.server.start()
        printFlush("Server started...")
        self.lastSave = time()
        self.routine()

    def stopServer(self):
        printFlush("Stopping server...")
        self.server.stop()
        self.server = None

def main(handler):
    handler.startServer()

if __name__ == "__main__":
 
    check = Popen(['netstat', '-lnp'], stdout = PIPE, stderr = PIPE)
    out, err = check.communicate()
    if 'java' in out and '25565' in out:
        printFlush("Server already running... Exiting")
        exit(0)
    
    handler = ServerHandler()
    try:
        main(handler)
    except KeyboardInterrupt:
        handler.stopServer()
        exit(0)
