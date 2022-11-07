
**Dependencies**
Install missing libraries via pip. Check the imported libraries in `manual_score.py`

**Usage**
`python3 auto_score.py`

**Description**
The program will update the score to the plaintext file `live_score`. To modify the format by which the score is written to the file, modify the methods `LiveScore.writeToFile()` and `LiveScore.__str__()` accordingly. The plaintext file can thus be added in OBS as a text file source which updates with a latency of approximately one second.

The program will assume that the player is playing on 1P (left) side by default. Switching the playing side will flip the position of the current score.

**Hotkeys**
F5: Set the playing side to 1P (left)  
F8: Set the playing side to 2P (right)  
F9: Reset the score to 0-0  
Keyboard Interrupt: Exit program

Note: the application will attempt to retrieve a new PID value every 10 seconds if the previous game process dies. Hotkeys may or may not work as intended while waiting for the new process.
