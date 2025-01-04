import configparser
import os

parser = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'configs/config.conf')

if os.path.exists(config_path):
    parser.read(config_path)
else:
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

# app
MAX_RETRY = parser.get("app", "max_retry")

# prompt
RESULT_LIMIT = parser.get("prompt", "result_limit")
INPUT_TOKEN_LIMIT = parser.get("prompt", "input_token_limit")
