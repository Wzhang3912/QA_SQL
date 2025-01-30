import configparser
import os

parser = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'configs/config.conf')

if os.path.exists(config_path):
    parser.read(config_path)
else:
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

# api key
API_KEY = parser.get("api_key", "api_key")

# app
MAX_RETRY = int(parser.get("app", "max_retry"))

# prompt
RESULT_LIMIT = int(parser.get("prompt", "result_limit"))
INPUT_TOKEN_LIMIT = int(parser.get("prompt", "input_token_limit"))
