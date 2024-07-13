#!/usr/bin/env python3

# Copyright 2023 by Inrobics Social Robotics, S.L.L.
# Jose Carlos Gonzalez Dorado.
# All rights reserved.

import subprocess
import socket
import pickle
import struct
import re
import os
import traceback
import atexit
import json
from threading import Thread

TIMEOUT = 1

hosts = dict()  # Key: service name. Value: host struct

def is_connected(host, port=None): # It is possible to try the connection in a different port from the one reported in the located avahi host, like Naoqi (9556) and NaoComp (17700) which uses the same service (_naoqi._tcp).
    p = port
    if not p:
        p = host["port"]
    
    if host["ice"]: # Ice socket
        return False
            
    else: # Python socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(TIMEOUT)
            s.connect((host["ip"], p))
            s.sendall(struct.pack('>IB', 0, 1)) # length = 0, binary_mode = 1
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            set_host(host)
            return True
        except Exception as e:
            #traceback.print_exc()
            return False


def get_host(service, port=None):
    out = None
    hosts_found = locate_hosts(service, port)
    
    # Try first the last succesful known IP for this service.
    if service in hosts and hosts[service]["ip"] in hosts_found:
        if is_connected(hosts_found[hosts[service]["ip"]], port):
            out = hosts[service]
        
    # If the last succesful known IP does not work or it does not exist, try local.
    elif "127.0.0.1" in hosts_found:
        if is_connected(hosts_found["127.0.0.1"], port):
            out = hosts_found["127.0.0.1"]
    
    # If local robot does not exists, try the rest.
    else:
        for h in hosts_found:
            if is_connected(hosts_found[h], port):
                out = hosts_found[h]
                break

    #print(str(out))
    return out


def Host():
    out = dict()
    out["service"] = None
    out["network"] = None
    out["domain"] = None
    out["ip"] = None
    out["port"] = None
    out["portforced"] = None
    out["txt"] = dict()
    out["ice"] = None
    out["iceprx"] = None
    return out


def locate_hosts(service, port=None):
    shell_output = str(subprocess.check_output(["avahi-browse", "-rpt", "_" + service + "._tcp"], encoding='utf-8'))
    regex = r"=;([^;]*);IPv4;[^;]*;_" + service + "\._tcp;[^;]*;([^;]*\.[^;]*);(\d*\.\d*\.\d*\.\d*);(\d*);?(.*)?"
    regex_txt = r'\"(.*?)\"'
    
    matches = re.finditer(regex, shell_output, re.MULTILINE)
    
    out = dict() # Key: IP. Value: host struct

    for match in matches:
        entry = Host()
        entry["service"] = service
        entry["network"] = match.group(1)
        entry["domain"] = match.group(2)
        entry["ip"] = match.group(3)
        entry["port"] = int(match.group(4))
        entry["portforced"] = entry["port"]
        if port:
            entry["portforced"] = port
        
        txt = re.findall(regex_txt, match.group(5))
        for t in txt:
            parts = t.split("=")
            entry["txt"][parts[0]] = parts[1]
        
        if "RobotMaterialization" not in entry["txt"] or entry["txt"]["RobotMaterialization"].lower().strip() != "avatar":
            entry["ice"] = False  # Python robot socket
        else:
            entry["ice"] = True   # Ice robot socket
        
        out[entry["ip"]] = entry
                        
    #print(str(out))
    return out


def get_host_async(service, port=None):
    Thread(target=get_host, args=(service,port,)).start()


def set_host(host):
    hosts[host["service"]] = host
        
"""
def set_ice_communicator(communicator):
    global ice_communicator
    if ice_communicator and ice_communicator != communicator:
        ice_communicator.destroy()
    ice_communicator = communicator


def destroy_ice():
    if ice_communicator:
        try:
            ice_communicator.destroy()
        except:
            traceback.print_exc()


atexit.register(destroy_ice)
"""

