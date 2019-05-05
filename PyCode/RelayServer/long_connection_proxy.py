#-*-coding: utf-8-*-

from threading import Thread, Condition
import struct
import socket
import json
import requests
import sys
import time

if sys.version_info[0] == 2:
    from Queue import Queue
else:
    from queue import Queue


class HeartBeatServer(Thread):
    """
    长连接, 周期性心跳, push功能
    """
    QueSize = 10 
    def __init__(self, host):
        self.host = host
        
        #self.cmdDic = {}
    
        #use Queue to synchronize threads
        self.cmdQue = Queue(self.QueSize)

        self.SetSock()

        #用于Pusher与SetDic同步
        self.cv = Condition()

        super(self.__class__, self).__init__()

#    def SetDic(self, cmdDic):
#        #pass cmdDic to long connection
#        self.cv.acquire()
#        self.cmdDic = cmdDic
#        self.cv.notify_all()
#        self.cv.release()
#

    def Push(self, cmdDic):
        #block if the Queue is full
        self.start = time.time()
        self.cmdQue.put(cmdDic)
        print "Pushed {dic}".format(dic = cmdDic)

    def SetSock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.host)
        self.sock.listen(5)

    def run(self):
        while True:
            conn, addr = self.sock.accept()
            print addr
            keepAlive = Thread(target = self.KeepAlive, args = (conn, ))
            keepAlive.setDaemon(1)
            keepAlive.start()
            print "keepAlive daemon {tid} started".format(tid = keepAlive.ident)

            worker = Thread(target = self.Pusher, args = (conn, ))
            worker.start()
            print "worker {tid} started".format(tid = worker.ident)


    def Pusher(self, conn):
        """
        long connection proxy
        """
        while True:
           # self.cv.acquire()
           # if len(self.cmdDic) == 0:
           #     self.cv.wait()
       
            #this will block if cmdQueue is empty
            cmdDic = self.cmdQue.get()
            print "Get from Queue: {cmd}".format(cmd = cmdDic)
            cmdJson = json.dumps(cmdDic)

            try:
                conn.sendall(struct.pack("i", len(cmdJson))+cmdJson)
                #self.cmdDic = {}
                print "Pusher done"
                print "Pusher costs %ds"%(time.time() - self.start)

            except:
                print "Connection Broken, exit"
                conn.close()
                #通过flask api通知手机客户端树梅派断开了
                err = json.dumps({"ret": -2, "msg": "The connection between Pi and Relay server is broken"})
                resp = requests.post("http://127.0.0.1:5000/api/feedback", err)
                break


    def KeepAlive(self, conn):
        cnt = 0
        while True:
            cnt += 1
            szbuf = conn.recv(4)
            if len(szbuf) == 0:
                #connection broken
                print "connection broken"
                conn.close()
                break

            sz = struct.unpack("i", szbuf)[0]
            if sz == 0:
                #heartBeat package
                try:
                    conn.sendall(struct.pack("i", 0))
                    print "Answer hearBeat package %d"%cnt
                except:
                    print "Connection broken, exit"
                    conn.close()

