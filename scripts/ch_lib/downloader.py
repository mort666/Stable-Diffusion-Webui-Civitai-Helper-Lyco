# -*- coding: UTF-8 -*-
import sys
import requests
import os
from . import util
from logger import logger
import time
import subprocess


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
    pid_num = os.fork()
    if pid_num!=0:
        while not os.path.exists(file_path):
            time.sleep(30)
            if os.path.exists(dl_file_path):
                downloaded_size = os.path.getsize(dl_file_path)
                util.printD(f"Downloaded size: {downloaded_size}/{total_size}")
        return file_path

    # check if downloading file is exsited
    log_file = open(f'{dl_file_path}.txt', 'w')
    while not os.path.exists(file_path):
        downloaded_size = 0
        if os.path.exists(dl_file_path):
            downloaded_size = os.path.getsize(dl_file_path)
        try:
            subprocess.run(['wget', '-c', url, '-O', dl_file_path], timeout=120, stdout=log_file, stderr=log_file)
        except Exception as e:
            pass
        log_file.write(f'{dl_file_path} downloaded')
        if os.path.exists(dl_file_path):
            downloaded_size = os.path.getsize(dl_file_path)
        if downloaded_size>total_size-1:
            log_file.write(f'{downloaded_size}/{total_size}')
            os.rename(dl_file_path, file_path)
            log_file.close()
            util.printD(f"Downloaded size: {downloaded_size}")
            util.printD(f"File Downloaded to: {file_path}")
            os._exit(0)
