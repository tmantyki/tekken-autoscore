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
        self.prev_rounds = (0, 0)
        self.updateProcess()
        self.updateScore()
        self.live_score.writeToFile()
        print(self.live_score.__repr__())

    def resetScores(self):
        self.live_score.resetScores()

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
                    # print("base++", hex(self.base))
                    return self.pid
            time.sleep(10)
    
    def closeProcess(self):
        CloseHandle(self.processHandle)

    def readSideFlag(self):
        while True:
            try:
                self.updatePID()
                buffer = c_ubyte()
                bufferSize = 1
                #ptr = self.base + 0x34CAFB0
                ptr = self.base + 0x034CE030
                ptr_chain = [0x498, 0x14]
                return forwardPtr(self.processHandle, ptr, ptr_chain, buffer, bufferSize)
            except TypeError:
                continue

    def readRounds(self):
        while True:
            try:
                self.updatePID()
                bytesRead = c_ulonglong()
                p1_rounds = c_ubyte()
                p2_rounds = c_ubyte()
                bufferSize = 1
                p1_ptr = self.base + 0x34CD500
                p2_ptr = self.base + 0x34CD5F0
                ReadProcessMemory(self.processHandle, p1_ptr, byref(p1_rounds), 1, byref(bytesRead))
                ReadProcessMemory(self.processHandle, p2_ptr, byref(p2_rounds), 1, byref(bytesRead))
            except TypeError:
                continue
            if self.readSideFlag() == 0:
                return p1_rounds.value, p2_rounds.value
            elif self.readSideFlag() == 1:
                return p2_rounds.value, p1_rounds.value

    def updateScore(self):
        min_age = 50
        o_p1, o_p2 = self.prev_rounds
        n_p1, n_p2 = self.prev_rounds = self.readRounds()
        if (o_p1, o_p2) != (n_p1, n_p2):
            if (n_p1 == 3) ^ (n_p2 == 3):
                if self.rounds_age >= min_age:
                    if n_p1 == 3 and o_p1 == 2 and n_p2 == o_p2:
                        self.live_score.incrementScore(side=1)
                        self.live_score.writeToFile()
                        print(self.live_score.__repr__())
                    elif n_p2 == 3 and o_p2 == 2 and n_p1 == o_p1:
                        self.live_score.incrementScore(side=2)
                        self.live_score.writeToFile()
                        print(self.live_score.__repr__())          
            self.rounds_age = 0
            #print("# Debug: readSideFlag() =", self.readSideFlag())
        else:
            self.rounds_age += 1

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
    print(auto_score.getLiveScore().__repr__())

def event_p1(event):
    global auto_score
    if auto_score.getLiveScore().getPlayingSide() == 2:
        print("Playing side set to 1")
        auto_score.getLiveScore().invertScore()
        auto_score.getLiveScore().setPlayingSide(1)
        auto_score.getLiveScore().writeToFile()
        print(auto_score.getLiveScore().__repr__())

def event_p2(event):
    global auto_score
    if auto_score.getLiveScore().getPlayingSide() == 1:
        print("Playing side set to 2")
        auto_score.getLiveScore().invertScore()
        auto_score.getLiveScore().setPlayingSide(2)
        auto_score.getLiveScore().writeToFile()
        print(auto_score.getLiveScore().__repr__())

init_p1 = 0
init_p2 = 0
if len(sys.argv) == 3:
    init_p1 = int(sys.argv[1])
    init_p2 = int(sys.argv[2])
print("Playing side set to 1")
try:
    auto_score = AutoScore(init_p1, init_p2)
except KeyboardInterrupt:
    print("Exiting..")
    sys.exit()

if __name__ == "__main__":
    keyboard.on_press_key('f5', event_p1, suppress=False)
    keyboard.on_press_key('f8', event_p2, suppress=False)
    keyboard.on_press_key('f9', event_reset, suppress=False)
    
    try:
        while True:
            auto_score.updateScore()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting..")
        with open("live_score", 'w') as f:
            f.write("")