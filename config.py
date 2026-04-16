# ============================================================
# ATLAS - Configuration globale du système
# ============================================================

import os
import json

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR  = os.path.join(BASE_DIR, "models")
CONFIG_FILE = os.path.join(BASE_DIR, "atlas_config.json")

os.makedirs(MODELS_DIR, exist_ok=True)

MAX_EPOCHS    = 200
DAILY_QUOTA_H = 4
DIMENSIONS    = [32, 64, 128]


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(data: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_model_path(ai_name: str) -> str:
    path = os.path.join(MODELS_DIR, ai_name)
    os.makedirs(path, exist_ok=True)
    return path