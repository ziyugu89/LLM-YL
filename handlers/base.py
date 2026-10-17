# -*- coding: utf-8 -*-
#encoding:utf-8
import sys

import json,os,time,datetime

import uuid  #UUID 生成库

##################################################

sys.path.append("..") 
from config import conf as CONF
from mydb.mq import tomysql

from flask import Flask,url_for,request,render_template,redirect,session
from functools import wraps

# 过滤用户
def check_sess(func):
    @wraps(func)
    def check_login(*args, **kwargs):
        try:
            # print (head)
            session_id = request.headers[CONF['TokenKey']]
            # print session_id
            if session_id and type(session_id) == str:
                sqls = tomysql()
                # 检查token对应用户
                sql = '''
                    SELECT `user`.id,`user`.stime FROM `user` WHERE `user`.token=%s AND `user`.`status`=1
                '''
                rs,rf = sqls.setSql(sql, (session_id,))
                if rs != False and len(rf) != 0:
                    # 判断下时间是否超过
                    new_time = int(time.time())
                    res = new_time - rf[0][1]
                    # 是否登录超时
                    if res > CONF['userOut']:
                        print (u'token 验证失败,请重新登录')
                        # 登录超时
                        return {'code': 20001,'data': u'登录超时'}
                    else:
                        print (u'token 验证通过')
                        return func(*args, **kwargs)
                else:
                    return {'code': 20001,'data': u'请重新登录'}
            else:
                print (u'token 验证失败 请求缺少token信息')
                return {'code': 20001,'data': u'请重新登录'}
        except Exception as ex:
            print (u'异常错误：%s'%str(ex))
            return {'code': 20001,'data': str(ex)}
        
    return check_login

# 获取并写入token
def set_user(id):
    token = str(uuid.uuid1())
    sqls = tomysql()
    # 更新token
    sql = '''
        UPDATE `user` SET `token`=%s , `stime`=%s  WHERE `id`=%s
    '''
    rs,rf = sqls.setSql(sql, (token, int(time.time()), id))
    if rs != False:
        return True,token
    else:
        return False,rf

# 根据token注销用户
def set_user_token(token):
    sqls = tomysql()
    # 更新token
    sql = '''
        UPDATE `user` SET `token`='' WHERE `token`=%s
    '''
    rs,rf = sqls.setSql(sql, (token,))
    if rs != False:
        return True
    else:
        return False