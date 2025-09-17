# -*- coding: utf-8 -*-
#encoding:utf-8

# pip install mysqlclient
import MySQLdb

import sys
sys.path.append("..") 
from config import conf as CONF

class tomysql():
    def __init__(self,local=CONF['SQL']['local'],user=CONF['SQL']['user'],pwd=CONF['SQL']['pwd'],library=CONF['SQL']['library'],port=CONF['SQL']['port']):
        self.local = local
        self.user = user
        self.port = port
        self.pwd = pwd
        self.library = library
        self.db = None
        self.db = MySQLdb.connect(
            host = self.local, #服务器地址
            port = self.port, #服务器端口号
            user = self.user, #用户名
            passwd = self.pwd,#密码
            db = self.library, #需要操作的表格，可以在这里强调，也可以在sql语句中单独说明
            charset = 'utf8' #编码式附上原文出处链接及本声明。
        )
    
    # 获取游标
    def getcursor(self):
        cursor = self.db.cursor()
        return cursor

    # 短链接 执行sql 完毕自动关闭链接
    def setSql(self,strs,vals=()):
        if CONF['SQL']['printSql']:
            print (strs%vals)

        cursor = self.getcursor()
        re = True
        data = None
        try:
            cursor.execute(strs,vals)
            self.db.commit()
            data = cursor.fetchall()
            if CONF['SQL']['printSql']:
                print (data)
        except Exception as e:
            # Rollback in case there is any error
            re = False
            # data = self.db.rollback()
            data = e
            print ('sql error : %s'%e)
        # 关闭游标
        cursor.close()
        return re,data

    # 长连接 执行sql后手动关闭链接
    def setSqlDoing(self,strs,vals=()):
        if CONF['SQL']['printSql']:
            print (strs%vals)

        cursor = self.getcursor()
        re = True
        data = None
        try:
            cursor.execute(strs,vals)
            self.db.commit()
            data = cursor.fetchall()
            if CONF['SQL']['printSql']:
                print (data)
        except Exception as e:
            # Rollback in case there is any error
            re = False
            # data = self.db.rollback()
            data = e
            print ('sql error : %s'%e)
        # 关闭游标
        cursor.close()
        return re,data

    def close(self):
        # 关闭数据库连接
        self.db.close()

if __name__ == "__main__":
    sq = tomysql()
    sq.setSql('SELECT VERSION()')
    # MySQLdb.connect(host="127.0.0.1",user="root",passwd="123123",db="pigs",charset="utf8")

