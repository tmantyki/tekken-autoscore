from ctypes import *
from ctypes.wintypes import *
from manual_score import LiveScore
import psutil
import pymem
import sys
import time
import keyboard

OpenProcess = windll.kernel32.OpenProcess
ReadProcessMemory = windll.kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = HANDLE, LPCVOID, LPVOID, c_size_t, POINTER(c_size_t)
ReadProcessMemory.restype = BOOL
CloseHandle = windll.kernel32.CloseHandle

PROCESS_ALL_ACCESS = 0x1F0FFF

def forwardPtr(processHandle, origin_addr, offsetList, res_buffer, res_size):
    ptr_addr = origin_addr
    buffer = c_void_p()
    bufferSize = sizeof(buffer)
    bytesRead = c_ulonglong()
    ReadProcessMemory(processHandle, ptr_addr, byref(buffer), bufferSize, byref(bytesRead))
    for offset in offsetList:
        ptr_addr = buffer.value + offset
        if offset == offsetList[-1]:
            ReadProcessMemory(processHandle, ptr_addr, byref(res_buffer), res_size, byref(bytesRead))
        else:
            ReadProcessMemory(processHandle, ptr_addr, byref(buffer), bufferSize, byref(bytesRead))
    return res_buffer.value

class AutoScore:

    def __init__(self, init_p1=0, init_p2=0):
        self.pid = None
        self.base = None
        self.live_score = LiveScore(init_p1, init_p2)
        self.rounds_age = 0
        self.time_ref = time.time()
        self.prev_rounds = (0, 0)
        self.prev_side = None
        self.side_t_ref = None
        self.history = {}
        self.most_recent_opponent = None
        self.updateProcess()
        self.updateScore()
        if not self.most_recent_opponent:
            self.live_score.writeToFile(side=self.getPlayerSide())
            print(self.live_score.__repr__(side=self.getPlayerSide()))

    def loadHistory(self, opponentName):
        if opponentName in self.history.keys():
            print("Loading existing record with {}".format(opponentName))
            self.live_score = self.history[opponentName]
        else:
            print("Creating new record with {}".format(opponentName))
            self.live_score = LiveScore()
            self.history[opponentName] = self.live_score
        self.live_score.writeNameToFile(name=opponentName)
        self.live_score.writeToFile(side=self.getPlayerSide())
        print(self.live_score.__repr__(side=self.getPlayerSide()))    
    
    def saveHistory(self):
        op_name = self.readOpponentName()
        if op_name:
            self.history[op_name] = self.live_score
        else:
            self.history[self.most_recent_opponent] = self.live_score

    def checkNewOpponent(self):
        op_name = self.readOpponentName()
        if not op_name:
            return False
        if not op_name in self.history.keys():
            return True
        if self.history[op_name] == self.live_score:
            return False
        else:
            return True

    def resetScores(self):
        self.most_recent_opponent = None
        self.history.pop(self.readOpponentName(), None)
        self.live_score = LiveScore()

    def updateProcess(self):
        while self.pid == None:
            pids = psutil.pids()
            for p in pids:
                try:
                    ps = psutil.Process(p)
                except psutil.NoSuchProcess:
                    continue
                if "TekkenGame" in ps.name():
                    pm = pymem.Pymem("TekkenGame")
                    self.pid = int(ps.pid)
                    self.base = pm.base_address
                    self.processHandle = OpenProcess(PROCESS_ALL_ACCESS, False, self.pid)
                    pm.close_process()
                    print("Tekken 7 PID acquired:", self.pid)
                    return self.pid
            time.sleep(10)
    
    def closeProcess(self):
        CloseHandle(self.processHandle)

    def readPlayerSideFlag(self):
        while True:
            try:
                self.updatePID()
                buffer = c_ubyte()
                bufferSize = 1
                ptr = self.base + 0x034CE030
                ptr_chain = [0x498, 0x14]
                return forwardPtr(self.processHandle, ptr, ptr_chain, buffer, bufferSize)
            except TypeError:
                continue

    def readViewSideFlag(self):
        self.updatePID()
        bytesRead = c_ulonglong()
        buffer = c_ubyte()
        ptr = self.base + 0x034DF554
        ReadProcessMemory(self.processHandle, ptr, byref(buffer), 1, byref(bytesRead))
        return buffer.value
    
    def updateScoreOrientation(self, writing=True, protected=False):
        p_side = self.getPlayerSide()
        if self.prev_side == None:
            self.prev_side = p_side
            return
        if self.prev_side != p_side:
            if protected:
                if self.side_t_ref == None:
                    self.side_t_ref = time.time()
                    print("Detected side switch. Confirming in 30 seconds")
                    return
                else:
                    if time.time() - self.side_t_ref < 30: # 30 second protection
                        return
            self.prev_side = p_side
            if writing:
                if protected:
                    print("Confirm succeeded")
                print("Flipping score to match playing side")
                self.live_score.writeToFile(side=p_side)
                print(self.live_score.__repr__(side=p_side))
            self.side_t_ref = None
            return
        else:
            if self.side_t_ref != None:
                print("Confirm failed")
            self.side_t_ref = None


    def readOpponentName(self):
        confirm_name = None
        ptr = self.base + 0x34D55A0
        ptr_chain = [0x0, 0x8, 0x11C]
        while True:
            name = self.readString(ptr, ptr_chain, max_len=256)
            if name == "NOT_LOGGED_IN" or name == "":
                time.sleep(0.01)
                return None
            else:
                if name == confirm_name:
                    self.most_recent_opponent = name
                    return name
                else:
                    confirm_name = name
                    time.sleep(0.01)
                    continue
    
    def readString(self, ptr, ptr_chain, max_len=256):
        result = ''
        ptr_chain_copy = ptr_chain.copy()
        for i in range(max_len):
            while True:
                try:
                    self.updatePID()
                    buffer = c_ubyte()
                    bufferSize = 1
                    char_val = forwardPtr(self.processHandle, ptr, ptr_chain_copy, buffer, bufferSize)
                    if char_val == 0:
                        return result
                    result += chr(char_val)
                    break
                except TypeError:
                    continue
            ptr_chain_copy[-1] += 1
        return result

    def getPlayerSide(self):
        return int(self.readPlayerSideFlag() != self.readViewSideFlag())
        

    def readRounds(self):
        while True:
            try:
                self.updatePID()
                bytesRead = c_ulonglong()
                p1_rounds = c_ubyte()
                p2_rounds = c_ubyte()
                p1_ptr = self.base + 0x34CD500
                p2_ptr = self.base + 0x34CD5F0
                ReadProcessMemory(self.processHandle, p1_ptr, byref(p1_rounds), 1, byref(bytesRead))
                ReadProcessMemory(self.processHandle, p2_ptr, byref(p2_rounds), 1, byref(bytesRead))
            except TypeError:
                continue
            if self.readPlayerSideFlag() == 0:
                return p1_rounds.value, p2_rounds.value
            else:
                return p2_rounds.value, p1_rounds.value

    def updateScore(self):
        if self.checkNewOpponent():
            self.loadHistory(self.readOpponentName())
            self.updateScoreOrientation(writing=False, protected=False)
        self.updateScoreOrientation(protected=True)
        min_age = 3 # seconds
        o_p1, o_p2 = self.prev_rounds
        n_p1, n_p2 = self.prev_rounds = self.readRounds()
        if (o_p1, o_p2) != (n_p1, n_p2):
            if (n_p1 == 3) ^ (n_p2 == 3):
                if time.time() - self.time_ref >= min_age:
                    if n_p1 == 3 and o_p1 == 2 and n_p2 == o_p2:
                        self.live_score.incrementScore(player=0)
                        self.saveHistory()
                        self.live_score.writeToFile(side=self.getPlayerSide())
                        print(self.live_score.__repr__(side=self.getPlayerSide()))
                    elif n_p2 == 3 and o_p2 == 2 and n_p1 == o_p1:
                        self.live_score.incrementScore(player=1)
                        self.saveHistory()
                        self.live_score.writeToFile(side=self.getPlayerSide())
                        print(self.live_score.__repr__(side=self.getPlayerSide()))          
            self.time_ref = time.time()

    def updatePID(self):
        if not psutil.pid_exists(self.pid):
            print("Game process has died. Waiting for restart..")
            self.closeProcess()
            self.pid = None
            self.updateProcess()

    def getLiveScore(self):
        return self.live_score

def event_reset(event):
    global auto_score
    print("Resetting score..")
    auto_score.resetScores()
    auto_score.getLiveScore().writeToFile()
    print(auto_score.getLiveScore().__repr__(side=auto_score.getPlayerSide()))

init_p1 = 0
init_p2 = 0
if len(sys.argv) == 3:
    init_p1 = int(sys.argv[1])
    init_p2 = int(sys.argv[2])
try:
    auto_score = AutoScore(init_p1, init_p2)
except KeyboardInterrupt:
    print("Exiting..")
    sys.exit()

if __name__ == "__main__":
    keyboard.on_press_key('f9', event_reset, suppress=False)
    try:
        while True:
            auto_score.updateScore()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting..")
        with open("live_score", 'w') as f:
            f.write("")