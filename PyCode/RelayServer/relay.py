#-*-coding: utf-8-*-
import socket
import struct
from threading import Thread, Condition
import json
import time
import random
import copy
from flask import Flask
from flask import request

from long_connection_proxy import HeartBeatServer
from account_utils import VerifyAcct
from account_db_proxy import DBProxy


feedback = {}
cv = Condition()


host = ("0.0.0.0", 12580)
pushProxy = HeartBeatServer(host)




app = Flask(__name__)

@app.route("/api/checkin", methods=["POST"])
def Checkin():
    #pi upload account info 
    global tableName

    reqData = request.data.decode("utf-8")
    
    reqDic = json.loads(reqData)

    piName = reqDic.get("piName", None)
    md5Pwd = reqDic.get("pwd", None)

    if not piName or not md5Pwd:
        return json.dumps({"ret": -4, "msg": "check in bad format"})

    dbName = "account.db"
    tableName = "account"
    dbProxy = DBProxy(dbName)
    dbProxy.Store(piName, md5Pwd, tableName)
    print md5Pwd

    return json.dumps({"ret": 0, "msg": "check in succ"})


@app.route("/api/register", methods=["POST"])
def Register():
    global tableName

    reqData = request.data.decode("utf-8")
    
    reqDic = json.loads(reqData)

    piName = reqDic.get(piName, None)
    md5Pwd = reqDic.get(pwd, None)

    if not piName or not md5Pwd:
        return json.dumps({"ret": -4, "msg": "register bad format"})

    ret = VerifyAcct(piName, md5Pwd)
    if not ret:
        return json.dumps({"ret": -5, "msg": "piName or passwd wrong"})

    return json.dumps({"ret": 0, "msg": "register succ"})
   

@app.route("/api/feedback", methods=["POST"])
def Feedback():
    global feedback
    ok = json.dumps({"ret": 0, "msg": "Feedback ok"})
    
    if request.method != "POST":
        return json.dumps({"ret":-1, "msg":"Post method only"})

    cv.acquire()
    feedback = json.loads(request.data.decode("utf-8"))
    print "feedback: ", feedback 
    #wake up one thread a time
    cv.notify()
    cv.release()

    return ok


@app.route("/api/sendsignal", methods = ["POST"])
def SendSignal():
    global pushProxy
    global feedback

    if request.method != "POST":
        return json.dumps({"ret":-1, "msg":"Post method only"})
        
    cmdDic = json.loads(request.data.decode("utf-8"))    

    piName = cmdDic.get("piName", None)
    pwd = cmdDic.get("pwd", None)
    if not piName or not pwd:
        return json.dumps({"ret": -4, "msg": "piName and passwd required"})

    ret = VerifyAcct(piName, pwd)
    if not ret:
        return json.dumps({"ret": -5, "msg": "piName or passwd wrong"})

    print "\nRecv: ", cmdDic

    cmdDic = cmdDic["cmd"]
    pushProxy.Push(cmdDic)

    #feedback global variable lock
    cv.acquire()
    if len(feedback) == 0:
        cv.wait()

    print "Send feedback to mobile"

    retDic = copy.deepcopy(feedback)
    feedback = {}
    cv.release()

    return json.dumps(retDic)


def main():
    pushProxy.start()
    app.run(host = "0.0.0.0")

if __name__ == "__main__":
    main()
