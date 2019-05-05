#-*-coding: utf-8-*-

"""
this is the proxy module connected to the sqlit3 database, 
which is used as the database of account info.
"""

import sqlite3
import traceback

class DBProxy(object):
    """
    database proxy
    """

    def __init__(self, db):
        self.db = db
        
        self.Connect()

        self.CreateTable("account")
        

    def __del__(self):
        self.conn.close()
    

    def Connect(self):
        self.conn = sqlite3.connect(self.db)
        print "Connect to db {name} succ".format(name = self.db)

        self.proxy = self.conn.cursor()
        print "Create cursor object to {name} succ".format(name = self.db)

       
    def CreateTable(self, tableName):
        try:
            cmd = "CREATE TABLE {name} (piName text PRIMARY KEY NOT NULL, passwd text NOT NULL)".format(name = tableName)
            self.proxy.execute(cmd)
            self.conn.commit()
        
        except Exception, e:
            if "already exists" in e.__str__():
                pass
            else:
                print e.__str__()
                traceback.print_exc()


    def _Insert(self, key, value, tableName):
        
        cmd = "INSERT INTO {table} VALUES (?, ?)".format(table = tableName)
        target = (key, value)

        self.proxy.execute(cmd, target)
        
        self.conn.commit()
        print "Insert {key} {value} in table {table} succ".format(key=key, value=value, table = tableName)


    def Store(self, key, value, tableName):
        if not self.Retrieve(key, tableName):
            self._Insert(key, value, tableName)

        else:
            self._Update(key, value, tableName)
        


    def Retrieve(self, key, tableName):

        cmd = "SELECT * FROM {table} WHERE piName = ?".format(table = tableName)
        target = (key, )
        
        self.proxy.execute(cmd, target)
        
        self.conn.commit()

        ret = self.proxy.fetchone()

        if not ret:
            return None

        return ret[1]


    def DropTable(self, tableName):
        cmd = "DROP TABLE {table}".format(table = tableName)
        print cmd
        self.proxy.execute(cmd)
        
        self.conn.commit()
        print "Delete table {name} succ".format(name = tableName)

   
    def DeleteItem(self, key, tableName):
        cmd = "DELETE FROM {table} WHERE piName = ?".format(table = tableName)

        target = (key, )
        self.proxy.execute(cmd, target)

        self.conn.commit()
        print "Delete entry {key} in {table} succ".format(key = key, table = tableName)

    
    def _Update(self, key, value, tableName):
        cmd = "UPDATE {table} SET passwd = ? WHERE piName = ?".format(table = tableName)
        target = (value, key)

        self.proxy.execute(cmd, target)

        self.conn.commit()
        print "Update {key} in table {table} succ".format(key = key, table = tableName)




if __name__ == "__main__":
    db = DBProxy("account.db")
    db.Connect()

    tableName = "account"
    db.CreateTable(tableName)

    db.Store("pi1", Encrypt2MD5("test1"), tableName)
    db.Store("pi2", Encrypt2MD5("test2"), tableName)

    pwd1 =  db.Retrieve("pi1", tableName)

    assert(Encrypt2MD5("test1") == pwd1)
    pwd2 = db.Retrieve("pi2", tableName)
    assert(Encrypt2MD5("test2") == pwd2)

    db.DeleteItem("pi1", tableName)
    db.DeleteItem("pi2", tableName)

    db.DropTable(tableName)

