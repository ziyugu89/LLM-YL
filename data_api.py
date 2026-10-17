# -*- coding: utf-8 -*-
#encoding:utf-8
import time
import redis
from flask import request

from config import conf as CONF
from utils import user
from llm_master import api
from llm_master import hospital_feed


def _viewer_from(info):
    return {
        "id": str(info[0]),
        "name": str(info[1] or ""),
        "roles": [str(item) for item in info[3]],
        "pcode": str(info[5] or "") if len(info) > 5 else "",
    }

# 创建连接对象
rds = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def _token():
    return request.headers.get(CONF["TokenKey"]) or ""


def _listed(loader):
    ret = {"code": 20001, "data": "查询失败"}
    ok, data = loader(_token())
    if ok:
        ret["code"] = 20000
    ret["data"] = data
    return ret

def addbingli():
    ret = {
        'code': 20000,
        'data': '添加成功'
    }
    req = request.get_json()
    ok, message = user.addBingli(_token(), req)
    if not ok:
        ret['code'] = 20001
        ret['data'] = message
    return ret

def getbingli():
    return _listed(user.getBingli)

def getbingliBH():
    return _listed(user.getBingliList)
def llm():
    ret = {
        'code': 20001,
        'data': '查询失败'
    }
    try:
        token = _token()
        if not token:
            print('Token is missing or invalid')
            return ret

        req = request.get_json()
        if not req or 'query' not in req:
            print('Invalid request data:', req)
            return ret
            
        use_agent = req.get('use_agent', False)  # 新增参数，决定是否使用Agent

        rq, rf = user.getBingliList(token)
        records = []
        if rq and isinstance(rf, dict):
            records = [item.get('text') or '' for item in rf.get('list') or []]
        elif not rq:
            ret['data'] = rf or '请重新登录'
            return ret

        role_names = []
        viewer = None
        known, info = user.get_user_name(token)
        if known and info and len(info) >= 5:
            role_names = [str(item) for item in list(info[3]) + list(info[4])]
            viewer = _viewer_from(info)
        response_from_model = api.answer(req['query'], records, token, use_agent, role_names, viewer)
        ret['code'] = 20000
        ret['data'] = {
            "choices": [
                {
                    "message": {
                        "content": response_from_model["content"]
                    }
                }
            ],
            "actions": response_from_model["actions"],
        }
    except Exception as ex:
        print('Unexpected error:', str(ex))
        ret['data'] = '暂时无法回答，请稍后再试'
    return ret

def hospital():
    ret = {'code': 20001, 'data': '查询失败'}
    try:
        token = _token()
        known, info = user.get_user_name(token)
        if not known or not info or len(info) < 4:
            ret['data'] = '请重新登录'
            return ret
        req = request.get_json() or {}
        kind = req.get('kind') if req.get('kind') in ('slots', 'queue', 'reports') else 'slots'
        viewer = _viewer_from(info)
        ret['code'] = 20000
        ret['data'] = hospital_feed.query(kind, req.get('query') or '', viewer)
    except Exception as ex:
        print('hospital error:', str(ex))
        ret['data'] = '暂时无法读取医院资料'
    return ret

def guide():
    ret = {'code': 20001, 'data': '查询失败'}
    req = request.get_json() or {}
    topic = req.get('topic') if req.get('topic') in ('register', 'place') else 'place'
    try:
        ret['code'] = 20000
        ret['data'] = api.guide(topic, req.get('query') or '')
    except Exception as ex:
        print('guide error:', str(ex))
        ret['data'] = '暂时无法查询就诊引导'
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
    
    rs, use = user.get_user_name(_token())
    if not rs or not use:
        ret['code'] = 20001
        ret['data'] = '请重新登录'
        return ret
    rdsList = []
    while rds.llen(use[0]) > 0:
        data = rds.rpop(use[0])
        t,text = data.split('|', 1)
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
        setRedis({'bingid': req['bingid'], 'time': item, 'text': req['message']})
    return ret
