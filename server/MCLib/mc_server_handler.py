from time import time
from sys import stdout, path
from mc_server import Server
from mc_server_commander import ServerCommander
from os import getenv
import re
import json

class ServerHandler():
    SAVE_INTERVAL = 15 * 60
    WARNING_TIME = 60
    CMD_PATTERN = r'^\[(?:\d{2}:){2}\d{2}\] \[.*\]: <(.*)> (.*)$'
    COMMANDS_FILE = '{}/commands.json'.format(path[0])
    SHOULD_RUN_VAR = "MC_SVR_SHOULD_RUN"
    def __init__(self, server = None):
        if server:
            self.server = server
        else:
            self.server = Server()
        self.lastSave = 0

        self.commander = ServerCommander(self.server)
        self.COMMANDS = {}
        syntaxSet = {}
        desc = []
        
        cmd_data = json.load(open(self.COMMANDS_FILE))
        for cmd, obj in cmd_data['weather'].iteritems():
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.commander.changeWeatherTo
            syntaxSet[cmd] = obj['syntax']
            desc.append(obj['desc'])
        for cmd, obj in cmd_data['time'].iteritems():
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.commander.changeTimeTo
            syntaxSet[cmd] = obj['syntax']
            desc.append(obj['desc'])
        for cmd, obj in cmd_data['control'].iteritems():
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.serverControlCmd
            syntaxSet[cmd] = obj['syntax']
            desc.append(obj['desc'])
        for cmd, obj in cmd_data['player'].iteritems():
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.commander.playerCmd    
            syntaxSet[cmd] = obj['syntax']
            desc.append(obj['desc'])

        self.commander.setSyntax(syntaxSet)
        self.commander.setDescriptions(desc)

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

    def serverShouldRun(self):
        #if int(getenv(self.SHOULD_RUN_VAR, 0)):
        return True
        #return False

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
        if self.COMMANDS[args[0]]['admin'] and not self.server.isAdmin(player):
            self.server.message(player, "You don't have access to that command!")
            return
        func(player, args)

    def saveNeeded(self):
        if time() > (self.lastSave + self.SAVE_INTERVAL):
            return True
        return False

    def routine(self):
        while self.serverShouldRun():
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

        self.printFlush('Stopping server due to env var...')
        self.stopServer()

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

