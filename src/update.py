import io
import os
import shutil
import zipfile

import requests


def download_and_replace_branch(repo_url, branch_name, extract_to="."):
    zip_url = f"{repo_url}/archive/refs/heads/{branch_name}.zip"

    response = requests.get(zip_url)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        temp_dir = os.path.join(extract_to, f"temp_{branch_name}")

        z.extractall(temp_dir)

        extracted_dir = os.path.join(temp_dir, os.listdir(temp_dir)[0])

        for item in os.listdir(extracted_dir):
            src_path = os.path.join(extracted_dir, item)
            dest_path = os.path.join(extract_to, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_path)

        shutil.rmtree(temp_dir)

        print(f"Successfully downloaded and replaced files with the {branch_name} branch.")


repo_url = "https://github.com/nishimura5/behavior_senpai"
branch_name = "master"
download_and_replace_branch(repo_url, branch_name)
