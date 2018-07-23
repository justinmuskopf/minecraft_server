from time import time
from sys import stdout
from mc_server import Server
import re
import json

class ServerHandler():
    SAVE_INTERVAL = 15 * 60
    WARNING_TIME = 60
    CMD_PATTERN = r'^\[(?:\d{2}:){2}\d{2}\] \[.*\]: <(.*)> (.*)$'
    LOCATIONS_FILE = 'locations.json'
    COMMANDS_FILE = 'commands.json'
    def __init__(self, server = None):
        if server:
            if type(server) != Server:
                raise TypeError
            self.server = server
        else:
            self.server = Server()
        self.lastSave = 0

        self.COMMANDS = {}
        cmd_data = json.load(open(self.COMMANDS_FILE))
        for cmd, obj in cmd_data['weather']:
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.changeWeatherTo
        for cmd, obj in cmd_data['time']:
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.changeTimeTo
        for cmd, obj in cmd_data['control']:
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.serverControlCmd
        for cmd, obj in cmd_data['player']:
            self.COMMANDS[cmd] = obj
            self.COMMANDS[cmd]['func'] = self.playerCmd

    def printFlush(self, line):
        self.printLine('>>> {}'.format(line))

    def printLine(self, line):
        print(line)
        stdout.flush()

    def invalidSyntax(self, player, cmd):
        self.server.message(player, self.COMMANDS[cmd]['syntax'])

    def changeWeatherTo(self, player, args):
        self.server.changeWeather(args[0])

    def changeTimeTo(self, player, args):
        self.server.changeTime(args[0])

    def serverControlCmd(self, player, args):
        lowCmd = args[0].lower()
        if lowCmd == 'restart':
            self.restartServer()
        elif lowCmd == 'save':
            self.saveServer()
        elif lowCmd == 'help':
            self.sendHelp(player, args)

    def playerCmd(self, player, args):
        lowCmd = args[0].lower()
        if lowCmd == 'tp':
            self.teleportPlayer(player, args)
        elif lowCmd == 'save-spot':
            self.saveLocationForPlayer(player, args)
        
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

    def saveServer(self):
        self.printFlush("Saving server...")
        self.server.save()
        self.lastSave = time()

    def getLocationsForPlayer(self, player):
        json_data = json.load(open(self.LOCATIONS_FILE))
        locations = json_data[player]
        return locations

    def saveLocationForPlayer(self, player, args):
        if len(args) != 5:
            self.invalidSyntax(player, args[0])

        name = args[1].lower()
        xyz = args[2:]

        json_data = json.load(open(self.LOCATIONS_FILE))

        if not json_data[player]:
            json_data[player] = {}
        json_data[player][name] = {
            'x': xyz[0],
            'y': xyz[1],
            'z': xyz[2]
        }

        with open(self.LOCATIONS_FILE, 'w') as json_file:
            json.dump(json_data, json_file)
                
    def teleportPlayer(self, player, args):
        numArgs = len(args)
        if numArgs < 2 or numArgs > 4:
            self.invalidSyntax(player, args[0])
            return
        
        tpString = ""

        #!tp <x> <y> <z>
        if numArgs == 4:
            tpString = "{} {} {} {}".format(player, args[1], args[2], args[3])
        
        #!tp <them> me
        elif numArgs == 3:
            if args[2] != 'me':
                self.invalidSyntax(player, args[0])
            if len(args[1]) < 3:
                self.server.message(player, "Please use at least three characters in the other person's name!")
                return

            players = self.server.getCurrentPlayers()
            playerToTp = ""
            for playerName in players:
                if args[1].lower() in playerName.lower():
                    playerToTp = playerName
                    break
            if not playerToTp:
                self.server.message(player, "Player '{}' not found!".format(args[1]))
                return
            tpString = "{} {}".format(playerToTp, player)

        #!tp <them> | <location name>
        elif numArgs == 2:
            #player
            playerToTp = ""
            players = self.server.getCurrentPlayers()
            lowerSearch = args[1].lower()
            for playerName in players:
                if lowerSearch in playerName.lower():
                    playerToTp = playerName
                    break
            if playerToTp:
                tpString = "{} {}".format(player, playerToTp)
            #location
            else:
                locations = self.getLocationsForPlayer(player)
                if locations:
                    location = None
                    try:
                        location = locations[args[1].lower()]
                    except KeyError:
                        self.server.message(player, "No player or location '{}' found!".format(args[1]))
                        return
                    if location:
                        tpString = "{} {} {} {}".format(player, location["x"], location["y"], location["z"])
                else:
                    self.invalidSyntax(player, "No player or location '{}' found!".format(args[1]))
                    return

        self.server.teleport(tpString)

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

