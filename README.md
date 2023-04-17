
**Dependencies**
Install missing libraries via pip. Check the imported libraries in `manual_score.py`

**Usage**
`python auto_score.py`
`python3 auto_score.py`

**Description**
The program will update the score to the plaintext file `live_score`. To modify the format by which the score is written to the file, modify the methods `LiveScore.writeToFile()` and `LiveScore.__str__()` accordingly. The plaintext file can thus be added in OBS as a text file source which updates with a latency of approximately one second.

The program will independently keep track of scores for each encountered opponent. Records are preserved in memory only for the duration of program execution. The displayed score will switch orientation automatically whenever the playing side is changed.

**Hotkeys**
F9: Reset the score to 0-0 for the current opponent
Keyboard Interrupt (Ctrl+C): Exit program

**Restrictions**
This program is primarily intended for use with queued Player or Ranked matches. Record-keeping probably works in one-on-one lobbies and local versus matches, however, it is recommended to reset the score manually at the start of such sets. Player match lobbies with more than two players are untested and may result in unpredictable behaviour.

The application will attempt to retrieve a new PID value every 10 seconds if the previous game process dies. Hotkeys may or may not work as intended while waiting for the new process.

When the script freshly is launched and a new game process is started, the scorekeeper may detect garbage strings in memory as new players and report the creation of new records for such bogus opponents. This bug is largely benign and should not affect the apparent function of the program.
