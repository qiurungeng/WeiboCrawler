import sqlite3


class FollowedListTable():
    def __init__(self):
        self.dbstr = "weibo.db"
        con = sqlite3.connect(self.dbstr)
        cur = con.cursor()
        cur.execute(
            'create table if not exists followlist(uid int(10) primary key,followed boolean)')
        cur.close()
        con.close()

    def addFollow(self,uid):
        """添加uid到数据库"""
        con = sqlite3.connect(self.dbstr)
        cur = con.cursor()
        cur.execute(" INSERT INTO followlist(uid,followed) select ?,? "+
                     "WHERE NOT EXISTS "
                    "(SELECT * FROM followlist WHERE uid=?);", (uid,False,uid))
        con.commit()
        cur.close()
        con.close()

    def addFollowFromList(self,uid_list):
        """uid列表批量添加到数据库"""
        if not len(uid_list)>0:
            raise RuntimeError('列表为空！')
        con = sqlite3.connect(self.dbstr)
        cur = con.cursor()
        for uid in uid_list:
            cur.execute(" INSERT INTO followlist(uid,followed) select ?,? " +
                        "WHERE NOT EXISTS "
                        "(SELECT * FROM followlist WHERE uid=?);", (uid, False, uid))
        con.commit()
        cur.close()
        con.close()

    def updateFollow(self,uid):
        """标记数据库中对应uid状态为已关注"""
        con = sqlite3.connect(self.dbstr)
        cur = con.cursor()
        cur.execute("UPDATE followlist SET followed=? WHERE uid=?", (True,uid))
        con.commit()
        cur.close()
        con.close()

    def getUnfollowList(self):
        """获取数据库中仍未关注的uid"""
        con = sqlite3.connect(self.dbstr)
        cur = con.cursor()
        cur.execute("SELECT uid FROM followlist WHERE followed=0")
        unfollow_list=[]
        # con.commit()
        for item in cur.fetchall():
            unfollow_list.append(item[0])
        cur.close()
        con.close()
        return unfollow_list

    def getAll(self):
        """获取数据库中所有uid"""
        con = sqlite3.connect(self.dbstr)
        cur = con.cursor()
        cur.execute("SELECT uid FROM followlist")
        uid_list = []
        # con.commit()
        for item in cur.fetchall():
            uid_list.append(item[0])
        cur.close()
        con.close()
        return uid_list

    def reset(self):
        con = sqlite3.connect(self.dbstr)
        cur = con.cursor()
        cur.execute("UPDATE followlist SET followed=? ",(False,))
        con.commit()
        cur.close()
        con.close()

# test
# if __name__ =='__main__':
#     db=FollowedListTable()
#     print(len(db.getUnfollowList()))
#     db.addFollowFromList([1,2,3,4,5,6])
#     # db.addFollow(111)
#     # db.updateFollow(1231)
#     # print(db.getUnfollowList())
#     # for id in db.getUnfollowList():
#     #     db.updateFollow(id)
#     db.reset()