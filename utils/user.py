# -*- coding: utf-8 -*-
#encoding:utf-8
import sys

import json,os,time,datetime

##################################################

sys.path.append("..") 
# from config import conf as CONF
from mydb.mq import tomysql


# 通过用户名，密码获取用户ID
def get_user(user,pwd):
    sqls = tomysql()
    # 更新token
    sql = '''
        SELECT `user`.`id` FROM `user` WHERE `user`.`user`='%s' AND `user`.`pwd`='%s' AND `user`.`status`=1
    '''
    rs,rf = sqls.setSql(sql%(user,pwd))
    if rs != False and len(rf) != 0:
        return True,rf[0][0]
    else:
        return False,rf

# 通过token获取用户信息
def get_user_name(token):
    sqls = tomysql()
    # 获取用户信息
    sql = '''
        SELECT `user`.`id`,`user`.`name`,`user`.`stime`,`user`.`roles` FROM `user` WHERE `user`.`token`='%s' AND `user`.`status`=1
    '''
    rs,user = sqls.setSqlDoing(sql%(token))
    if rs != False and len(user) != 0:
        sql = '''
            SELECT `roles`.`name`,`roles`.`nid` FROM `roles` WHERE `roles`.`id` in (%s)
        '''
        rs,roles = sqls.setSqlDoing(sql%(user[0][3]))
        sqls.close()
        if rs != False and len(roles) != 0:
            new_user = list(user[0][:-1])
            new_roles = []
            new_nid = []
            for item in roles:
                new_roles.append(item[0])
                new_nid.append(item[1])
            new_user.append(new_roles)
            new_user.append(new_nid)
            return True,new_user
        else:
            return False,roles
        # 返回用户信息
        return True,user[0]
    else:
        sqls.close()
        return False,user

# 根据token注销用户
def set_user_token(token):
    sqls = tomysql()
    # 更新token
    sql = '''
        UPDATE `user` SET `token`='' WHERE `token`='%s'
    '''
    rs,rf = sqls.setSql(sql%(token))
    if rs != False:
        return True
    else:
        return False

# 获取用户列表
def get_user_list(req):
    sqls = tomysql()
    sql = '''
        SELECT `user`.`user`, `user`.stime, `user`.`name`,`user`.`id`,`user`.`roles`,`user`.`status` FROM `user` WHERE `user`.`status`=1 AND `user`.`id`<>1 LIMIT %s,%s
    '''
    limit = int(req['limit']) if 'limit' in req else 20
    vals = ((int(req['page']) - 1) * 20, limit)
    rs,users = sqls.setSqlDoing(sql%(vals))
    if rs != False and len(users) != 0:
        sql = '''
            SELECT COUNT(`user`.id) FROM `user` WHERE `user`.`status`=1 AND `user`.`id`<>1 
        '''
        rs,total = sqls.setSqlDoing(sql)
        sqls.close()
        return True,{
            "list":[{
                'user':i[0],
                'stime':i[1],
                'name':i[2],
                'id':i[3],
                'roles':i[4],
                'status':i[5]
            } for i in users],"total":total[0][0]}
    else:
        sqls.close()
        return True,{"list":[],"total":0}
    
# 创建用户
def set_user(req):
    sqls = tomysql()
    user = req['user'] if 'user' in req else ''
    pwd = req['pwd'] if 'pwd' in req else ''
    name = req['name'] if 'name' in req else ''
    roles = req['roles'] if 'roles' in req else []
    if user == '' or pwd == '':
        return False,u'创建失败'
    if name == '':
        name = user
    # 把权限转为串存储
    roles = ','.join([str(i) for i in roles])
    # 先检查账户是否已经创建
    sql = '''
        SELECT ``user`.`name` FROM `user` WHERE `user`.`user`='%s' AND `user`.`pwd`='%s'
    '''
    rs,users = sqls.setSqlDoing(sql%(user,pwd))
    if rs != False and len(users) != 0:
        sqls.close()
        return False,u'用户创建失败，账号已存在'
    else:
        sql = '''
            INSERT INTO `user`(`user`,`pwd`,`name`,`roles`,`status`) VALUES ('%s','%s','%s','%s',1)
        '''
        rs,users = sqls.setSqlDoing(sql%(user,pwd,name,roles))
        if rs != False:
            sqls.close()
            # 创建成功
            return True,u'账户创建成功'
        else:
            sqls.close()
            return False,u'用户创建失败'

# 修改用户信息 修改后清空token 强制被修改用户下线
def up_user(req):
    sqls = tomysql()
    sql = '''
        UPDATE `user` SET `token`='',`name`='%s',`roles`='%s'
    '''
    pwd = req['pwd'] if 'pwd' in req else ''
    name = req['name'] if 'name' in req else ''
    roles = req['roles'] if 'roles' in req else []
    if name == '':
        return False,u'用户信息修改失败'
    # 把权限转为串存储
    roles = ','.join([str(i) for i in roles])
    vals = [name,roles]
    if pwd != '' and pwd != None:
        sql += " ,`pwd`='%s'"
        vals.append(pwd)
    
    sql += " WHERE `id`='%s'"
    vals.append(str(req['id']))
    rs,rf = sqls.setSql(sql%tuple(vals))
    if rs != False:
        return True,u'用户信息修改成功'
    else:
        return False,u'用户信息修改失败'

# 用户除权 清空token status修改
def del_user(req):
    sqls = tomysql()
    sql = '''
        UPDATE `user` SET `token`='',`status`=0 WHERE `id`='%s'
    '''
    rs,rf = sqls.setSql(sql%(req['id']))
    if rs != False:
        return True,u'用户除权成功'
    else:
        return False,u'用户除权失败'

# 用户密码修改
def up_user_pwd(token,req):
    sqls = tomysql()
    sql = '''
        UPDATE `user` SET `pwd`='%s' WHERE `token`='%s'
    '''
    rs,rf = sqls.setSql(sql%(req['pwd'],token))
    if rs != False:
        return True,u'用户密码修改成功'
    else:
        return False,u'用户密码修改失败'
# 用户密码修改
def addBingli(token,req):
    sqls = tomysql()
    # 获取当前用户的id
    sql = '''
        SELECT `user`.`id` FROM `user` WHERE `user`.`token`='%s'
    '''
    rs,user = sqls.setSqlDoing(sql%(token))
    if rs != False and len(user) != 0:
        # 添加病历信息 创建时间：time 病患id：bingid 医生id：ysid 性别：gender 年龄：age 病患姓名：name 病历信息：text
        sql = '''
            INSERT INTO `bingli`(`time`,`bingid`,`ysid`,`gender`,`age`,`name`,`text`) VALUES ('%s','%s','%s','%s','%s','%s','%s')
        '''
        rs,rf = sqls.setSql(sql%(int(time.time()),req['bingid'],user[0][0],req['gender'],req['age'],req['name'],req['text']))
        if rs != False:
            sqls.close()
            # 创建成功
            return True,u'病历添加成功'
        else:
            sqls.close()
            return False,u'病历添加失败'

# 根据病患ID查询病历列表
def getBingliList(token):
    sqls = tomysql()
    # 获取当前用户的id
    sql = '''
        SELECT `user`.`id` FROM `user` WHERE `user`.`token`='%s'
    '''
    rs,user = sqls.setSqlDoing(sql%(token))
    if rs != False and len(user) != 0:
        # 添加病历信息创建时间：time 病患id：bingid 医生id：
        sql = '''
            SELECT `bingli`.`id`,`bingli`.`time`,`bingli`.`bingid`,(SELECT `user`.`name` FROM `user` WHERE `id`=`bingli`.`ysid`),`bingli`.`gender`,`bingli`.`age`,`bingli`.`name`,`bingli`.`text` FROM `bingli` WHERE `bingli`.`bingid`='%s' ORDER BY `bingli`.`time` DESC
        '''
        rs,bingli = sqls.setSqlDoing(sql%(user[0][0]))
        sqls.close()
        if rs != False and len(bingli) != 0:
            return True,{
                "list":[{
                    'id':i[0],
                    'time':i[1],
                    'bingid':i[2],
                    'ysid':i[3],
                    'gender':i[4],
                    'age':i[5],
                    'name':i[6],
                    'text':i[7]
                } for i in bingli]
            }
        else:
            return True,{"list":[]}
# 查询医生的病历列表
def getBingli(token):
    sqls = tomysql()
    # 获取当前用户的id
    sql = '''
        SELECT `user`.`id` FROM `user` WHERE `user`.`token`='%s'
    '''
    rs,user = sqls.setSqlDoing(sql%(token))
    if rs != False and len(user) != 0:
        # 添加病历信息 创建时间：time 病患id：bingid 医生id：ys
        sql = '''
            SELECT `bingli`.`id`,`bingli`.`time`,`bingli`.`bingid`,`bingli`.`ysid`,`bingli`.`gender`,`bingli`.`age`,`bingli`.`name`,`bingli`.`text` FROM `bingli` WHERE `bingli`.`ysid`='%s' ORDER BY `bingli`.`time` DESC
        '''
        rs,bingli = sqls.setSqlDoing(sql%(user[0][0]))
        sqls.close()
        if rs != False and len(bingli) != 0:
            return True,{
                "list":[{
                    'id':i[0],
                    'time':i[1],
                    'bingid':i[2],
                    'ysid':i[3],
                    'gender':i[4],
                    'age':i[5],
                    'name':i[6],
                    'text':i[7]
                } for i in bingli]
            }
        else:
            return True,{"list":[]}

