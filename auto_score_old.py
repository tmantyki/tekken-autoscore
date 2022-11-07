from ctypes import *
from ctypes.wintypes import *
from manual_score import LiveScore
import psutil
import pymem
import os
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
            ReadProcessMemory(processHandle, ptr_addr, res_buffer, res_size, byref(bytesRead))
        else:
            ReadProcessMemory(processHandle, ptr_addr, byref(buffer), bufferSize, byref(bytesRead))
    return res_buffer.value

class AutoScore:

    def __init__(self, init_p1=0, init_p2=0):
        self.pid = None
        self.base = None
        self.live_score = LiveScore()
        self.reference = [-init_p1, -init_p2]
        self.updateProcess()
        read_wins = self.readWins()
        self.reference[0] += read_wins[0]
        self.reference[1] += read_wins[1]
        self.updateScore()
        self.history = set()
        self.history.add(self.live_score.getScore())
        self.live_score.writeToFile()
        print(self.live_score.__repr__())

    def resetScores(self):
        self.live_score.resetScores()
        self.history.clear()

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
                    print("PID acquired!", self.pid)
                    # print("base++", hex(self.base))
                    return self.pid
            time.sleep(10)
    
    def closeProcess(self):
        CloseHandle(self.processHandle)

    def bytesToScore(self, bytes):
        str_b = bytes.decode("utf-8")
        if str_b[-2:] != " W":
            return None
        else:
            return int(str_b[:-2])

    def readWins(self):
        buffer = c_char_p("12345678901234567890".encode('utf-8'))
        bufferSize = len(buffer.value)
        ptr_chain_1 = [0x20, 0x50, 0x40, 0x48, 0x188, 0x390, 0x4c]
        ptr_chain_2 = [0x20, 0x50, 0x40, 0x48, 0x170, 0x48, 0xac]
        while True:
            try:
                time.sleep(1)
                self.updatePID()
                p1_wins = self.bytesToScore(forwardPtr(self.processHandle, self.base + 0x034D3120, ptr_chain_1, buffer, bufferSize))
                p2_wins = self.bytesToScore(forwardPtr(self.processHandle, self.base + 0x034D3120, ptr_chain_2, buffer, bufferSize))
                if p1_wins and p2_wins:
                    # print("{} W, {} W".format(p1_wins, p2_wins))
                    return p1_wins, p2_wins
                else:  
                    continue
            except TypeError:
                continue

    def resetReference(self):
        self.reference[0], self.reference[1] = self.readWins()

    def updateScore(self):
        wins = self.readWins()
        old_p1, old_p2 = self.live_score.getScore()
        new_p1, new_p2 = wins[0]-self.reference[0], wins[1]-self.reference[1]
        if old_p1 != new_p1 or old_p2 != new_p2:
            if not (new_p1, new_p2) in self.history:
                self.history.add((new_p1, new_p2))
                self.live_score.setScore(new_p1, new_p2)
                self.live_score.writeToFile()
                print(self.live_score.__repr__())

    def updatePID(self): # when to use?
        if not psutil.pid_exists(self.pid):
            print("Game process has died. Waiting for restart..")
            self.pid = None
            self.updateProcess()

    def getLiveScore(self):
        return self.live_score

def event_p1_wins(event):
    global auto_score
    auto_score.getLiveScore().incrementScore(side=1)
    auto_score.history.add(auto_score.getLiveScore().getScore())
    auto_score.getLiveScore().writeToFile()
    print(auto_score.getLiveScore().__repr__())

def event_p2_wins(event):
    global auto_score
    auto_score.getLiveScore().incrementScore(side=2)
    auto_score.history.add(auto_score.getLiveScore().getScore())
    auto_score.getLiveScore().writeToFile()
    print(auto_score.getLiveScore().__repr__())

def event_reset(event):
    global auto_score
    auto_score.resetScores()
    auto_score.resetReference()
    auto_score.history.add(auto_score.getLiveScore().getScore())
    auto_score.getLiveScore().writeToFile()
    print(auto_score.getLiveScore().__repr__())

init_p1 = 0
init_p2 = 0
if len(sys.argv) == 3:
    init_p1 = int(sys.argv[1])
    init_p2 = int(sys.argv[2])
auto_score = AutoScore(init_p1, init_p2)

if __name__ == "__main__":
    keyboard.on_press_key('f5', event_p1_wins, suppress=False)
    #keyboard.on_press_key('f6', event_hide, suppress=False)
    keyboard.on_press_key('f7', event_reset, suppress=False)
    keyboard.on_press_key('f8', event_p2_wins, suppress=False)
    try:
        while True:
            auto_score.updateScore()
    except KeyboardInterrupt:
        print("Exiting..")
        with open("live_score", 'w') as f:
            f.write("")