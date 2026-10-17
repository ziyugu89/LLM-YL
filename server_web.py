# -*- coding: utf-8 -*-
#encoding:utf-8
from handlers import base
import user_api as users
import data_api as datas

from flask import Flask, render_template
from flask_cors import cross_origin

app  =  Flask(__name__,static_url_path="/static")

@app.route('/',methods=['GET'])
def index():
    return render_template('./index.html')

# 登录
@app.route('/webapi/user/login',methods=['POST','OPTIONS'])
@cross_origin()
def webapi_user_login():
    return users.login()

# 注销登录
@app.route('/webapi/user/logout',methods=['POST'])
@base.check_sess
def webapi_user_logout():
    return users.logout()

# 拉取用户信息
@app.route('/webapi/user/info',methods=['GET'])
def webapi_user_info():
    return users.info()

# 当前登录身份
@app.route('/webapi/user/profile',methods=['POST'])
@base.check_sess
def webapi_user_profile():
    return users.profile()

# 拉取用户列表
@app.route('/webapi/user/getlist',methods=['POST'])
@base.check_sess
def webapi_user_getlist():
    return users.getlist()

# 创建用户
@app.route('/webapi/user/adduser',methods=['POST'])
# @base.check_sess
def webapi_user_adduser():
    return users.addUser()

# 修改用户信息
@app.route('/webapi/user/upUser',methods=['POST'])
@base.check_sess
def webapi_user_upUser():
    return users.upUser()

# 用户除权
@app.route('/webapi/user/delUser',methods=['POST'])
@base.check_sess
def webapi_user_delUser():
    return users.delUser()

# 修改密码
@app.route('/webapi/user/upUserPwd',methods=['POST'])
@base.check_sess
def webapi_user_upUserPwd():
    return users.upUserPwd()

# 获取信息
@app.route('/webapi/data/getData',methods=['POST'])
@base.check_sess
def webapi_data_getData():
    return datas.getData()

# 添加病历
@app.route('/webapi/data/addbingli',methods=['POST'])
@base.check_sess
def webapi_data_addbingli():
    return datas.addbingli()

# 查询病历
@app.route('/webapi/data/getbingli',methods=['POST'])
@base.check_sess
def webapi_data_getbingli():
    return datas.getbingli()

# 查询病历
@app.route('/webapi/data/getbingliBH',methods=['POST'])
@base.check_sess
def webapi_data_getbingliBH():
    return datas.getbingliBH()

# 查询病历
@app.route('/webapi/data/llm',methods=['POST'])
@base.check_sess
def webapi_data_llm():
    return datas.llm()

# 挂号流程和院内位置
@app.route('/webapi/data/guide',methods=['POST'])
@base.check_sess
def webapi_data_guide():
    return datas.guide()

# 已导入的号源、排队和检查报告
@app.route('/webapi/data/hospital',methods=['POST'])
@base.check_sess
def webapi_data_hospital():
    return datas.hospital()

# 查询病历
@app.route('/webapi/data/setmessage',methods=['POST'])
@base.check_sess
def webapi_data_setmessage():
    return datas.setmessage()

# 查询提醒
@app.route('/webapi/data/getmessage',methods=['POST'])
@base.check_sess
def webapi_data_getmessage():
    req = datas.getRedis()
    return req


# # 静态资源处理
# @app.route('/cdn/<path:filename>')
# def custom_static(filename):
#     return send_from_directory(os.path.join('./download'), filename)

if __name__ == "__main__":
    print (u'服务运行...')
    app.run(host='127.0.0.1',port=5050,debug=True)