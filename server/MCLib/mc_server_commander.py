from mc_server import Server
import json

class ServerCommander:
    LOCATIONS_FILE = 'locations.json'
    def __init__(self, server):
        self.server = server
        self.syntaxSet = {}

    def setSyntax(self, syntax):
        self.syntaxSet = syntax

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
        if lowCmd == 'tp':
            self.teleportPlayer(player, args)
        elif lowCmd == 'save-spot':
            self.saveLocationForPlayer(player, args)
        elif lowCmd == 'help':
            self.sendHelp(player, args)

    def sendHelp(self, player, args):
        if len(args) > 1:
            helpStr = ""
            try:
                helpStr = self.syntaxSet[args[1].lower()]
            except KeyError:
                self.server.say("help: No such function '{}' found".format(args[1]))
            else:
                self.server.say(helpStr)
        else:
            for cmd, syntax in self.syntaxSet.iteritems():
                self.server.say(syntax)

    def getLocationsForPlayer(self, player):
        json_data = json.load(open(self.LOCATIONS_FILE))
        locations = json_data[player]
        return locations or None

    def saveLocationForPlayer(self, player, args):
        if len(args) != 5:
            self.invalidSyntax(player, args[0])
            return

        name = args[1].lower()
        xyz = args[2:]

        json_data = json.load(open(self.LOCATIONS_FILE))

        if not player in json_data:
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
                return
            if len(args[1]) < 3:
                self.server.message(player, "Please use at least three characters in the other person's name!")
                return

            players = self.server.getCurrentPlayers()
            playerToTp = ""
            lowerSearch = args[1].lower()
            for playerName in players:
                if lowerSearch in playerName.lower():
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
                    self.server.message(player, "No player or location '{}' found!".format(args[1]))
                    return

        self.server.teleport(tpString)

