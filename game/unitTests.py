#!/usr/bin/python

import unittest

from core import Player, StandardGameLogic, GameState
from server import ServerMsgHandler, ServerGameState

class TestTakingHits(unittest.TestCase):
  def setUp(self):
    self.gl = StandardGameLogic()
    self.gameState = GameState()
    self.gameState.setGameTime(120)
    
  def test_simple_hit_while_game_stopped(self):
    player = Player(1, 1)
    initialHealth = player.health
  
    sentTeam = 1
    sentPlayer = 2
    damage = 2
  
    self.gl.hit(self.gameState, player, sentTeam, sentPlayer, damage)
  
    self.assertEqual(initialHealth, player.health)

  def test_simple_hit(self):
    self.gameState.startGame()
    player = Player(1, 1)
    initialHealth = player.health
  
    sentTeam = 2
    sentPlayer = 1
    damage = 2
  
    self.gl.hit(self.gameState, player, sentTeam, sentPlayer, damage)
  
    self.assertEqual(initialHealth - damage, player.health)

  def test_self_hit(self):
    self.gameState.startGame()
    player = Player(1, 1)
    initialHealth = player.health
  
    sentTeam = 1
    sentPlayer = 1
    damage = 2
  
    self.gl.hit(self.gameState, player, sentTeam, sentPlayer, damage)
  
    self.assertEqual(initialHealth, player.health)

  def test_team_hit(self):
    self.gameState.startGame()
    player = Player(1, 1)
    initialHealth = player.health
  
    sentTeam = 1
    sentPlayer = 2
    damage = 2
  
    self.gl.hit(self.gameState, player, sentTeam, sentPlayer, damage)
  
    self.assertEqual(initialHealth - damage, player.health)

  def test_shot_until_dead(self):
    self.gameState.startGame()
    player = Player(1, 1)
    initialHealth = player.health
  
    sentTeam = 2
    sentPlayer = 1
    damage = (player.health // 2) + 1 # this will fail if the player only starts with 2 health :-(
  
    self.gl.hit(self.gameState, player, sentTeam, sentPlayer, damage)
    self.assertEqual(initialHealth - damage, player.health)

    self.gl.hit(self.gameState, player, sentTeam, sentPlayer, damage)
    self.assertEqual(0, player.health)
    #TODO assert death signal
    
    self.gl.hit(self.gameState, player, sentTeam, sentPlayer, damage)
    self.assertEqual(0, player.health)
    #TODO assert NO death signal

if __name__ == '__main__':
  unittest.main()
