import os
from pathlib import Path
import json

default_directory = os.path.join(Path.home(), ".big-map-archive")
default_config_file = os.path.join(default_directory, "big-map-archive.json")


def add_token(token):
    if not os.path.exists(default_directory):
        os.mkdir(default_directory)
    datas = {"token": token}
    with open(default_config_file, "w") as f:
        datas = json.dump(datas, f, indent=4)
    print("You token is added to {}.".format(default_config_file))


def load_token(file=None):
    if file is None:
        file = default_config_file
    # environment variable first
    token = os.environ.get("BIG_MAP_ARCHIVE_TOKEN")
    if token is not None:
        return token
    # try read json file
    try:
        with open(file, "r") as f:
            datas = json.load(f)
            token = datas.get("token")
    except Exception as e:
        token = None

    return token


if __name__ == "__main__":
    token = load_token()
    print(token)
