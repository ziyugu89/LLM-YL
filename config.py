# -*- coding: utf-8 -*-
#encoding:utf-8

# 配置一些公共信息

conf = {
    'TokenKey': 'XC-Token',# 获取请求头中token的key
    'userOut': 3600,#登录超时控制
    'SQL': {
        'local': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'pwd': 'root123',
        'library': 'web_server',
        'printSql': False,#是否打印sql语句
        'path': r'../web_server.sql',#数据库文件路径
        'exe': r'mysql'#mysql的路径
    }
}