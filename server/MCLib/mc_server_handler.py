from time import time
from sys import stdout
from mc_server import Server
from mc_server_commander import ServerCommander
import re
import json

class ServerHandler():
    SAVE_INTERVAL = 15 * 60
    WARNING_TIME = 60
    CMD_PATTERN = r'^\[(?:\d{2}:){2}\d{2}\] \[.*\]: <(.*)> (.*)$'
    COMMANDS_FILE = 'commands.json'
    def __init__(self, server = None):
        if server:
            if type(server) != Server:
                raise TypeError
            self.server = server
        else:
            self.server = Server()
        self.lastSave = 0

        self.commander = ServerCommander(self.server)

        self.COMMANDS = {}
        cmd_data = json.load(open(self.COMMANDS_FILE))
        for cmd, obj in cmd_data['weather']:
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.commander.changeWeatherTo
        for cmd, obj in cmd_data['time']:
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.commander.changeTimeTo
        for cmd, obj in cmd_data['control']:
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.serverControlCmd
        for cmd, obj in cmd_data['player']:
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.commander.playerCmd

    def printFlush(self, line):
        self.printLine('>>> {}'.format(line))

    def printLine(self, line):
        print(line)
        stdout.flush()

    def serverControlCmd(self, player, args):
        lowCmd = args[0].lower()
        if lowCmd == 'restart':
            self.restartServer()
        elif lowCmd == 'save':
            self.saveServer()

    def restartServer(self):
        self.server.restart(self.WARNING_TIME)

    def saveServer(self):
        self.printFlush("Saving server...")
        self.server.save()
        self.lastSave = time()

    def handleCommand(self, player, cmd):
        self.printFlush('Handling command: {}'.format(cmd))
        args = cmd.split(' ')
        func = None
        try:
            func = self.COMMANDS[args[0]]['func']
        except KeyError:
            msg = "Function '{}' not found!".format(args[0])
            self.server.message(player, msg)
            self.printFlush(msg)
            return
        if self.COMMANDS[args[0]]['admin'] and !self.server.isAdmin(player):
            self.server.message(player, "You don't have access to that command!")
            return
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

