import json
import os
import shutil

def generate_final_env():
    """
    合并 .env 和从 config.json 生成的动态配置，创建一个统一的 generated.env 文件。
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(base_dir, 'config.json')
    user_env_path = os.path.join(base_dir, '.env')
    output_path = os.path.join(base_dir, 'generated.env')

    print("🚀 开始生成统一的生产环境配置文件 (generated.env)...")

    # 1. 检查必要文件是否存在
    if not os.path.exists(config_path):
        print(f"❌ 错误：无法找到配置文件 {config_path}")
        exit(1)
    if not os.path.exists(user_env_path):
        print(f"❌ 错误：无法找到用户配置文件 {user_env_path}，请从 .env.example 创建。")
        exit(1)

    try:
        # 2. 从 config.json 读取并生成动态配置
        with open(config_path, 'r') as f:
            config = json.load(f)

        prod_config = config.get('environments', {}).get('production')
        if not prod_config:
            print("❌ 错误：在 config.json 中未找到 'production' 环境配置。")
            exit(1)

        base_domain = prod_config.get('baseDomain')
        web_prefix = prod_config.get('webPrefix')
        mail_server_prefix = prod_config.get('mailServerPrefix')

        if not all([base_domain, web_prefix, mail_server_prefix]):
            print("❌ 错误：'baseDomain', 'webPrefix', 或 'mailServerPrefix' 在生产环境配置中缺失。")
            exit(1)

        web_domain = f"{web_prefix}.{base_domain}"
        mail_server_hostname = f"{mail_server_prefix}.{base_domain}"

        # 3. 复制用户 .env 内容到 generated.env
        shutil.copyfile(user_env_path, output_path)

        # 4. 将动态生成的配置追加到 generated.env
        with open(output_path, 'a') as f:
            f.write("\n# === 由脚本自动生成的配置 ===\n")
            f.write(f"WEB_DOMAIN={web_domain}\n")
            f.write(f"MAIL_SERVER_HOSTNAME={mail_server_hostname}\n")

        print("✅ 成功生成统一配置文件: generated.env")
        print(f"   - WEB_DOMAIN: {web_domain}")
        print(f"   - MAIL_SERVER_HOSTNAME: {mail_server_hostname}")

    except Exception as e:
        print(f"❌ 生成 generated.env 文件时发生未知错误: {e}")
        exit(1)

if __name__ == "__main__":
    generate_final_env()