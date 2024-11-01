import requests
import yaml
import json
import os
import warnings
import sys
import threading
from pathlib import Path
from itertools import zip_longest
from termcolor import colored

CONFIG = yaml.safe_load(open("config.yaml", "r"))

MODLIST = yaml.safe_load(open(sys.argv[1], "r"))
VERSION = CONFIG["minecraft_version"]
LOADER = CONFIG["mod_loader"]
RETRY_FETCH_LIMIT = CONFIG["retry_fetch_limit"]
FETCH_GROUP_N = CONFIG["fetch_group_n"]
DOWNLOAD_THREADS = CONFIG["download_threads"]

OUT_DIR_STR = "out"

SCOPE_COLORS = {
    "client": "light_green",
    "shared": "light_magenta",
    "server": "light_blue"
}

retry_fetch_count = 0
failed_fetch_count = 0
no_match_count = 0

print(colored("downloading for:", "yellow"), colored(LOADER + " " + VERSION, "cyan"))
print(colored("fetching mods in groups of", "yellow"), colored(str(FETCH_GROUP_N) + "s", "cyan"))
print(colored("amount of download threads:", "yellow"), colored(str(DOWNLOAD_THREADS), "cyan"))

def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def getMatchingVersionIndex(mod_version_list):
    # match the version and loader
    index = 0
    for version_info in mod_version_list:
        if VERSION in version_info["game_versions"] and LOADER in version_info["loaders"]:
            return index
        else:
            index += 1

def downloadSlugs(project_slugs, out_subdir, scope):
    mods_download_registry = [] # [name.jar, url]

    # cache the data for each
    # {info, versions}
    # project_slugs = parseProjectSlugs(MODLIST_FILE)
    success_slugs = []
    mods_data = {}
    known_slugs = []

    # slugs
    failed_slugs = []

    # get project info and versions
    def getProjectData(proj_idslug, dependent_of):
        info_response = requests.get("https://api.modrinth.com/v2/project/" + proj_idslug)
        version_response = requests.get("https://api.modrinth.com/v2/project/" + proj_idslug + "/version")

        proj_name = proj_idslug
        if dependent_of != None:
            proj_name = dependent_of + ": " + proj_name

        if info_response.ok and version_response.ok:
            mod_info = info_response.json()
            mod_versions = version_response.json()

            # match version and loader
            if VERSION in mod_info["game_versions"] and LOADER in mod_info["loaders"]:
                matched_version = mod_versions[getMatchingVersionIndex(mod_versions)]
                mod_data = {
                    "info": mod_info,
                    "version": matched_version
                }

                mods_data[mod_info["slug"]] = mod_data
                success_slugs.append(mod_info["slug"])
                known_slugs.append(mod_info["slug"])

                version_dependencies = matched_version["dependencies"]
                for d_info in version_dependencies:
                    if d_info["dependency_type"] == "required":
                        d_slug = d_info["project_id"]

                        if d_slug in known_slugs:
                            proj_name = mod_info["slug"] + ": " + d_slug
                            print(colored(scope, SCOPE_COLORS[scope]), colored(proj_name + " already fetched: " + mod_info["title"], "green"))
                        else:
                            known_slugs.append(d_slug)
                            getProjectData(d_slug, proj_name)

                print(colored(scope, SCOPE_COLORS[scope]), colored(proj_name + " fetched successfully: " + mod_info["title"], "green"))
                return mod_data
            else:
                print(colored(scope, SCOPE_COLORS[scope]), colored(proj_name + " matched neither selected version or loader", "red"))

                global no_match_count
                no_match_count += 1
        else:
            failed_slugs.append(proj_idslug)
            print(colored(scope, SCOPE_COLORS[scope]), colored(proj_name + " failed one of the requests to modrinth", "red"))
            global failed_fetch_count
            failed_fetch_count += 1

    # first class
    def proccessSlugs():
        threads = []
        slugs_grouped = list(grouper(project_slugs, FETCH_GROUP_N))
        for group in slugs_grouped:
            def _processGroup():
                for ps in group:
                    if ps != None:
                        getProjectData(ps, None)
            
            t = threading.Thread(target=_processGroup)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    proccessSlugs()

    # proccess all dependencies

    print(colored(scope, SCOPE_COLORS[scope]), colored("mods to install:", "yellow"))
    print(colored(scope, SCOPE_COLORS[scope]), colored(", ".join(success_slugs), "yellow"))

    # fetch download info
    def getDownloadData(mod_data):
        mod_info = mod_data["info"]
        mod_version = mod_data["version"]

        version_files = mod_version["files"]
        if len(version_files) > 1:
            for f in version_files:
                if f["primary"]:
                    file_name = f["filename"]
                    file_url = f["url"]
        else:
            file_name = version_files[0]["filename"]
            file_url = version_files[0]["url"]

        mods_download_registry.append([file_name, file_url])

    for ps in success_slugs:
        getDownloadData(mods_data[ps])

    # download
    def downloadModFiles():
        threads = []

        download_data_grouped = list(grouper(mods_download_registry, DOWNLOAD_THREADS))
        for group in download_data_grouped:
            def _downloadGroup():
                for mod_download_data in group:
                    if mod_download_data != None:
                        file_name = mod_download_data[0]
                        file_url = mod_download_data[1]

                        r = requests.get(file_url)
                        file_content = r.content

                        mods_out_dir = Path(OUT_DIR_STR + "/" + out_subdir)

                        with open(mods_out_dir / file_name, "wb") as f:
                            f.write(file_content)
                            print(colored(scope, SCOPE_COLORS[scope]), colored("successfully downloaded: " + str(mods_out_dir) + "/" + file_name, "green"))

            t = threading.Thread(target=_downloadGroup)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    downloadModFiles()
    
    # retry failed slugs
    global retry_fetch_count
    if len(failed_slugs) > 0 and retry_fetch_count < RETRY_FETCH_LIMIT:
        retry_fetch_count += 1
        print(colored(scope, SCOPE_COLORS[scope]), colored("retrying fetch (attempt " + str(retry_fetch_count) + "), failed to fetch the following: " + ", ".join(failed_slugs), "red"))
        downloadSlugs(failed_slugs, out_subdir, scope)

# SKIBIDI
def createDirectory(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def downloadModlist():
    threads = []
    # scopes = ["client", "shared", "server"]

    # make directories
    modlist_dir = OUT_DIR_STR + "/" + MODLIST["modlist_name"]
    createDirectory(modlist_dir)

    def process_scope(scope):
        def _fn():
            scope_subdir = MODLIST["modlist_name"] + "/" + scope
            createDirectory(OUT_DIR_STR + "/" + scope_subdir)
            downloadSlugs(MODLIST[scope], scope_subdir, scope)

        t = threading.Thread(target=_fn)
        t.start()
        threads.append(t)

    process_scope("client")
    process_scope("shared")
    process_scope("server")
    
    for t in threads:
        t.join()

downloadModlist()
print(colored("download finished with:", "yellow"))
print(colored(str(failed_fetch_count) + " failed fetches", "red"))
print(colored(str(no_match_count) + " mods that did not match version or loader", "red"))