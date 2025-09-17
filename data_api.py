# -*- coding: utf-8 -*-
#encoding:utf-8
import sys
import json,os,time,datetime
from flask import Flask,url_for,request,render_template,redirect,session
from werkzeug.utils import secure_filename

from handlers import base
from config import conf as CONF
from utils import user
from master import api
import redis

# 创建连接对象
rds = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
def getFun(fun):
    ret = {
        'code': 20001,
        'data': ''
    }
    req = request.get_json()
    try:
        token = request.headers[CONF['TokenKey']]
    except Exception as ex:
        print('token error:', str(ex))
        token = ""
    # print(req, token)
    # 获取用户列表
    rs, rq = fun(req, token)
    # print ('rf = ',rq)
    if rs == True:
        ret['code'] = 20000
        ret['data'] = rq
    else:
        ret['data'] = rq
    return ret

def addbingli():
    ret = {
        'code': 20000,
        'data': '添加成功'
    }
    try:
        token = request.headers[CONF['TokenKey']]
    except Exception as ex:
        print('token error:', str(ex))
        token = ""
    req = request.get_json()
    user.addBingli(token, req)
    return ret

def getbingli():
    ret = {
        'code': 20001,
        'data': '查询失败'
    }
    try:
        token = request.headers[CONF['TokenKey']]
    except Exception as ex:
        print('token error:', str(ex))
        token = ""
    rq,rf = user.getBingli(token)
    if rq == True:
        ret['code'] = 20000
    ret['data'] = rf
    return ret

def getbingliBH():
    ret = {
        'code': 20001,
        'data': '查询失败'
    }
    try:
        token = request.headers[CONF['TokenKey']]
    except Exception as ex:
        print('token error:', str(ex))
        token = ""
    rq,rf = user.getBingliList(token)
    if rq == True:
        ret['code'] = 20000
    ret['data'] = rf
    return ret
def llm():
    ret = {
        'code': 20001,
        'data': '查询失败'
    }
    try:
        token = request.headers.get(CONF['TokenKey'])
        if not token:
            print('Token is missing or invalid')
            return ret

        req = request.get_json()
        if not req or 'query' not in req:
            print('Invalid request data:', req)
            return ret
            
        use_agent = req.get('use_agent', False)  # 新增参数，决定是否使用Agent

        rq, rf = user.getBingliList(token)
        if rq:
            # print("病历信息获取成功")
            if use_agent:
                response_from_model = api.agent_message(req['query'], [i['text'] for i in rf['list']])
            else:
                response_from_model = api.message(req['query'], [i['text'] for i in rf['list']])
            # print("模型返回的回答：", response_from_model)  # 打印模型的返回值
            ret['code'] = 20000
            ret['data'] = {
                "choices": [
                    {
                        "message": {
                            "content": response_from_model
                        }
                    }
                ]
            }
        else:
            print("病历信息获取失败:", rq, rf)
    except Exception as ex:
        print('Unexpected error:', str(ex))
    return ret

def setRedis(req):
    ret = {
        'code': 20000,
        'data': '添加成功'
    }
    rds.lpush(req['bingid'], str(req['time'])+'|'+req['text'])
    return ret

def getRedis():
    ret = {
        'code': 20000,
        'data': ''
    }
    
    try:
        token = request.headers[CONF['TokenKey']]
    except Exception as ex:
        print('token error:', str(ex))
        token = ""
    rs,use = user.get_user_name(token)
    rq = rds.lrange(use[0], 0, -1)
    rdsList = []
    while rds.llen(use[0]) > 0:
        data = rds.rpop(use[0])
        t,text = data.split('|')
        if int(time.time()) - int(t) > 0 and int(time.time()) - int(t) < 60:
            ret['code'] = 20000
            ret['data'] = text
            return ret
        elif int(time.time()) - int(t) > 60:
            continue
        else:
            rdsList.append((use[0], t+'|'+text))
    for item in rdsList:
        rds.lpush(item[0], item[1])
    return ret

def setmessage():
    ret = {
        'code': 20000,
        'data': ''
    }
    req = request.get_json()
    for item in req['times']:
        print(item)
        setRedis({'bingid': req['bingid'], 'time': item, 'text': req['message']})
    return ret
