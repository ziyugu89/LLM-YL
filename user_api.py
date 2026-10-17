# -*- coding: utf-8 -*-
#encoding:utf-8
from flask import request

from handlers import base
from utils import user
from config import conf as CONF

_LOGIN_ROLES = {"use": "2", "doctor": "3", "admin": "1"}

def login():
    # 处理跨域请求
    ret = {
        'code': 20000,
        'data': ''
    }
    req = request.get_json() or {}
    wanted = str(req.get('role') or '')
    if wanted not in _LOGIN_ROLES:
        ret['code'] = 20001
        ret['data'] = '请先选择患者、医生或管理员'
        return ret
    # 判断用户名密码 获取用户ID
    rs, rf = user.get_user(req.get('username'), req.get('password'))
    if rs != True:
        ret['code'] = 20001
        ret['data'] = '用户名或密码错误'
        return ret
    if _LOGIN_ROLES[wanted] not in rf["roles"].split(","):
        ret['code'] = 20001
        ret['data'] = '这个账号不能用所选身份登录'
        return ret
    res, token = base.set_user(rf["id"])
    if res == False:
        ret['code'] = 20001
        ret['data'] = '登录失败'
        return ret
    ret['data'] = {'token': token}
    return ret

def logout():
    ret = {
        'code': 20000,
        'data': 'success'
    }
    token = request.headers[CONF['TokenKey']]
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
    if rs == True:
        ret['code'] = 20000
        ret['data'] = {
            'id': rf[0],
            'name': rf[1],
            'roles': rf[3],# 用户角色 多种用,分割
            'pcode': rf[5] if len(rf) > 5 else '',
            'expireAt': (int(rf[2])+CONF['userOut'])*1000,# token过期时间
            'token': token,
        }
        ret['message'] = u'登录成功'
    else:
        ret['data'] = u'获取用户信息失败。'
    return ret

def profile():
    ret = {'code': 20001, 'data': '请重新登录'}
    token = request.headers.get(CONF['TokenKey']) or ""
    rs, rf = user.get_user_name(token)
    if rs == True:
        names = {"admin": "管理员", "use": "患者", "doctor": "医生"}
        ret['code'] = 20000
        ret['data'] = {
            'id': rf[0],
            'name': rf[1],
            'roles': rf[3],
            'roleText': "、".join(names.get(item, item) for item in rf[3]),
            'pcode': rf[5] if len(rf) > 5 else '',
        }
    return ret

def getlist():
    ret = {
        'code': 20001,
        'data': ''
    }
    token = request.headers.get(CONF['TokenKey']) or ""
    known, info = user.get_user_name(token)
    if not known or not info or len(info) < 4:
        ret['data'] = '请重新登录'
        return ret
    if 'admin' not in info[3] and 'doctor' not in info[3]:
        ret['data'] = '当前身份不能管理人员'
        return ret
    req = request.get_json() or {}
    req['viewer_roles'] = info[3]
    # 获取用户列表
    rs, rf = user.get_user_list(req)
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

