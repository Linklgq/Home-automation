#-*-coding: utf-8-*-

import hashlib
from account_db_proxy import DBProxy



def Encrypt2MD5(string):
    salt = "yjf"

    md = hashlib.md5()

    md.update(salt + string)

    return md.hexdigest()



def VerifyAcct(piName, md5Pwd):
    dbName = "account.db"
    tableName = "account"
    dbProxy = DBProxy(dbName)
    realPwd = dbProxy.Retrieve(piName, tableName)

    if md5Pwd == realPwd:
        return True

    return False
