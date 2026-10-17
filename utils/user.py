# -*- coding: utf-8 -*-
#encoding:utf-8
import sys
import time

##################################################

sys.path.append("..") 
# from config import conf as CONF
from mydb.mq import tomysql

_ROLE_NAMES = {"1": "管理员", "2": "患者", "3": "医生"}
_pcode_ready = False


def ensure_patient_codes(sqls, force=False):
    """患者使用 8 位就诊编号。编号补齐后，同一进程里不再重复扫描。"""
    global _pcode_ready
    if _pcode_ready and not force:
        return
    rs, cols = sqls.setSqlDoing("SHOW COLUMNS FROM `user` LIKE 'pcode'")
    if not rs:
        return
    if not cols:
        rs, _ = sqls.setSqlDoing("ALTER TABLE `user` ADD COLUMN `pcode` CHAR(8) NULL")
        if not rs:
            return
    rs, pending = sqls.setSqlDoing(
        "SELECT `id` FROM `user` WHERE FIND_IN_SET('2', `roles`) AND (`pcode` IS NULL OR `pcode`='') ORDER BY `id`"
    )
    if not rs:
        return
    if not pending:
        _pcode_ready = True
        return
    rs, current = sqls.setSqlDoing("SELECT MAX(`pcode`) FROM `user` WHERE `pcode` REGEXP '^[0-9]{8}$'")
    nxt = int(current[0][0]) + 1 if rs and current and current[0][0] else 26000001
    for row in pending:
        rs, _ = sqls.setSqlDoing("UPDATE `user` SET `pcode`=%s WHERE `id`=%s", (f"{nxt:08d}", row[0]))
        if not rs:
            return
        nxt += 1
    _pcode_ready = True


def _role_text(roles):
    return "、".join(_ROLE_NAMES.get(item, item) for item in str(roles or "").split(",") if item)


# 通过用户名，密码获取用户ID
def get_user(user,pwd):
    sqls = tomysql()
    # 更新token
    sql = '''
        SELECT `user`.`id`,`user`.`roles` FROM `user` WHERE `user`.`user`=%s AND `user`.`pwd`=%s AND `user`.`status`=1
    '''
    rs,rf = sqls.setSql(sql, (user, pwd))
    sqls.close()
    if rs != False and len(rf) != 0:
        return True, {"id": rf[0][0], "roles": str(rf[0][1] or "")}
    return False, rf

# 通过token获取用户信息
def _find_patient_id(sqls, raw):
    text = str(raw or "").strip()
    if not text:
        return None
    if text.isdigit() and len(text) >= 8:
        rs, rows = sqls.setSqlDoing("SELECT `id` FROM `user` WHERE `pcode`=%s AND `status`=1", (text,))
        if rs and rows:
            return rows[0][0]
    if text.isdigit():
        rs, rows = sqls.setSqlDoing("SELECT `id` FROM `user` WHERE `id`=%s AND `status`=1", (int(text),))
        if rs and rows:
            return rows[0][0]
    return None


def get_user_name(token):
    sqls = tomysql()
    ensure_patient_codes(sqls)
    # 获取用户信息
    sql = '''
        SELECT `user`.`id`,`user`.`name`,`user`.`stime`,`user`.`roles`,`user`.`pcode` FROM `user` WHERE `user`.`token`=%s AND `user`.`status`=1
    '''
    rs,user = sqls.setSqlDoing(sql, (token,))
    if rs != False and len(user) != 0:
        role_ids = [item.strip() for item in str(user[0][3] or "").split(",") if item.strip().isdigit()]
        if not role_ids:
            sqls.close()
            return False, "用户没有可用角色"
        marks = ",".join(["%s"] * len(role_ids))
        sql = f'''
            SELECT `roles`.`name`,`roles`.`nid` FROM `roles` WHERE `roles`.`id` in ({marks})
        '''
        rs,roles = sqls.setSqlDoing(sql, tuple(role_ids))
        sqls.close()
        if rs != False and len(roles) != 0:
            return True, list(user[0][:3]) + [
                [item[0] for item in roles],
                [item[1] for item in roles],
                user[0][4] or "",
            ]
        return False, roles
    else:
        sqls.close()
        return False,user

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

# 获取用户列表
def get_user_list(req):
    sqls = tomysql()
    ensure_patient_codes(sqls)
    limit = int(req['limit']) if req and 'limit' in req else 20
    page = int(req['page']) if req and 'page' in req else 1
    keyword = str((req or {}).get('keyword') or '').strip()[:40]
    viewer_roles = (req or {}).get('viewer_roles') or []
    where = ["`user`.`id`<>1"]
    vals = []
    if 'admin' not in viewer_roles:
        where.append("FIND_IN_SET('2', `user`.`roles`)")
    if keyword:
        where.append("(`user`.`name` LIKE %s OR `user`.`user` LIKE %s OR IFNULL(`user`.`pcode`,'') LIKE %s)")
        like = "%" + keyword + "%"
        vals.extend((like, like, like))
    clause = " AND ".join(where)
    rs, total = sqls.setSqlDoing("SELECT COUNT(`user`.id) FROM `user` WHERE " + clause, tuple(vals))
    rs, users = sqls.setSqlDoing(
        "SELECT `user`.`user`, `user`.stime, `user`.`name`,`user`.`id`,`user`.`roles`,`user`.`status`, IFNULL(`user`.`pcode`,'') FROM `user` WHERE "
        + clause + " ORDER BY `user`.`id` DESC LIMIT %s,%s",
        tuple(vals) + ((page - 1) * limit, limit),
    )
    sqls.close()
    if rs == False:
        return False, "查询失败"
    return True, {
        "list": [{
            'user': i[0],
            'stime': i[1],
            'name': i[2],
            'id': i[3],
            'roles': i[4],
            'roleText': _role_text(i[4]),
            'status': i[5],
            'pcode': i[6],
        } for i in users],
        "total": total[0][0] if total else 0,
    }
    
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
        SELECT `user`.`name` FROM `user` WHERE `user`.`user`=%s
    '''
    rs,users = sqls.setSqlDoing(sql, (user,))
    if rs != False and len(users) != 0:
        sqls.close()
        return False,u'用户创建失败，账号已存在'
    else:
        sql = '''
            INSERT INTO `user`(`user`,`pwd`,`name`,`roles`,`status`) VALUES (%s,%s,%s,%s,1)
        '''
        rs,users = sqls.setSqlDoing(sql, (user, pwd, name, roles))
        if rs != False:
            pcode = ""
            if "2" in str(roles).split(","):
                ensure_patient_codes(sqls, force=True)
                rs, created = sqls.setSqlDoing("SELECT `pcode` FROM `user` WHERE `user`=%s", (user,))
                pcode = created[0][0] if rs and created else ""
            sqls.close()
            return True, {"message": "账户创建成功", "pcode": pcode or ""}
        else:
            sqls.close()
            return False,u'用户创建失败'

# 修改用户信息 修改后清空token 强制被修改用户下线
def up_user(req):
    sqls = tomysql()
    pwd = req['pwd'] if 'pwd' in req else ''
    name = req['name'] if 'name' in req else ''
    roles = req['roles'] if 'roles' in req else []
    if name == '':
        sqls.close()
        return False,u'用户信息修改失败'
    roles = ','.join([str(i) for i in roles])
    if pwd != '' and pwd != None:
        sql = "UPDATE `user` SET `token`='',`name`=%s,`roles`=%s,`pwd`=%s WHERE `id`=%s AND `id`<>1"
        vals = (name, roles, pwd, req['id'])
    else:
        sql = "UPDATE `user` SET `token`='',`name`=%s,`roles`=%s WHERE `id`=%s AND `id`<>1"
        vals = (name, roles, req['id'])
    rs,rf = sqls.setSql(sql, vals)
    if "2" in roles.split(","):
        ensure_patient_codes(sqls, force=True)
    sqls.close()
    if rs != False:
        return True,u'用户信息修改成功'
    else:
        return False,u'用户信息修改失败'

# 用户除权 清空token status修改
def del_user(req):
    sqls = tomysql()
    sql = '''
        UPDATE `user` SET `token`='',`status`=0 WHERE `id`=%s AND `id`<>1
    '''
    rs,rf = sqls.setSql(sql, (req['id'],))
    sqls.close()
    if rs != False:
        return True,u'账号已注销，无法再登录'
    else:
        return False,u'注销失败'

# 用户密码修改
def up_user_pwd(token,req):
    sqls = tomysql()
    sql = '''
        UPDATE `user` SET `pwd`=%s WHERE `token`=%s
    '''
    rs,rf = sqls.setSql(sql, (req['pwd'], token))
    if rs != False:
        return True,u'用户密码修改成功'
    else:
        return False,u'用户密码修改失败'
def _owner_id(sqls, token):
    rs, rows = sqls.setSqlDoing("SELECT `id` FROM `user` WHERE `token`=%s", (token,))
    if rs != False and rows:
        return rows[0][0]
    return None


def _bingli_list(rows):
    return {"list": [{
        "id": row[0],
        "time": row[1],
        "bingid": row[2],
        "ysid": row[3],
        "gender": row[4],
        "age": row[5],
        "name": row[6],
        "text": row[7],
        "pcode": row[8] or "",
    } for row in rows or []]}


def _records_for(token, sql):
    sqls = tomysql()
    owner = _owner_id(sqls, token)
    if owner is None:
        sqls.close()
        return False, "请重新登录"
    rs, rows = sqls.setSqlDoing(sql, (owner,))
    sqls.close()
    if rs != False and rows:
        return True, _bingli_list(rows)
    return True, {"list": []}


def addBingli(token, req):
    required = ("bingid", "gender", "age", "name", "text")
    if not req or any(not req.get(key) and req.get(key) != 0 for key in required):
        return False, "病历信息不完整"
    sqls = tomysql()
    patient_id = _find_patient_id(sqls, req.get("bingid"))
    if not patient_id:
        sqls.close()
        return False, "没有这个就诊编号"
    owner = _owner_id(sqls, token)
    if owner is None:
        sqls.close()
        return False, "请重新登录"
    rs, _ = sqls.setSql(
        "INSERT INTO `bingli`(`time`,`bingid`,`ysid`,`gender`,`age`,`name`,`text`) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (int(time.time()), patient_id, owner, req["gender"], req["age"], req["name"], req["text"]),
    )
    sqls.close()
    if rs != False:
        return True, "病历添加成功"
    return False, "病历添加失败"


def getBingliList(token):
    sql = """
        SELECT `bingli`.`id`,`bingli`.`time`,`bingli`.`bingid`,
        (SELECT `user`.`name` FROM `user` WHERE `id`=`bingli`.`ysid`),
        `bingli`.`gender`,`bingli`.`age`,`bingli`.`name`,`bingli`.`text`,
        (SELECT `user`.`pcode` FROM `user` WHERE `id`=`bingli`.`bingid`)
        FROM `bingli` WHERE `bingli`.`bingid`=%s ORDER BY `bingli`.`time` DESC
    """
    return _records_for(token, sql)


def getBingli(token):
    sql = """
        SELECT `bingli`.`id`,`bingli`.`time`,`bingli`.`bingid`,`bingli`.`ysid`,
        `bingli`.`gender`,`bingli`.`age`,`bingli`.`name`,`bingli`.`text`,
        (SELECT `user`.`pcode` FROM `user` WHERE `id`=`bingli`.`bingid`)
        FROM `bingli` WHERE `bingli`.`ysid`=%s ORDER BY `bingli`.`time` DESC
    """
    return _records_for(token, sql)

