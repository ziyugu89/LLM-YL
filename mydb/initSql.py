import subprocess
import sys
sys.path.append("..") 
from config import conf as CONF

def import_sql(file_path, user, password, database, exe):
    try:
        # 构建 MySQL 命令
        mysql_command = [
            exe,
            f"--user={user}",
            f"--password={password}",
            "-e",
            f"CREATE DATABASE IF NOT EXISTS {database};"
        ]
        result = subprocess.run(mysql_command, capture_output=True, text=True, check=True)
        print(f"数据库 {database} 创建成功！")
        print("命令输出：", result.stdout)

        command = [
            exe,
            '-u', user,
            '-p' + password,
            database
        ]
        # 如果不想在命令行中暴露密码，可以省略 '-p' 参数，之后会提示输入密码
        # command = ['mysql', '-u', user, database]
        
        with open(file_path, 'r', encoding='utf-8') as f:
            result = subprocess.run(
                command,
                stdin=f,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        print("导入成功！")
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print("导入失败！")
        print(e.stderr.decode())

# 使用示例
if __name__ == "__main__":
    sql_file = CONF['SQL']['path']  # 替换为你的 SQL 文件路径
    db_user = CONF['SQL']['user']                    # 替换为你的 MySQL 用户名
    db_password = CONF['SQL']['pwd']        # 替换为你的 MySQL 密码
    db_name = CONF['SQL']['library']              # 替换为目标数据库名
    db_exe = CONF['SQL']['exe']                    # 替换为 MySQL 可执行文件路径

    import_sql(sql_file, db_user, db_password, db_name, db_exe)