#!/usr/bin/env python
# -*- encoding: utf-8
import fnmatch
import io
import pathlib
import shutil
import zipfile

import requests
import re
import os
import errno
from sys import exit

__version__ = '1.2.0'
GH_API_BASE_URL = 'https://api.github.com'
GH_REPO_CONTENTS_ENDPOINT = GH_API_BASE_URL + '/repos/{}/{}/contents'
BASE_NORMALIZE_REGEX = re.compile(r'.*github\.com\/')

req = requests.Session()
req.headers.update({'User-Agent': 'git.io/ghclone ' + __version__})


def exit_with_m(m='An error occured'):
    print(m)
    exit(1)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as err:  # Python >2.5
        if err.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_release(gh_url, path_to_folder, release_name):
    gh_args, normal_url = parse_gh_url(gh_url)
    owner = gh_args[0]
    repo = gh_args[1]
    response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/releases/latest")
    assets = response.json()["assets"]

    download_link = ""
    for asset in assets:
        if asset["name"] == release_name:
            download_link = asset["browser_download_url"]

    print(f"Downloading {repo} into {path_to_folder} ...")
    file_name = download_and_extract_zip(download_link, path_to_folder)
    print(f"Done downloading {file_name}.")


def get_repo_and_unzip_needed(gh_url, path_to_folder, mod_name, is_mod_pack=False):
    show_message(source=mod_name, message="Start downloading repo", lvl=1)

    gh_args, normal_url = parse_gh_url(gh_url)
    owner = gh_args[0]
    repo = gh_args[1]

    req_folder = ""
    if len(gh_args) < 3:
        req_folder = repo + "-master/"
    else:
        req_folder = repo + "-master/" + "/".join(gh_args[3:]) + "/"

    req_folder = download_zip_and_extract_req_folder(
        f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip", path_to_folder + "/" + mod_name, req_folder)

    return path_to_folder + "/" + mod_name + "/" + req_folder


def move_folder(source, destination, mod_name):
    show_message(source=mod_name, message="Move to mod folder", lvl=1)
    if pathlib.Path(destination + "/" + mod_name).exists():
        show_message(source=mod_name, message="Remove old mod", lvl=2)
        shutil.rmtree(destination)

    shutil.move(source, destination + "/" + mod_name)
    show_message(source=mod_name, message="Moved successfully", lvl=1)


def download_zip_and_extract_req_folder(url, save_path, req_folder):
    r = requests.get(url)

    archive = zipfile.ZipFile(io.BytesIO(r.content))

    show_message(source="", message="Download complete", lvl=1)

    if archive.namelist()[0].endswith("-main/"):
        req_folder = req_folder.replace("-master/", "-main/", 1)

    show_message(source="", message="Unzip", lvl=1)

    for file in archive.namelist():
        if file.startswith(req_folder):
            file.replace(req_folder, "")
            archive.extract(file, save_path)

    archive.close()

    show_message(source="", message="Unzip complete", lvl=1)
    return req_folder


def show_message(source, message, lvl):
    if lvl == 0:
        print("\t" * lvl + source + ": " + message)
    else:
        print("\t" * lvl + message + "!")


def download_and_extract_zip(url, save_path):
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(save_path)
    return z.filename


def clone_file(download_url, file_path):
    """
    Clones the file at the download_url to the file_path
    """
    r = req.get(download_url, stream=True)
    try:
        r.raise_for_status()
    except Exception as e:
        print('Failed to fetch metadata for ' + download_url)
        return
        # exit_with_m('Failed to clone ' + download_url)

    with open(file_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)


def clone(base_url, rel_url=None, path=None, ref=None):
    """
    Recursively clones the path
    """
    req_url = base_url + '/' + rel_url if rel_url else base_url

    # Get path metadata
    r = req.get(req_url) if not ref else req.get(req_url, params={'ref': ref})
    try:
        r.raise_for_status()
    except Exception as e:
        print('Failed to fetch metadata for ' + path)
        return
        # exit_with_m('Failed to fetch metadata for ' + path)
    repo_data = r.json()

    # Recursively clone content
    for item in repo_data:
        if item['type'] == 'dir':
            # Fetch dir recursively
            clone(base_url, item['path'], path, ref)
        else:
            # Fetch the file
            new_file_path = resolve_path(item['path'], path)
            new_path = os.path.dirname(new_file_path)
            # Create path locally
            mkdir_p(new_path)
            # Download the file
            clone_file(item['download_url'], new_file_path)
            # print('Cloned', item['path'])


def resolve_path(path, dir):
    index = path.find(dir)
    if index == -1:
        return os.path.abspath(os.path.join(dir, path))
    else:
        return os.path.abspath(path[index:])


def parse_gh_url(gh_url):
    # Normalize & parse input
    gh_url = gh_url.replace('%20', " ")
    normal_gh_url = re.sub(BASE_NORMALIZE_REGEX, '', gh_url)
    gh_args = normal_gh_url.replace('/tree', '').split('/')
    return gh_args, normal_gh_url


def getRepo(gh_url, path_to_folder, is_mod_pack=False):
    gh_args, normal_gh_url = parse_gh_url(gh_url)

    if len(gh_args) < 2 or normal_gh_url == gh_url:
        exit_with_m('Invalid GitHub URI')

    user, repo = gh_args[:2]
    ref = None
    rel_url = None

    if len(gh_args) >= 2:
        # Clone entire repo
        path = repo

    if len(gh_args) >= 3:
        # Clone entire repo at the branch
        ref = gh_args[2]

    if len(gh_args) >= 4:
        # Clone subdirectory
        rel_url = os.path.join(*gh_args[3:])
        path = gh_args[-1]

    api_req_url = GH_REPO_CONTENTS_ENDPOINT.format(user, repo)

    if is_mod_pack == True:
        print(f"Cloning {repo} into {path_to_folder} ...")
        clone(api_req_url, rel_url, path_to_folder, ref)
        print(f"Done cloning {repo}.")
    else:
        print(f"Cloning {repo} into {path_to_folder + path} ...")
        clone(api_req_url, rel_url, path_to_folder + path, ref)
        print(f"Done cloning {repo}.")


def remove_downloads(download_folder):
    shutil.rmtree(download_folder)
