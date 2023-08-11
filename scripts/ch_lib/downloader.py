# -*- coding: UTF-8 -*-
import sys
import requests
import os
from . import util
import time
import subprocess
from pathlib import Path
import tqdm


dl_ext = ".downloading"

# disable ssl warning info
requests.packages.urllib3.disable_warnings()

# output is downloaded file path
def dl(url, folder, filename, filepath):
    util.printD("Start downloading from: " + url)
    # get file_path
    file_path = ""
    if filepath:
        file_path = filepath
    else:
        # if file_path is not in parameter, then folder must be in parameter
        if not folder:
            util.printD("folder is none")
            return
        
        if not os.path.isdir(folder):
            util.printD("folder does not exist: "+folder)
            return
        
        if filename:
            file_path = os.path.join(folder, filename)

    # first request for header
    rh = requests.get(url, stream=True, verify=False, headers=util.def_headers, proxies=util.proxies)
    # get file size
    total_size = 0
    total_size = int(rh.headers['Content-Length'])
    util.printD(f"File size: {total_size}")

    # if file_path is empty, need to get file name from download url's header
    if not file_path:
        filename = ""
        if "Content-Disposition" in rh.headers.keys():
            cd = rh.headers["Content-Disposition"]
            # Extract the filename from the header
            # content of a CD: "attachment;filename=FileName.txt"
            # in case "" is in CD filename's start and end, need to strip them out
            filename = cd.split("=")[1].strip('"')
            if not filename:
                util.printD("Fail to get file name from Content-Disposition: " + cd)
                return
            
        if not filename:
            util.printD("Can not get file name from download url's header")
            return
        
        # with folder and filename, now we have the full file path
        file_path = os.path.join(folder, filename)


    util.printD("Target file path: " + file_path)
    base, ext = os.path.splitext(file_path)

    # check if file is already exist
    count = 2
    new_base = base
    while os.path.isfile(file_path):
        util.printD("Target file already exist.")
        # re-name
        new_base = base + "_" + str(count)
        file_path = new_base + ext
        count += 1

    # use a temp file for downloading
    dl_file_path = new_base+dl_ext


    util.printD(f"Downloading to temp file: {dl_file_path}")

    try:
        get_single_file(url, dl_file_path)
    except Exception as e:
        print("Download Error")
        print(e)
        return ""
    
    os.rename(dl_file_path, file_path)
    util.printD(f"File Downloaded to: {file_path}")
    return file_path

def get_single_file(url, output_folder, start_from_scratch=False):
        s = requests.Session()
        filename = Path(url.rsplit('/', 1)[1])
        output_path = output_folder 
        headers = {}
        mode = 'wb'
        if output_path.exists() and not start_from_scratch:

            # Check if the file has already been downloaded completely
            r = s.get(url, stream=True, timeout=10)
            total_size = int(r.headers.get('content-length', 0))
            if output_path.stat().st_size >= total_size:
                return

            # Otherwise, resume the download from where it left off
            headers = {'Range': f'bytes={output_path.stat().st_size}-'}
            mode = 'ab'

        with s.get(url, stream=True, headers=headers, timeout=10) as r:
            r.raise_for_status()  # Do not continue the download if the request was unsuccessful
            total_size = int(r.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1MB
            with open(output_path, mode) as f:
                with tqdm.tqdm(total=total_size, unit='iB', unit_scale=True, bar_format='{l_bar}{bar}| {n_fmt:6}/{total_fmt:6} {rate_fmt:6}') as t:
                    count = 0
                    for data in r.iter_content(block_size):
                        t.update(len(data))
                        f.write(data)
                        