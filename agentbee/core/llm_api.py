from typing import Dict
import json

# from langchain_google_genai import GoogleGenerativeAI
# from langchain_ollama import ChatOllama
from pydantic import SecretStr
from .. import config

def get_api_key() -> SecretStr:
    try:
        cfg =config.load_config()
        return SecretStr(cfg['llm_api_key'])
    except Exception as e:
        print(f"🚨 API Error: {e}")
        raise
