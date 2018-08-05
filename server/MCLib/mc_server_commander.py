from mc_server import Server
from sys import path
import json
import re

class ServerCommander:
    LOCATIONS_FILE = '{}/locations.json'.format(path[0])

    def __init__(self, server):
        self.server = server
        self.syntaxSet = {}
        self.descriptions = {}
        self.teleTable = {}

    def setSyntax(self, syntax):
        self.syntaxSet = syntax

    def setDescriptions(self, desc):
        self.descriptions = desc

    def invalidSyntax(self, player, cmd):
        try:
            self.server.message(player, self.syntaxSet[cmd])
        except KeyError:
            self.server.message(player, "Syntax for '{}' not found!".format(cmd))

    def changeWeatherTo(self, player, args):
        self.server.changeWeather(args[0])

    def changeTimeTo(self, player, args):
        self.server.changeTime(args[0])

    def playerCmd(self, player, args):
        lowCmd = args[0].lower()
        if lowCmd == 'tp' or lowCmd == 'bring':
            self.teleportPlayer(player, args)
        elif lowCmd == 'save-spot':
            self.saveLocationForPlayer(player, args)
        elif lowCmd == 'help':
            self.sendHelp(player, args)
        elif lowCmd == 'back':
            self.teleportPlayerBack(player)
        elif lowCmd == 'locations':
            self.sendPlayerLocations(player)

    def sendHelp(self, player, args):
        if len(args) > 1:
            helpStr = ""
            try:
                helpStr = self.syntaxSet[args[1].lower()]
            except KeyError:
                self.server.message(player, "help: No such function '{}' found".format(args[1]), "red")
            else:
                self.server.message(player, helpStr)
        else:
            helpStr = "TIP: Call '!help' on a specific function to view its syntax!\n"
            if self.descriptions:
                helpStr += "\n".join(self.descriptions)
            else:
                helpStr += "\n".join(self.syntaxSet)

            self.server.message(player, helpStr)

    def getLocationsForPlayer(self, player):
        json_data = json.load(open(self.LOCATIONS_FILE))
        locations = json_data[player]
        return locations or None

    def sendPlayerLocations(self, player):
        locations = self.getLocationsForPlayer(player)
        locationsStr = "\n".join([key for key in locations])
        self.server.message(player, locationsStr)

    def saveLocationForPlayer(self, player, args):
        argsLen = len(args)
        if argsLen != 5 and argsLen != 2:
            self.invalidSyntax(player, args[0])
            return

        name = args[1].lower()

        xyz = []
        if argsLen == 2:
            xyz = self.server.getPlayerCoords(player)
            if not xyz:
                self.server.message(player, "ERROR: No coordinates received!", "red")
                return
        else:
            xyz = args[2:]

        self.server.message(player, "Saving Location {} at Position {}".format(name, xyz))
        json_data = json.load(open(self.LOCATIONS_FILE))

        if not player in json_data:
            json_data[player] = {}
        json_data[player][name] = {
            'x': xyz[0],
            'y': xyz[1],
            'z': xyz[2]
        }

        with open(self.LOCATIONS_FILE, 'w') as json_file:
            json.dump(json_data, json_file, indent = 4, sort_keys = True)
                
    def teleportPlayer(self, player, args):
        numArgs = len(args)
        if numArgs != 2 and numArgs != 4:
            self.invalidSyntax(player, args[0])
            return
        
        tpString = ""

        #!tp <x> <y> <z>
        if numArgs == 4:
            tpString = "{} {} {} {}".format(player, args[1], args[2], args[3])
        
        #!tp (<them> | <location name>) | !bring <them>
        elif numArgs == 2:
            #location
            locations = self.getLocationsForPlayer(player)
            if locations:
                location = None
                try:
                    location = locations[args[1].lower()]
                except KeyError:
                    pass
                if location:
                    tpString = "{} {} {} {}".format(player, location["x"], location["y"], location["z"])
            #player/bring
            if not tpString:
                playerToTp = ""
                players = self.server.getCurrentPlayers()
                lowerSearch = args[1].lower()
                for playerName in players:
                    if lowerSearch in playerName.lower():
                        playerToTp = playerName
                        break
                if playerToTp:
                    if args[0] == 'tp':
                        tpString = "{} {}".format(player, playerToTp)
                    elif args[0] == 'bring':
                        tpString = "{} {}".format(playerToTp, player)
                else:
                    self.server.message(player, "No player or location '{}' found!".format(args[1]), "red")
                    return

        self.teleTable[player] = self.server.getPlayerCoords(player)

        self.server.teleport(tpString)

    def teleportPlayerBack(self, player):
        if player not in self.teleTable or self.teleTable[player] == None:
            self.server.message(player, 'No previous locations to teleport you to!', 'red')
            return
        coords = self.teleTable[player]
        tpString = '{} {} {} {}'.format(player, coords[0], coords[1], coords[2])
        self.server.teleport(tpString)
        self.teleTable[player] = None
