#!/usr/bin/env python3

import sys
import time
import traceback
import subprocess
import re

def printerr(message=None, function_name=None, exception=None, warning=False):
    out = "\n"
    
    if warning:
        out += "WARNING "
    elif exception:
        out += "EXCEPTION "
    else:
        out += "ERROR "
        
    out += str(time.time())
    
    if function_name:
        out += " " + function_name + "()"
    
    if message:
        out += ": " + str(message)
        
    out += "\n"
        
    sys.stderr.write(out)
    sys.stderr.flush()
    
    if exception:
        traceback.print_exc()

def get_all_connected_ips(service):
    # inrobics for Persee
    # naoqi for Nao robot
    shell_output = str(subprocess.check_output(["avahi-browse", "-rpt", "_" + service + "._tcp"]))
    regex = r"=;([^;]*);IPv4;[^;]*;_" + service + "\._tcp;[^;]*;([^;]*\.[^;]*);(\d*\.\d*\.\d*\.\d*);(\d*)"
    matches = re.finditer(regex, shell_output, re.MULTILINE)

    output = dict()
    for match in matches:
        entry = dict()
        entry["network"] = match.group(1)
        entry["domain"] = match.group(2)
        entry["ip"] = match.group(3)
        entry["port"] = int(match.group(4))
        output[entry["ip"]] = entry

    return output

