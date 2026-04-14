import json
import os
from pathlib import Path

DATA_DIR = 'data'


def get_user_file(user_id: int):
    Path(DATA_DIR).mkdir(exist_ok=True)
    return f'{DATA_DIR}/user_{user_id}.json'


def load_data(user_id: int):
    file = get_user_file(user_id)

    if not os.path.exists(file):
        return {'habits': [], 'entries': []}

    with open(file, "r") as f:
        return json.load(f)


def save_data(user_id: int, data: dict):
    file = get_user_file(user_id)
    with open(file, "w") as f:
        json.dump(data, f, indent=4)