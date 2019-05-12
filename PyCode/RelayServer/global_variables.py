#-*-coding: utf-8-*-
"""
global variabls with lock
"""

from threading import Condition
import copy

class GlobalVal(object):
    
    dicVal = {
        "feedback": {},
        "status": {}, #store last feedback
    }
    
    cv = Condition()

    @staticmethod
    def GetFeedBack():
        GlobalVal.cv.acquire()
        
        if len(GlobalVal.dicVal["feedback"]) == 0:
            GlobalVal.cv.wait()

        retDic = copy.deepcopy(GlobalVal.dicVal["feedback"])
        GlobalVal.dicVal["feedback"] = {}

        GlobalVal.cv.release()
        return retDic

    @staticmethod
    def SetFeedBack(feedback):
        GlobalVal.cv.acquire()
        GlobalVal.dicVal["feedback"] = copy.deepcopy(feedback)
        GlobalVal.dicVal["status"] = copy.deepcopy(feedback)

        GlobalVal.cv.notify()
        GlobalVal.cv.release()

        return True
        
    @staticmethod
    def GetStatus():
        return GlobalVal.dicVal["status"]
