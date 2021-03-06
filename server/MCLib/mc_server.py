from subprocess import Popen, PIPE, STDOUT
from time import sleep
from datetime import date
from sys import stdout, exit, path
from mc_timeout import TimeoutSignal
import json
import re

class Server:

    ADMINS = [
        'KILA_GODZ',
        'iLikeYoBraids',
        'Hexwolf'
    ]
    WAIT_FOR_STARTED = 5
    CMD = ['java', '-Xmx4096m', '-Xms2048m', '-jar', '{}/server.jar'.format(path[0]), 'nogui']
    CMD_WAIT = 3
    TIMEOUT = 5
    
    ADMINS_FILE = 'ops.json'
    CONNECT_PATTERN = r'^\[(?:\d{2}:){2}\d{2}\] \[.*\]: (.*) joined the game$'
    DISCONN_PATTERN = r'^\[(?:\d{2}:){2}\d{2}\] \[.*\]: (.*) lost connection: .*'
    COORDS_PATTERN  = r'^\[(?:\d{2}:){2}\d{2}\] \[.*\]: .* has the following entity data: \[([-]?\d+\.\d+)d, ([-]?\d+\.\d+)d, ([-]?\d+\.\d+)d\]$'
    COORDS_CMD      = 'execute run data get entity {} Pos'

    PLAYER_GAMEMODE_CMD = 'execute as {} run gamemode {}'

    def __init__(self):
        self.today = date.today()
        self.process = None
        self.players = set()

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

        out = self.process.communicate("stop\n")[0]
        print out
        sleep(self.CMD_WAIT)
        self.process = None

    def changeWeather(self, weather):
        self.writeToProcess("weather {}".format(weather))

    def changeTime(self, time):
        self.writeToProcess("time set {}".format(time))

    def teleport(self, tpFmt):
        self.writeToProcess("tp {}".format(tpFmt))
    
    def message(self, player, msg, color = None):
        message = {}
        message['text'] = msg
        if color:
            message['color'] = color
        
        self.writeToProcess("tellraw {} {}".format(player, json.dumps(message)))

    def start(self):
        self.today = date.today()
        self.process = Popen(self.CMD, stdin = PIPE, stdout = PIPE, stderr = STDOUT)
        sleep(self.WAIT_FOR_STARTED)

    def restart(self, warnTime = 0):
        if warnTime > 0:
            self.say("Restarting Server in {} seconds!".format(warnTime))
            sleep(warnTime)
        self.stop()
        self.start()

    def readLine(self):
        TimeoutSignal.timeout(self.TIMEOUT)
        line = ""
        try:
            line = self.process.stdout.readline().strip()
        except TimeoutSignal:
            pass
        else:
            TimeoutSignal.reset()
            if 'joined' in line:
                match = re.match(self.CONNECT_PATTERN, line)
                if match:
                    self.players.add(match.group(1))
                    self.printPlayers()
            elif 'lost connection' in line:
                match = re.match(self.DISCONN_PATTERN, line)
                if match:
                    self.players.discard(match.group(1))
                    self.printPlayers()

        return line

    def changePlayerGameMode(self, player, gamemode):
        self.writeToProcess(self.PLAYER_GAMEMODE_CMD.format(player, gamemode))

    def getCurrentPlayers(self):
        return list(self.players)

    def getPlayerCoords(self, player):
        self.writeToProcess(self.COORDS_CMD.format(player))
        coords = self.readLine()
        print("received {}".format(coords))
        coordsArr = []
        if coords:
            match = re.match(self.COORDS_PATTERN, coords)
            if match:
                coordsArr = [round(float(match.group(1)), 2), round(float(match.group(2)), 2), round(float(match.group(3)), 2)]
        return coordsArr

    def printPlayers(self):
        print('Current Players: {}'.format(self.players))

    def isAdmin(self, player):
        if player in self.ADMINS:
            return True
        json_data = json.load(open(self.ADMINS_FILE))
        for obj in json_data:
            if player == obj["name"]:
                return True
        return False
