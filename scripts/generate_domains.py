import json
import os

def generate_domain_env():
    """
    从 config.json 读取生产环境配置，并生成 .env.domains 文件。
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(base_dir, 'config.json')
    output_path = os.path.join(base_dir, '.env.domains')

    print(f"🚀 从 {config_path} 读取架构配置...")

    try:
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
        mail_server = f"{mail_server_prefix}.{base_domain}"

        env_content = (
            f"# 此文件由 scripts/generate_domains.py 自动生成，定义了由架构决定的域名。\n"
            f"# 请勿手动修改。\n\n"
            f"WEB_DOMAIN={web_domain}\n"
            f"MAIL_SERVER={mail_server}\n"
        )

        with open(output_path, 'w') as f:
            f.write(env_content)

        print(f"✅ 成功生成域名配置文件：.env.domains")
        print(f"   - WEB_DOMAIN={web_domain}")
        print(f"   - MAIL_SERVER={mail_server}")

    except Exception as e:
        print(f"❌ 生成 .env.domains 文件时发生未知错误: {e}")
        exit(1)

if __name__ == "__main__":
    generate_domain_env()