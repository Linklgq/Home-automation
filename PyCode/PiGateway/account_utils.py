#-*-coding: utf-8-*-

import hashlib
#from account_db_proxy import DBProxy
#
#dbName = "account.db"
#tableName = "account"
#dbProxy = DBProxy(dbName)
#
#
def Encrypt2MD5(string):
    salt = "yjf"

    md = hashlib.md5()

    md.update(salt + string)

    return md.hexdigest()


#def VerifyAcct(piName, md5Pwd):
#    realPwd = dbProxy.Retrieve(piName)
#
#    if md5Pwd == realPwd:
#        return True
#
#    return False
