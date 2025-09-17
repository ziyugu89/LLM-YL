# -*- coding: utf-8 -*-
#encoding:utf-8
import sys
import json,os,time,datetime
from flask import Flask,url_for,request,render_template,redirect,session

from handlers import base
from utils import user
from config import conf as CONF

def login():
    # 处理跨域请求
    ret = {
        'code': 20000,
        'data': ''
    }
    req = request.get_json()
    # 判断用户名密码 获取用户ID
    rs, rf = user.get_user(req['username'],req['password'])
    if rs == True:
        res, token = base.set_user(rf)
        # 登录失败
        if res == False:
            ret['code'] = 20001
        ret['data'] = {'token':token}
    else:
        ret['code'] = 20001
        ret['data'] = u'用户名，密码错误'
    return ret

def logout():
    ret = {
        'code': 20000,
        'data': 'success'
    }
    token = request.headers[CONF['TokenKey']]
    print (u'注销token ： %s'%token)
    # 清理token 注销用户
    base.set_user_token(token)
    return ret

def info():
    ret = {
        'code': 20001,
        'data': ''
    }
    token = request.args.get("token")
    # 获取用户信息
    rs, rf = user.get_user_name(token)
    print(rf)
    if rs == True:
        ret['code'] = 20000
        ret['data'] = {
            'id': rf[0],
            'name': rf[1],
            'roles': rf[3],# 用户角色 多种用,分割
            'expireAt': (int(rf[2])+CONF['userOut'])*1000,# token过期时间
            'token': token,
        }
        ret['message'] = u'登录成功'
    else:
        ret['data'] = u'获取用户信息失败。'
    return ret

def getlist():
    ret = {
        'code': 20001,
        'data': ''
    }
    req = request.get_json()
    # 获取用户列表
    rs, rf = user.get_user_list(req)
    print ('rf = ',rf)
    if rs == True:
        ret['code'] = 20000
        ret['data'] = rf
    else:
        ret['data'] = u'获取用户列表失败。'
    return ret

def addUser():
    ret = {
        'code': 20001,
        'data': ''
    }
    req = request.get_json()
    rs,rf = user.set_user(req)
    if rs == True:
        ret['code'] = 20000
        ret['data'] = rf
    else:
        ret['data'] = rf
    return ret

def upUser():
    ret = {
        'code': 20001,
        'data': ''
    }
    req = request.get_json()
    rs,rf = user.up_user(req)
    if rs == True:
        ret['code'] = 20000
        ret['data'] = rf
    else:
        ret['data'] = rf
    return ret

def delUser():
    ret = {
        'code': 20001,
        'data': ''
    }
    req = request.get_json()
    rs,rf = user.del_user(req)
    if rs == True:
        ret['code'] = 20000
        ret['data'] = rf
    else:
        ret['data'] = rf
    return ret

def upUserPwd():
    ret = {
        'code': 20001,
        'data': ''
    }
    req = request.get_json()
    token = request.headers[CONF['TokenKey']]
    rs,rf = user.up_user_pwd(token,req)
    if rs == True:
        ret['code'] = 20000
        ret['data'] = rf
    else:
        ret['data'] = rf
    return ret

