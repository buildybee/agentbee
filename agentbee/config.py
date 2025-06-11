import configparser
from pathlib import Path

CONFIG_DIR = Path.home() / ".agentbee"
CONFIG_FILE = CONFIG_DIR / "config.ini"
CONFIG_SECTION = "DEFAULT"

def get_config_path() -> Path:
    """Returns the path to the config file."""
    return CONFIG_FILE

def save_config(api_key: str, base_url: str, model: str):
    """Saves the configuration to the global config file."""
    CONFIG_DIR.mkdir(exist_ok=True)
    config = configparser.ConfigParser()
    config[CONFIG_SECTION] = {
        'llm_api_key': api_key,
        'llm_base_url': base_url,
        'llm_model': model
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    print(f"✅ Configuration saved to {CONFIG_FILE}")

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return {
        'llm_api_key': config.get(CONFIG_SECTION, 'llm_api_key', fallback=''),
        'llm_base_url': config.get(CONFIG_SECTION, 'llm_base_url', fallback=''),
        'llm_model': config.get(CONFIG_SECTION, 'llm_model', fallback='')
    }