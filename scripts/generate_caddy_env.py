import json
from pathlib import Path

def generate_caddy_env():
    """
    Reads the main config.json, determines the correct web domain based on the
    current environment, and writes it to a .env.caddy file for Docker Compose
    to use.
    """
    try:
        # Assuming the script is run from the project root
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"
        output_path = project_root / ".env.caddy"

        print(f"Reading configuration from: {config_path}")
        with open(config_path, "r") as f:
            config = json.load(f)

        env = config.get("currentEnvironment", "development")
        env_config = config.get("environments", {}).get(env, {})

        base_domain = env_config.get("baseDomain")
        web_prefix = env_config.get("webPrefix")

        if not base_domain or not web_prefix:
            raise ValueError(f"'{env}' environment in config.json is missing 'baseDomain' or 'webPrefix'")

        web_domain = f"{web_prefix}.{base_domain}"

        print(f"Writing WEB_DOMAIN={web_domain} to: {output_path}")
        with open(output_path, "w") as f:
            f.write(f"WEB_DOMAIN={web_domain}\n")

        print("Successfully generated .env.caddy file.")

    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generate_caddy_env()