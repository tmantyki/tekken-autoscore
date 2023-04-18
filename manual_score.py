import keyboard
import time

class LiveScore:

  def __init__(self, init_p1=0, init_p2=0):
    self.p1 = init_p1
    self.p2 = init_p2
  
  def resetScores(self):
    self.p1 = 0
    self.p2 = 0

  def incrementScore(self, player):
    if player == 0:
      self.p1 += 1
    elif player == 1:
      self.p2 += 1

  def __str__(self, side=0):
    if side == 0:
      p1 = self.p1
      p2 = self.p2
    elif side == 1:
      p1 = self.p2
      p2 = self.p1
    str_rpr = ""
    if p1 < 10:
      str_rpr += " "
    str_rpr += str(p1) + "             " + str(p2)
    if p2 < 10:
      str_rpr += " "
    return str_rpr

  def __repr__(self, side=0):
    if side == 0:
      return "{}   {}".format(self.p1, self.p2)
    elif side == 1:
      return "{}   {}".format(self.p2, self.p1)

  def writeToFile(self, side=0, filename="live_score"):
    with open(filename, 'w') as f:
      f.write(self.__str__(side))

  def writeNameToFile(self, name, filename="opponent_name.txt"):
    with open(filename, 'w') as f:
      f.write("Opponent: " + name)