import requests
import random
import json
import time

from account_utils import Encrypt2MD5



cmdDic = {"red": "on", "blue": "off", "green": "on"}

def getRandCmd():
    cmd = {}
    for each in cmdDic.items():
        cmd[each[0]] = random.choice(["on", "off"])

    return cmd

def main():
    succ = 0
    fail = 0
    duration = 0
    i = 0

    piName = "pi_test"
    pwd = str(raw_input("input passwd for %s: "%piName))
    md5Pwd = Encrypt2MD5(pwd)
   
    pkg = {}
    pkg["piName"] = piName
    pkg["pwd"] = md5Pwd
    
    for i in range(100):
        
#        t = str(raw_input("enter t: "))
#        if not t.isdigit():
#            continue

        t = random.randint(0, 5)
#        print("sleep %s"%t)
        time.sleep(t)

        cmd = getRandCmd()
        cmd["Cnt"] = i
        pkg["cmd"] = cmd

        #i += 1
        cmdJson = json.dumps(pkg)
        print(cmdJson)
        start = time.time()
        resp = requests.post("http://120.78.69.45:5000/api/sendsignal", cmdJson)
        duration = time.time() - start

        if resp.status_code != 200:
            fail += 1
            print("fail to sendsignal, status_code: %d"%resp.status_code)

        else:
            data = json.loads(resp.content.decode("utf-8"))
            print("ret: %d, msg: %s, duration: %f"%(data["ret"], data["msg"], duration))
            if data["ret"] != 0:
                fail += 1
            
            else:
                succ += 1


    print("succ: %d, fail: %d"%(succ, fail))

if __name__ == "__main__":
    main()
