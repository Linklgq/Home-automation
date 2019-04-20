from flask import Flask
from flask import request
import json
from threading import Thread, Lock
import socket
import struct
from copy import deepcopy
import time

lock = Lock()
cmdDic = {}
feedBack = {}


app = Flask(__name__)

@app.route("/index", methods=["POST"])
def CmdServer():
    global feedBack
    global cmdDic

    feedBackCopy = deepcopy(feedBack)
    if request.method != "POST":
        return json.dumps({"ret":-1, "msg":"Post method only"})
    lock.acquire()
    print(request.data)
    dataDic = json.loads(request.data.decode("utf-8"))
    if cmdDic != dataDic:
        cmdDic = deepcopy(dataDic)
    else:
        lock.release()
        return json.dumps(cmdDic)
    print(cmdDic)
    lock.release()

    while feedBack == feedBackCopy:
        print("sleep")
        time.sleep(1)

    return json.dumps(feedBack)  


class ConnPi(Thread):
    """
    接受树梅派连接的长连接
    """
    def __init__(self, port):
        self.port = port
        self.cmdCopy = {} #用于分辨是否产生了新命令，需要深层复制
        self.SetSocket()
        super(ConnPi, self).__init__()

    def SetSocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.port))
        self.sock.listen(5)
        print("Long connection with Pi listen as %d"%self.port)

    def ServePi(self, conn):
        global cmdDict
        global feedBack

        while True:
            lock.acquire()
            if len(cmdDic) != 0 and cmdDic != self.cmdCopy:
                self.cmdCopy = deepcopy(cmdDic)
                cmdJson = json.dumps(cmdDic)
                cmdJson = cmdJson.encode("utf-8")
                conn.send(struct.pack("i", len(cmdJson)))
                conn.send(cmdJson)
               
                #wait feedback
                retBuf = conn.recv(4)
                while len(retBuf) ==  0:
                    retBuf = conn.recv(4)

                retSize = struct.unpack("i", retBuf)[0]
                buf = b""
            
                while retSize >  0:
                    tempBuf = conn.recv(retSize)
                    buf += tempBuf
                    retSize -= len(tempBuf)
                
                buf = buf.decode("utf-8")
                retDic = json.loads(buf)
                feedBack = deepcopy(retDic)
            lock.release()    
            time.sleep(0.1)

    def run(self):
        while True:
            conn, addr = self.sock.accept()
            print(addr)
            self.ServePi(conn)
    
def main():
    pi = ConnPi(12580)
    pi.start()
    
    app.run(host="0.0.0.0")

if __name__ == "__main__":
    main()
