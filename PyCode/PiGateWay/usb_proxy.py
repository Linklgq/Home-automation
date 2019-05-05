#-*-coding: utf-8 -*-
import serial
import time
import copy
from threading import Thread
import sys
if sys.version_info[0] == 2:
    from Queue import Queue
else:
    from queue import Queue


class USBProxy(Thread):
    
    targetMap = {"red": "1", "green": "2", "blue": "3"}
    statMap = {"on": "1", "off": "0"}
    rtargetMap = {"1": "red", "2": "green", "3": "blue"}
    rstatMap = {"1": "online", "0": "online", "N": "offline"}

    def __init__(self, dev = None, baudrate=115200, timeout=1):
        self.dev = dev
        self.serProxy = None
        self.endDeviceStatusList = []
        
        self.cmdQue = Queue(32)

        if dev:
            self.serProxy = serial.Serial(dev, baudrate, timeout = timeout)

        super(self.__class__, self).__init__()


    def __del__(self):
        if self.serProxy:
            self.serProxy.close()

    
    def Open(self, dev, baudrate=115200, timeout=1):
        self.serProxy = serial.Serial(dev, baudrate, timeout)

    
    def Close(self):
        if self.serProxy:
            self.serProxy.close()
            self.serProxy = None

    
    def SendData(self, data):
        bdata = data.encode("utf-8")

        try:
            self.serProxy.write(bdata)
            print "write %d bytes to USB"%len(bdata)
             
            return len(data)

        except Exception, e:
            print "SendData Exception occurs: %s"%str(e)
            return 0

    
    def RecvData(self, timeout = 5):
        start = time.time()
        
        if not self.serProxy.isOpen():
            print "Serial Port Is Closed"
            return None

        data = self.serProxy.read()
        total = data
        while data or not total:
            data = self.serProxy.read()
            total += data
            
            end = time.time()
            if end- start > timeout:
                print "RecvData timeout"
                return None

        return total


    def _CmdDic2Lst(self, cmdDic):
        """
        cmdDic has following format:
            {"red": "on", "green": "on", "blue": "on", "No": 1}
        "red: -> "1", "green" -> "2", "blue" -> "3"
        "on" -> "1", "off" -> "0"
        """
        cmdList = [] 
        targetList = ["red", "green", "blue"]

        print cmdDic
        if type(cmdDic) != type({}):
            print "cmdDic requires dict type"
            return None

        for key, value in cmdDic.items():
            if key not in targetList:
                continue
            
            cmdStr = self.targetMap[key] + self.statMap[value]
            cmdList.append(cmdStr)
            
        return cmdList

    
    def _CmdLst2Dic(self, lst):
        print "cmdLst: ", lst

        cmdDic = {}
        for item in lst:
            if type(item) != type("") or len(item) != 2:
                continue

            target = self.rtargetMap[item[0]]
            stat = self.rstatMap[item[1]]

            cmdDic[target] = stat

        return cmdDic


    def Send2USB(self, cmdDic):
        self.cmdQue.put(cmdDic)
        print "Put cmdDic to async queue between ZigBee and Pi succ"


    def run(self):
        while True:
            cmdDic = self.cmdQue.get()
            while not self.cmdQue.empty():
                cmdDic = self.cmdQue.get_nowait()

            cmdList = self._CmdDic2Lst(cmdDic)
        
            print "cmdList ", cmdList
            
            start = time.time()
            retList = []
            for cmd in cmdList:
                if cmd in self.endDeviceStatusList:
                    retList.append(cmd)
                    continue

                self.SendData(cmd)
                ret = self.RecvData()
                retList.append(ret)
            print "Pi to ZigBee costs %ds"%(time.time() - start)
            
            self.endDeviceStatusList = copy.deepcopy(retList)


    def GetStatus(self):
        statusDic = self._CmdLst2Dic(self.endDeviceStatusList)

        return statusDic


if __name__ == "__main__":
    proxy = USBProxy("/dev/ttyUSB0", 115200, 1)
    data = "11"
    ld = proxy.SendData(data)
    while ld < len(data):
        ld += proxy.SendData(data[ld:])

    echo = proxy.RecvData()
    if echo:
        print echo
        
    
    
