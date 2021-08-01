import subprocess
import os
import sys
import configparser
import re
import time
import logging
import threading
import multiprocessing

config = configparser.ConfigParser()
config.read("config.ini")

apks = []
MONKEY_TIME = 60 * 5

def switch_extension(name, extension):
    return os.path.splitext(name)[0] + extension

def get_package_name(apk_path):
    command = "aapt dump badging {} | grep package:\ name".format(apk_path)
    result = str(subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout)

    return re.search("name='(.*?)'", result).group(1)

def index_apks(dir):
    for filename in os.listdir(dir):
        if filename.endswith(".apk"):
            apks.append({
                "name" : filename,
                "path" : config["paths"]["apks"] + filename,
                "package_name" : get_package_name(config["paths"]["apks"] + filename),
            })

def uninstall_apk(apk):
    command = "acv uninstall {}".format(apk["package_name"])
    result = subprocess.run(command, shell=True)
    print(f"Passed uninstalling {apk['path']}")

def monkey_apk(apk):
    command = f"adb shell monkey -p {apk['package_name']} 999999999"
    subprocess.run(command, shell=True)
    print(f"Passed monkey for {apk['path']}")

def reporter(apk):
    time.sleep(1)
    subprocess.run(f"acv stop {apk['package_name']}", shell=True)

    pickle_path = switch_extension(config["paths"]["acvtoolworkingdir"] + "metadata/" + apk["name"], ".pickle")
    command = f"acv report {apk['package_name']} -p {pickle_path}"
    subprocess.run(command, shell=True)
    print(f"Passed reporting {apk['path']}")

def clean_up():
    c = "adb devices | grep emulator | cut -f1 | while read line; do adb -s $line emu kill; done"
    subprocess.run(c, shell=True)

    time.sleep(5)

    c = f"{config["paths"]["emulator"]} -avd {config["emulator"]["devicename"]} -wipe-data"
    subprocess.Popen(c, shell=True)

    c = "adb shell getprop init.svc.bootanim"
    while True:
        process =  subprocess.Popen(c, stdout=subprocess.PIPE, stderr=None, shell=True)
        output = process.communicate()[0].decode("utf-8")

        if "stopped" in output:
            return

        time.sleep(1)


def process_apk(apk):
    clean_up()

    path  = config["paths"]["acvtoolworkingdir"] + "instr_" + apk["name"]
    command = f"acv install {path}"
    subprocess.run(command, shell=True)

    subprocess.Popen(f"acv start {apk['package_name']}", shell=True)

    while True:
        f = open("../lock.txt", "r")
        if f.read(1) == "y":
            break

        time.sleep(0.5)

    proc = multiprocessing.Process(target=monkey_apk, args=(apk,))
    proc.start()

    time.sleep(MONKEY_TIME)

    command = "adb shell ps | awk '/com\.android\.commands\.monkey/ { system(\"adb shell kill \" $2) }'"
    subprocess.run(command, shell=True)

    time.sleep(3)

    if proc.is_alive():
        command = "adb shell ps | awk '/com\.android\.commands\.monkey/ { system(\"adb shell kill \" $2) }'"
        subprocess.run(command, shell=True)
        time.sleep(0.5)
        proc.terminate()

    proc2 = multiprocessing.Process(target=reporter, args=(apk,))
    proc2.start()

    time.sleep(30)

    if proc2.is_alive():
        proc2.terminate()

if __name__ == "__main__":
    index_apks(config["paths"]["apks"])

    for i in apks:
        process_apk(i)
        uninstall_apk(i)

    c = "adb devices | grep emulator | cut -f1 | while read line; do adb -s $line emu kill; done"
    subprocess.run(c, shell=True)

    time.sleep(5)

    c = f"{config["paths"]["emulator"]} -avd {config["emulator"]["devicename"]} -wipe-data"
    subprocess.Popen(c, shell=True)
