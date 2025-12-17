import os
import psycopg2
import subprocess
import time
# --- 配置 ---
# 环境变量将由 Docker Compose 注入

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("DB_HOST_DOCKER", "db") # 允许覆盖
DB_PORT = os.getenv("DB_PORT_DOCKER", "5432")
MAILSERVER_CONTAINER_NAME = os.getenv("MAILSERVER_CONTAINER_NAME", "talentmail-mailserver-1")
DEFAULT_MAIL_PASSWORD = os.getenv("DEFAULT_MAIL_PASSWORD", "password")

def get_db_connection():
    """建立并返回数据库连接"""
    conn = None
    while conn is None:
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
        except psycopg2.OperationalError:
            print("数据库连接失败，将在5秒后重试...")
            time.sleep(5)
    return conn

def get_users_from_db(conn):
    """从数据库中获取所有用户的邮箱列表"""
    with conn.cursor() as cur:
        cur.execute("SELECT email FROM users")
        users = [row[0] for row in cur.fetchall()]
    return users

def get_existing_mail_users():
    """获取 mailserver 中已存在的所有邮箱账户"""
    try:
        result = subprocess.run(
            ["docker", "exec", MAILSERVER_CONTAINER_NAME, "setup", "email", "list"],
            capture_output=True, text=True, check=True
        )
        # 输出的第一行是标题，我们需要忽略它
        # 使用更健壮的方式来解析输出，过滤空行和标题
        lines = result.stdout.strip().split('\n')
        return {line.strip() for line in lines if line and 'Existing email addresses' not in line and '----------------' not in line}
    except subprocess.CalledProcessError as e:
        print(f"执行 'docker exec' 命令失败: {e.stderr}")
        return set()

def create_mail_user(email):
    """在 mailserver 中创建一个新的邮箱账户"""
    try:
        print(f"邮箱 {email} 不存在于 mailserver 中，正在创建...")
        subprocess.run(
            ["docker", "exec", MAILSERVER_CONTAINER_NAME, "setup", "email", "add", email, DEFAULT_MAIL_PASSWORD],
            capture_output=True, text=True, check=True
        )
        print(f"✔ 成功创建邮箱: {email}")
    except subprocess.CalledProcessError as e:
        print(f"✖ 创建邮箱 {email} 失败: {e.stderr}")

def main():
    print("--- 开始同步数据库用户至 Mailserver ---")
    
    conn = get_db_connection()
    db_users = get_users_from_db(conn)
    conn.close()
    
    if not db_users:
        print("数据库中没有找到用户，无需同步。")
        return

    print(f"从数据库中找到 {len(db_users)} 个用户。")
    
    mail_users = get_existing_mail_users()
    print(f"Mailserver 中已存在 {len(mail_users)} 个邮箱。")

    for user_email in db_users:
        if user_email not in mail_users:
            create_mail_user(user_email)
        else:
            print(f"邮箱 {user_email} 已存在于 mailserver 中，跳过。")
            
    print("--- 同步完成 ---")

if __name__ == "__main__":
    main()