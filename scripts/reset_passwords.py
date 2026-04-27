import os
import sys
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# 添加 backend 目录到 sys.path 以便导入配置
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

# 数据库连接配置 - 在 Docker 容器内使用 db，本地使用 localhost
import os
DATABASE_URL = os.environ.get("DATABASE_URL_DOCKER", "postgresql://user:password@localhost:5432/talentmail")

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def reset_passwords():
    print("Connecting to database...")
    try:
        engine = create_engine(DATABASE_URL)
        connection = engine.connect()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Make sure the database is running and port 5432 is exposed.")
        return

    new_password = os.environ.get("RESET_PASSWORD")
    if not new_password:
        print("Error: 请通过环境变量 RESET_PASSWORD 指定新密码")
        print("用法: RESET_PASSWORD='your_secure_password' python reset_passwords.py")
        return
    if len(new_password) < 8:
        print("Error: 密码长度不能少于 8 位")
        return
    hashed_password = get_password_hash(new_password)

    print(f"New password hash generated (password length: {len(new_password)})")

    # 更新除 admin@talenting.test 以外的所有用户的密码
    # 注意：这里假设 admin 用户的邮箱是 admin@talenting.test
    # 如果 admin 用户名不同，请相应修改 WHERE 子句
    sql = text("""
        UPDATE users 
        SET password_hash = :hashed_password 
        WHERE email != 'admin@talenting.test'
    """)

    try:
        result = connection.execute(sql, {"hashed_password": hashed_password})
        connection.commit()
        print(f"Successfully updated passwords for {result.rowcount} users.")
    except Exception as e:
        print(f"Error updating passwords: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    reset_passwords()