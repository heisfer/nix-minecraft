#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3Packages.requests

import json
import requests
import hashlib
from pathlib import Path
from requests.adapters import HTTPAdapter, Retry
import time
import pprint


ENDPOINT = "https://versions.mcjars.app/api/v2/builds/forge"

def load_lock(path):
    print("Loading lock file")
    if not path.exists():
        print("└ Creating one from scratch")
        return {}
    with open(path, "r+") as f:
        data = json.load(f)
    return data

def save_lock(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)



def get_versions():
    print("Fetching Versions and latest builds")
    versions = requests.get(ENDPOINT).json()['builds']
    return versions


def get_build_sha256(build_url):
    print(f"  -> Generating SHA256")
    sha256 = hashlib.sha256()
    with requests.get(build_url, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_content(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def main(lock_path):
    lock_data = load_lock(lock_path)
    data = get_versions();
    update = 0

    for version in data:
        if version not in lock_data:
            lock_data[version] = {}
        build = data[version]["latest"]["name"]
        build_download = data[version]["latest"]["zipUrl"]
        if build in lock_data[version]:
            continue

        print(f"-> Found new {build} build for {version} version")
        build_sha256 = get_build_sha256(build_download)

        lock_data[version][build] = {
            "url": build_download,
            "sha256": build_sha256
        }
        update +=1



    save_lock(lock_path, lock_data)
    print(f"-> Updated {update} builds")


            
        

if __name__ == "__main__":
    folder = Path(__file__).parent
    lock_path = Path(folder / "lock.json")
    main(lock_path)


