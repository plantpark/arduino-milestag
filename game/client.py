#!/usr/bin/python

import argparse
import serial
import socket
import sys
import time

from core import Player, StandardGameLogic, ClientServer, GameState
from connection import ClientServerConnection
import proto

class Client(ClientServerConnection):
  def __init__(self, main):
    ClientServerConnection.__init__(self)
    self.main = main
    
    self._openConnection()
  
  def handleMsg(self, fullLine):
    event = proto.parseEvent(fullLine)
    msgStr = event.msgStr
    
    h = proto.MessageHandler()

    @h.handles(proto.TEAMPLAYER)
    def teamPlayer(teamID, playerID):
      self.main.player = Player(teamID, playerID)
      return True
      
    @h.handles(proto.STARTGAME)
    def startGame(duration):
      self.main.gameState.setGameTime(int(duration))
      self.main.gameState.startGame()
      return True
    
    @h.handles(proto.STOPGAME)
    def stopGame():
      self.main.gameState.stopGame()
      return True
    
    @h.handles(proto.DELETED)
    def deleted():
      #just treat this as the game stopping for us.
      self.main.gameState.stopGame()
      return True
    
    return h.handle(msgStr)

  def _openConnection(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #reduce the timeout while we are testing on a good network.
    #This will want increasing dramatically when we are on the wireless mesh.
    self.sock.settimeout(1)
    self.sock.connect((ClientServer.SERVER, ClientServer.PORT))

    self.setSocket(self.sock)


class Main():

  def __init__(self):
    parser = argparse.ArgumentParser(description='BraidsTag gun logic.')
    parser.add_argument('-s', '--serial', type=str, help='serial device to which the arduino is connected', required=True)
    #parser.add_argument('-p', '--playerID', type=self._stringToPlayerID, help='player id', default=1)
    #parser.add_argument('-t', '--teamID', type=int, choices=xrange(1, 8), help='team id', default=1)

    self.args = parser.parse_args()

    self.serverConnection = Client(self)
    self._sendToServer(proto.HELLO.create())

    try:
      self.serial = serial.Serial(self.args.serial, 115200)
      self.properSerial = True
    except serial.serialutil.SerialException:
      #Try just opening this as a file
      self.serial = open(self.args.serial)
      self.properSerial = False

    def playerDead():
      print "Out of lives!"

    self.logic = StandardGameLogic()
    self.logic.playerDead.connect(playerDead)
    self.gameState = GameState()

    self.connectToArduino()

  def serialWrite(self, line):
    if (self.properSerial):
      self.serial.write(line + "\n")

    print "-a>", repr(line)
    sys.stdout.flush()

  def eventLoop(self):
    for line in self.serial:
      line = line.rstrip()
      print "<a-", repr(line)
      sys.stdout.flush()

      h = proto.MessageHandler()

      @h.handles(proto.HIT)
      def hit(sentTeam, sentPlayer, damage):
        self.logic.hit(self.gameState, self.player, sentTeam, sentPlayer, damage)
        return True

      @h.handles(proto.FULL_AMMO)
      def fullAmmo():
        self.logic.fullAmmo(self.gameState, self.player)
        return True

      @h.handles(proto.TRIGGER)
      def trigger():
        if (self.logic.trigger(self.gameState, self.player)):
          self.serialWrite(proto.FIRE.create(self.player.teamID, self.player.playerID, self.player.gunDamage))
        return True

      #TODO be more discerning about unparseable input here.
      h.handle(line)

      msg = proto.RECV.create(self.player.teamID, self.player.playerID, line)
      self._sendToServer(msg)

  def _stringToPlayerID(self, inp):
    out = int(inp)
    if out < 1 or out > 32:
      raise argparse.ArgumentTypeError("playerId must be between 1 and 32.")
    return out;

  def _sendToServer(self, msg):
    "queue this packet to be sent to the server"
    self.serverConnection.queueMessage(msg)
  
  def connectToArduino(self):
    self.serialWrite(proto.CLIENTCONNECT.create())
    line = self.serial.readline()
    print "<a-", repr(line)
    sys.stdout.flush()

    if not proto.CLIENT_CONNECTED.parse(line):
      raise RuntimeError("incorrect ack to ClientConnect(): %s" % (line))


main = Main()
try:
  print main.player
except:
  pass
main.eventLoop()
print main.player
main.serverConnection.stop()
main.serial.close()
