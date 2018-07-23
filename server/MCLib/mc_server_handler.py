from subprocess import Popen, PIPE, STDOUT
from time import sleep, time
from datetime import date
from sys import stdout, exit
from mc_server import Server
import signal
import re

class ServerHandler():
    SAVE_INTERVAL = 15 * 60
    WARNING_TIME = 60
    CMD_PATTERN = r'^\[(?:\d{2}:){2}\d{2}\] \[.*\]: <(.*)> (.*)$'
    DEBUG_LOG = 'debug_log.txt'
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
                'noon': {
                    'func': self.changeTimeTo,
                    'desc': '!noon: Sets the time to noon'
                }
                'midnight': {
                    'func': self.changeTimeTo,
                    'desc': '!midnight: Sets the time to midnight'
                }
                'help': {
                    'func': self.sendHelp,
                    'desc': '!help: Displays this help message'
                }
        }

    def printFlush(self, line):
        self.printLine('>>> {}'.format(line))

    def printLine(self, line):
        print(line)
        stdout.flush()
        with open(self.DEBUG_LOG, 'a') as f:
            f.write(line + '\n')

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
        self.server.restart(self.WARNING_TIME)
    def restartServerCmd(self, player, args):
        self.restartServer()

    def saveServer(self):
        self.printFlush("Saving server...")
        self.server.save()
        self.lastSave = time()
    def saveServerCmd(self, player, args):
        self.saveServer()

    def handleCommand(self, player, cmd):
        self.printFlush('Handling command: {}'.format(cmd))
        if not self.server.isAdmin(player):
            self.server.message(player, "You don't have access to that command!")
            return

        args = cmd.split(' ')
        try:
            func = self.COMMANDS[args[0]]['func']
        except KeyError:
            msg = "Function '{}' not found!".format(args[0])
            self.server.message(player, msg)
            self.printFlush(msg)
        else:
            func(player, args)

    def saveNeeded(self):
        if time() > (self.lastSave + self.SAVE_INTERVAL):
            return True
        return False

    def routine(self):
        while True:
            if self.server.restartNeeded():
                self.restartServer()
            if self.saveNeeded():
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
        self.printFlush("Starting server...")
        self.server.start()
        self.printFlush("Server started...")
        self.lastSave = time()
        self.routine()

    def stopServer(self):
        self.printFlush("Stopping server...")
        self.server.stop()
        self.server = None

