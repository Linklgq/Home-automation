#-*-coding: utf-8-*-
import socket
import struct
import json
from threading import Thread, Condition, Lock
import time
import requests

from usb_proxy import USBProxy
from account_utils import Encrypt2MD5

cmdDic = {}
cv = Condition()
lock = Lock()

class HeartBeatClient(object):
    
    def __init__(self, host, dev):
        self.host = host
        self.dev = dev
        self.checkin = False
        while not self.checkin:
            self.CheckIn()
        
        self.SetSock()
       
        self.cnt = 0
        #回复的json格式
        self.response = {"ret": 0, "msg": {},  "cnt": 0}

        #USB串口
        self.usbProxy = USBProxy(dev)
        self.usbProxy.start()


    def __del__(self):
        self.sock.close()
        self.usbProxy.Close()


    def CheckIn(self):
        postDic = {}

        piName = "pi_test"
        pwd = str(raw_input("input pwd for %s: "%piName))
        if len(pwd) < 4:
            print "please input password longer than 4"
            return

        md5Pwd = Encrypt2MD5(pwd)

        postDic["piName"] = piName
        postDic["pwd"] = md5Pwd
        
        resp = requests.post("http://120.78.69.45:5000/api/checkin", json.dumps(postDic))
        print resp.text

        if resp.status_code != 200:
            self.checkin = False
        
        else:
            self.checkin = True


    def PrepareResp(self, ret, msg, cnt):
        response = {}
        response["ret"] = ret
        response["msg"] = msg
        if isinstance(msg, dict):
            msg["cnt"] = cnt

        return response


    def SetSock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #keepalive setting
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 60)
        self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL,120)
        self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3)

        try:
            self.sock.connect(self.host)
            print("connect to {host}: succ".format(host=self.host))
        except Exception as e:
            print(e.__str__())


    def KeepAlive(self, period):
        """
        only send heart beat package
        recieve action will be done in worker thread
        """
        print("KeepAlive starts")
        cnt = 0
        while True:
            try:
                cnt += 1
                self.sock.sendall(struct.pack("i", 0))
                print("KeepAlive: Sent heartbeat package %d"%cnt)

            except Exception as e:
                print("KeepAlive: Connection broken, reconnecting...")
                self.SetSock()

            time.sleep(period)


    def Worker(self):
        print("Worker starts")
        cnt = 0
        global cmdDic
        while True:
            cnt += 1
            #cv.acquire()
            resp = self.sock.recv(4)
            if len(resp) == 0:
                print("Worker: connection broken, reconnect...")
                self.sock.close()
                self.SetSock()
                continue

            sz = struct.unpack("i", resp)[0]
            if sz == 0:
                continue
            
            resp = self.sock.recv(sz)
            if len(resp) == 0:
                print("Worker: connection broken, reconnect")
                self.sock.close()
                self.SetSock()
                continue

            print("Worker: ", resp)
            #lock.acquire()

            cmdDic = json.loads(resp)
            if cmdDic.get("cmd", None) != "check":
                self.usbProxy.Send2USB(cmdDic)
                self.cnt += 1
                status = self.usbProxy.GetStatus()
            
            else:
                status = self.usbProxy.GetLastStatus()

            response = self.PrepareResp(0, status, self.cnt)
            
            respJson = json.dumps(response)

            #apply http post to feedback
            resp = requests.post("http://120.78.69.45:5000/api/feedback", respJson)
            if resp.status_code == 200:
                print("feedback succ")
            else:
                print("feedback fail")


    
    def Run(self):
        #heart beat frequency
        period = 120

        keepAlive = Thread(target=self.KeepAlive, args=(period, ))
        keepAlive.setDaemon(1)
        keepAlive.start()

        self.Worker()


def main():
    global cmdDic
    host = ("120.78.69.45", 12580)
    dev = "/dev/ttyUSB0"

    client = HeartBeatClient(host, dev)
    client.Run()

           

if __name__ == "__main__":
    main()
