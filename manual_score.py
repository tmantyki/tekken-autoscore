import keyboard
import time

class LiveScore:

  def __init__(self, init_p1=0, init_p2=0, playing_side=1):
    self.playing_side = playing_side
    self.p1 = init_p1
    self.p2 = init_p2
  
  def resetScores(self):
    self.p1 = 0
    self.p2 = 0

  def incrementScore(self, side):
    if (side == 1 and self.playing_side == 1) or \
       (side == 2 and self.playing_side == 2):
      self.p1 += 1
    elif (side == 2 and self.playing_side == 1) or \
       (side == 1 and self.playing_side == 2):
      self.p2 += 1

  def invertScore(self):
    self.p1, self.p2 = self.p2, self.p1

  def getPlayingSide(self):
    return self.playing_side

  def setPlayingSide(self, side):
    self.playing_side = side

  def setScore(self, p1_score, p2_score):
    self.p1 = p1_score
    self.p2 = p2_score

  def __str__(self):
    str_rpr = ""
    if self.p1 < 10:
      str_rpr += " "
    str_rpr += str(self.p1) + "             " + str(self.p2)
    if self.p2 < 10:
      str_rpr += " "
    return str_rpr

  def __repr__(self):
    return "{}   {}".format(self.p1, self.p2)

  def writeToFile(self, filename="live_score"):
    with open(filename, 'w') as f:
      f.write(str(self))

  def getScore(self):
    return self.p1, self.p2

live_score = LiveScore()

def event_p1_wins(event):
  global live_score
  live_score.incrementScore(side=1)
  live_score.writeToFile()

def event_p2_wins(event):
  global live_score
  live_score.incrementScore(side=2)
  live_score.writeToFile()

def event_reset(event):
  global live_score
  live_score.resetScores()
  live_score.writeToFile()

def event_hide(event):
  global live_score
  live_score.resetScores()
  with open("live_score", 'w') as f:
      f.write("")

live_score = LiveScore()

if __name__ == "__main__":
  print("Started Tekken score tracker!")
  keyboard.on_press_key('f5', event_p1_wins, suppress=False)
  keyboard.on_press_key('f6', event_hide, suppress=False)
  keyboard.on_press_key('f7', event_reset, suppress=False)
  keyboard.on_press_key('f8', event_p2_wins, suppress=False)
  try:
    while True:
      time.sleep(0.1)
  except KeyboardInterrupt:
    print("Exiting..")