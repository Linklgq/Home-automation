import requests
import random
import json
import time

cmdDic = {"red": "on", "blue": "off", "green": "on"}

def getRandCmd():
    cmd = {}
    for each in cmdDic.items():
        cmd[each[0]] = random.choice(["on", "off"])

    return cmd

def main():
    succ = 0
    fail = 0
    for i in range(100):
        cmd = getRandCmd()
        cmdJson = json.dumps(cmd)
        print(cmdJson)
        data = requests.post("http://localhost:5000/index", cmdJson)
        if data.status_code != 200:
            fail += 1
        else:
            feedback = json.loads(data.content.decode("utf-8"))
            print(feedback)
            if feedback == cmd:
                succ += 1
            else:
                fail += 1
        #time.sleep(1)
    print("succ: %d, fail: %d"%(succ, fail))

if __name__ == "__main__":
    main()
