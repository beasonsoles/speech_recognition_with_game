#!/usr/bin/env python3

# Copyright 2021 by Inrobics Social Robotics, S.L.L.
# Jose Carlos Gonzalez Dorado.
# All rights reserved.

import sys
import socket
import struct
import json
import time
import os
import threading
import inspect
from threading import Thread

from inrutil import *
import inrzeroconf

MAX_RETRIES = 30
TIMEOUT = 1 #previously 0.5
MIN_BYTES_TO_PRINT_PROGRESS = 200 * 1024

mutexConnecting = threading.Lock()
syncHost = None
mutexHost = threading.Lock()
syncConnecting = False
mutexSocket = threading.Lock()

if os.environ['ROBOT_IP'].lower().strip() == "none":
    printerr("ROBOT_IP is set to 'none'. Skipping all orders.", "inrrobot", warning=True)


# send_order("isExecuting", [], True, ignore_errors=True)
def send_order(function_name, parameters=[], reply_required=False, ignore_errors=False, max_retries=MAX_RETRIES, binary_mode=0):
    #print("send_order START")
    #print(function_name, parameters)
    
    if function_name != None and (function_name not in globals() or type(send_order) != type(globals()[function_name])): # If it not exists or it is not a function
        printerr("Unknown robot action " + function_name, "inrrobot.send_order", warning=True)
        return
    
    if os.environ['ROBOT_IP'].lower().strip() == "none":
        if function_name == "isExecuting":
            return False
        else:
            return "none"
    
    params = parameters
    if parameters is None:
        params = []
        
    #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.settimeout(TIMEOUT)
        
    connection_ok = False
    retry = 0
    s = None
    
    while(not connection_ok and retry < max_retries):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        timer = time.time()
        exception = None
        try:
            host = sync_get_host()
            if host:
                s.connect((host["ip"], host["portforced"]))
                connection_ok = True
        except Exception as e:
            exception = e
            
        if not connection_ok:
            retry = retry + 1
            
            if not ignore_errors and retry < max_retries:
                printerr(function_name + " Persee->Robot. Retry " + str(retry) + " of " + str(max_retries) + "...", "inrrobot.send_order")
                if not exception or not isinstance(exception, socket.timeout):
                    sleep_min(timer, TIMEOUT)
            elif not ignore_errors:
                printerr(function_name + " Persee->Robot. Ignoring.", "inrrobot.send_order", exception)

            else:
                retry = max_retries

            try:
                s.shutdown(socket.SHUT_RDWR) # Finished sending and receiving. Free resources.
                s.close()
            except Exception as e:
                if not ignore_errors:
                    printerr(function_name + " Failure shutting down Persee->Robot (" + str(e) + ")", "inrrobot.send_order")

    out = None
    bin_mode = 0
    if connection_ok:
        mutexSocket.acquire()
        if binary_mode == 0:
            send_msg(s, get_command(function_name, params))
        else:
            send_msg(s, params[0], binary_mode=binary_mode)
        mutexSocket.release()

        if reply_required:
            #print("Waiting for response...")
            #s.shutdown(socket.SHUT_WR) # Finished sending. Still receiving.
                        
            retry = 0
            data_received = False
            while(not data_received and retry < max_retries):
                timer = time.time()
                try:
                    out, bin_mode = recv_msg(s)
                    data_received = True
                except Exception as e:
                    retry = retry + 1
                    if retry < max_retries:
                        if not ignore_errors:
                            printerr(function_name + " Robot->Persee. Retry " + str(retry) + " of " + str(max_retries) + "...", "inrrobot.send_order")
                        if not isinstance(e, socket.timeout):
                            sleep_min(timer, TIMEOUT)
                    else:
                        if not ignore_errors:
                            printerr(function_name + " Robot->Persee. Ignoring.", "inrrobot.send_order", e)
        try:
            s.shutdown(socket.SHUT_RDWR) # Finished sending and receiving. Free resources.            
            s.close()
        except Exception as e:
            if not ignore_errors:
                printerr(function_name + " Failure shutting down Robot->Persee (" + str(e) + ")", "inrrobot.send_order")
            
    #print("send_order END")
    if bin_mode == 0:
        return out
    else:
        return out, bin_mode

def send_order_local(function_name, parameters=[], reply_required=False, ignore_errors=False, max_retries=MAX_RETRIES, binary_mode=0):
    #print("send_order START")
    #print(function_name, parameters)
    
    if function_name != None and (function_name not in globals() or type(send_order) != type(globals()[function_name])): # If it not exists or it is not a function
        printerr("Unknown robot action " + function_name, "inrrobot.send_order", warning=True)
        return
    
    params = parameters
    if parameters is None:
        params = []
        
    #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.settimeout(TIMEOUT)
        
    connection_ok = False
    retry = 0
    s = None
    
    while(not connection_ok and retry < max_retries):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        timer = time.time()
        exception = None
        try:
            host = sync_get_host()
            if host:
                s.connect(("127.0.0.1", 9558))
                connection_ok = True
        except Exception as e:
            exception = e
            
        if not connection_ok:
            retry = retry + 1
            
            if not ignore_errors and retry < max_retries:
                printerr(function_name + " Persee->Robot. Retry " + str(retry) + " of " + str(max_retries) + "...", "inrrobot.send_order")
                if not exception or not isinstance(exception, socket.timeout):
                    sleep_min(timer, TIMEOUT)
            elif not ignore_errors:
                printerr(function_name + " Persee->Robot. Ignoring.", "inrrobot.send_order", exception)

            else:
                retry = max_retries

            try:
                s.shutdown(socket.SHUT_RDWR) # Finished sending and receiving. Free resources.
                s.close()
            except Exception as e:
                if not ignore_errors:
                    printerr(function_name + " Failure shutting down Persee->Robot (" + str(e) + ")", "inrrobot.send_order")

    out = None
    bin_mode = 0
    if connection_ok:
        mutexSocket.acquire()
        if binary_mode == 0:
            send_msg(s, get_command(function_name, params))
        else:
            send_msg(s, params[0], binary_mode=binary_mode)
        mutexSocket.release()

        if reply_required:
            #print("Waiting for response...")
            #s.shutdown(socket.SHUT_WR) # Finished sending. Still receiving.
                        
            data_received = False
            while(not data_received):
                timer = time.time()
                try:
                    out, bin_mode = recv_msg(s)
                    data_received = True
                except Exception as e:
                    time.sleep(0.2)
        try:
            s.shutdown(socket.SHUT_RDWR) # Finished sending and receiving. Free resources.            
            s.close()
        except Exception as e:
            if not ignore_errors:
                printerr(function_name + " Failure shutting down Robot->Persee (" + str(e) + ")", "inrrobot.send_order")
            
    #print("send_order END")
    if bin_mode == 0:
        return out
    else:
        return out, bin_mode
    
def get_robot_host():    
    out = None
    mode = get_robot_detection_mode()
    
    # auto
    if mode == 1:
        out = inrzeroconf.get_host("naoqi", int(os.environ['ROBOT_SOCKET_PORT']))
                        
    # static (includes "localhost")
    elif mode == 2:
        ice_needed = False
        if os.environ['ROBOT_ICE'].lower().strip() == "true":
            ice_needed = True
            
        out = inrzeroconf.Host()
        out["service"] = "naoqi"
        out["ip"] = os.environ['ROBOT_IP'].lower().strip()
        out["port"] = int(os.environ['ROBOT_SOCKET_PORT'])
        out["portforced"] = int(os.environ['ROBOT_SOCKET_PORT'])
        out["ice"] = ice_needed
        
        if not inrzeroconf.is_connected(out, out["port"]):
             out = None
             
    # none (mode == 3) 
    
    return out


def get_robot_detection_mode():
    # auto
    if "ROBOT_IP" not in os.environ or "ROBOT_SOCKET_PORT" not in os.environ or os.environ['ROBOT_IP'].lower().strip() == "auto":
        return 1
            
    # none
    elif os.environ['ROBOT_IP'].lower().strip() == "none":
        return 3
            
    # static (includes "localhost")
    else:
        return 2


def connect(host_forced=None):
    l = sync_lock_connecting()
    if not l:
        return
    
    if host_forced:
        sync_set_host(host_forced)
    else:
        sync_set_host(get_robot_host())
            
    mode = get_robot_detection_mode()
    
    if mode == 1:
        print("  Robot IP (auto) ")
    elif mode == 2:
        print("  Robot IP (static) " + os.environ['ROBOT_IP'].lower().strip() + ":" + os.environ['ROBOT_SOCKET_PORT'].lower().strip() + " ")
    elif mode == 3:
        print("  Robot IP (none) ")

    timeout = False
    if not host_forced:
        while not sync_get_host() and mode != 3:
            timer = time.time()
            sync_set_host(get_robot_host())
            sleep_min(timer, TIMEOUT)
    else:
        timer_forced = time.time()
        host = sync_get_host()
        while not timeout and not inrzeroconf.is_connected(host, host["portforced"]):
            if(time.time() - timer_forced > 5):
                timeout = True
            else:
                timer = time.time()
                sleep_min(timer, TIMEOUT)
                
        if not timeout:
            sync_set_host(inrzeroconf.hosts["naoqi"])
        else:
            sync_set_host(inrzeroconf.Host())

    host = sync_get_host()

    if mode==3:
        print("OK  robot:none. Accepting all robot functions.")
    elif not host_forced or not timeout:
        print("OK  " + host["ip"] + ":" + str(host["portforced"]))
    else:
        print("Error connecting to robot host " + host["ip"] + ":" + str(host["portforced"]))
        
    sync_unlock_connecting()


def sync_is_locked_connecting():
    mutexConnecting.acquire()
    out = syncConnecting
    mutexConnecting.release()
    return out

def sync_lock_connecting():
    mutexConnecting.acquire()

    global syncConnecting
    out = True
    if syncConnecting:
        out = False
    syncConnecting = True
    
    mutexConnecting.release()
    return out
    
def sync_unlock_connecting():
    mutexConnecting.acquire()    

    global syncConnecting
    syncConnecting = False
    
    mutexConnecting.release()

def sync_get_host():
    mutexHost.acquire()    
    out = syncHost
    mutexHost.release()
    return out   


def sync_set_host(value):
    mutexHost.acquire()
    global syncHost
    syncHost = value
    mutexHost.release()
    

def connect_async_function(host_forced=None):
    l = sync_lock_connecting()
    if not l:
        return
    
    if host_forced:
        sync_set_host(host_forced)
    else:
        sync_set_host(get_robot_host())

    mode = get_robot_detection_mode()
    
    while not sync_get_host() and mode != 3:
        timer = time.time()
        sync_set_host(get_robot_host())
        sleep_min(timer, TIMEOUT)

    sync_unlock_connecting()
   

def connect_async(host_forced=None):
    if sync_is_locked_connecting(): # To avoid creating too many threads.
        return
    Thread(target=connect_async_function, args=(host_forced,)).start()


def set_ice_communicator(communicator):
    inrzeroconf.set_ice_communicator(communicator)


def sleep_min(timer, delay_min):
    elapsed = time.time() - timer
    if elapsed < delay_min:
        time.sleep(delay_min - elapsed)


def is_ice_order():
    host = sync_get_host()
    if host and host["ice"] and host["iceprx"]:
        return True
    
    return False

#################################
#     ROBOT STATE FUNCTIONS     #
#################################

def startProcessing():
    return send_order_local("startProcessing", [], reply_required=True)

def startRobotSubscriptorConnection(MS_IP, retries=MAX_RETRIES):
    return send_order("startRobotSubscriptorConnection", [MS_IP], max_retries=retries)

def maintainRobotSubscriptorConnection(MS_IP, retries=MAX_RETRIES):
    send_order("maintainRobotSubscriptorConnection", [MS_IP], max_retries=retries)
    
def getInrobicsVersion():
    return send_order("getInrobicsVersion", [])

def getConnectionData():
    return send_order("getConnectionData", [], True)

def isSimulated():
    return send_order("isSimulated", [], True)
        
def isConnected():
    return send_order("isConnected", [], True, ignore_errors=True)
    
def isExecuting():
    return send_order("isExecuting", [], True, ignore_errors=True)

def isSpeaking():
    return send_order("isSpeaking", [], True, ignore_errors=True)

def isMoving():
    return send_order("isMoving", [], True, ignore_errors=True)

def isResting(retries=MAX_RETRIES):
    return send_order("isResting", [], True, ignore_errors=True, max_retries=retries)

def getGlobalVariableValue(variable, retries=MAX_RETRIES):
    return send_order("getGlobalVariableValue", [variable], True, max_retries=retries)

def setWaitingBehaviors(activated, from_app=False):
    send_order("setWaitingBehaviors", [activated, from_app])

#################################
#     ROBOT CALLS FUNCTIONS     #
#################################
    
def clearCalls():
    send_order("clearCalls")
    
def clearCallsBackground():
    send_order("clearCallsBackground")    

def printCalls():
    send_order("printCalls")

def moveBackgroundCallsToFront(): # has return to improve synchronization
    send_order("moveBackgroundCallsToFront", [], True)  

##################################
#     ROBOT HEALTH FUNCTIONS     #
##################################

def getRobotTemperature():
    return send_order("getRobotTemperature", [], True)

def getFallDetection():
    return send_order("getFallDetection", [], True)

################################
#     ROBOT INFO FUNCTIONS     #
################################

def getRobotVersion():
    return send_order("getRobotVersion", [], True)

def getInstalledBehaviors():
    return send_order("getInstalledBehaviors", [], True)

def getLanguagesInstalled():
    return send_order("getLanguagesInstalled", [], True)

#################################
#     ROBOT BASIC FUNCTIONS     #
#################################

def reboot():
    send_order("reboot")

def shutdown():
    send_order("shutdown")    
    
def wakeUp(from_app=False):
    send_order("wakeUp", [from_app])

def rest(from_app=False, forced=False):
    send_order("rest", [from_app, forced]) 

def restartRobotComp(): # TODO: Check if this should have this return for synchronization reasons.
    send_order("restartRobotComp", [], True)

#################################
#   APP INTERACTION FUNCTIONS   #
#################################

def setAppConnected(connected, retries=MAX_RETRIES):
    send_order("setAppConnected", [connected], max_retries=retries)

def setPerformanceMode(mode):
    send_order("setPerformanceMode", [mode])

def configWaitingBehaviors(new_period, period_type=None):
    send_order("configWaitingBehaviors", [new_period, period_type])

def setExerciseConfigured(exercise):
    send_order("setExerciseConfigured", [exercise])

def setSessionConfigStatus(status):
    send_order("setSessionConfigStatus", [status])

def sessionFinished(cancelled=False, chatter=False):
    send_order("sessionFinished", [cancelled, chatter]) 

###################################
#     ROBOT CHATTER FUNCTIONS     #
###################################
        
def setChatterStatus(status, opt="listening"):
    send_order("setChatterStatus", [status, opt])

################################
#     ROBOT LEDS FUNCTIONS     #
################################

def setLeds(ledGroup, intensity):
    send_order("setLeds", [ledGroup, intensity]) 

def executeLEDAnimation(animation_name, t1=0, t2=0, n_reps=1, background=False): # t1: delayInitial (in seconds), t2: duration (in seconds), n_reps: repetitions
    send_order("executeLEDAnimation", [animation_name, t1, t2, n_reps, background])

def stopAllLEDs():
    send_order("stopAllLEDs")

def setFeedbackCircular(feedback, left, color="green"):
    send_order("setFeedbackCircular", [feedback, left, color])

def setLedsColor(leds, color, intensity):
    send_order("setLedsColor", [leds, color, intensity])

def setPoseFeedback(left_correctness, left_threshold, right_correctness, right_threshold):
    send_order("setPoseFeedback", [left_correctness, left_threshold, right_correctness, right_threshold])

##################################
#     ROBOT SPEECH FUNCTIONS     #
##################################

def setLanguage(language, restore_volumes=True):
    send_order("setLanguage", [language, restore_volumes], False)

def getLanguageCurrent():
    return send_order("getLanguageCurrent", [], True)

def say(speech, synthesize=True, pitch=0.0, lower_music=False, speed=1.0, t0=0, end=None, background=False):
    send_order("say", [speech, synthesize, pitch, lower_music, speed, t0, end, background])
    
def sayAnimated(speech, synthesize=True, pitch=0.0, lower_music=False, background=False):
    send_order("sayAnimated", [speech, synthesize, pitch, lower_music, background])    

    
#################################
#     ROBOT AUDIO FUNCTIONS     #
#################################

def setVolume(volume, vol_type="general"): # general [0-100]
    send_order("setVolume", [volume, vol_type])
        
def getVolume(vol_type="general"):
    return send_order("getVolume", [vol_type], True) 

def playAudioFile(file, file_volume=1.0, vol_type='session', t0=0.0, position=0.0, background=True):
    send_order("playAudioFile", [file, file_volume, vol_type, t0, position, background]) # NaoI function has more parameters than used in architecture

def setMusicForced(music):
    send_order("setMusicForced", [music], True)

def setMusic(music):
    send_order("setMusic", [music])

def playMusic(volume=1.0, vol_type='session', position=0.0):
    send_order("playMusic", [volume, vol_type, position])

def stopMusic():
    send_order("stopMusic", [], True)
    
def stopAllSounds():
    send_order("stopAllSounds", [], True)    

def setRobotConfig(name, value):
    send_order("setRobotConfig", [name, value])

def setRobotDefaultConfig(from_app=False, restore_volumes=True):
    send_order("setRobotDefaultConfig", [from_app, restore_volumes])
    
#####################################
#     ROBOT RECORDING FUNCTIONS     #
#####################################

def startAudioRecording():
    send_order("startAudioRecording")

def stopAudioRecording():
    send_order("stopAudioRecording")

##################################
#      ROBOT BODY FUNCTIONS      #
##################################

def getJointNames():
    return send_order("getJointNames", [], True)
    
def getJointCurrentAngles(jointNames): # Default value returns all joint angles in the same order as getJointNames()
    return send_order("getJointCurrentAngles", [jointNames], True)

def getPostureFamily():
    return send_order("getPostureFamily", [], True)

##################################
#     ROBOT MOTION FUNCTIONS     #
##################################

def setAngles(jointNames, jointAngles, speed, background=False):
    send_order("setAngles", [jointNames, jointAngles, speed, background])
    
def setAngleInterpolation(list_names, list_keys, list_times, background=False):
    send_order("setAngleInterpolation", [list_names, list_keys, list_times, background])

def executeAnimation(name, speed, background=False, priority=False, refresh=True, from_app=False):
    send_order("executeAnimation", [name, speed, background, priority, refresh, from_app])

def setAnglesFromVision(angles, mirrored, speed, background=False):
    send_order("setAnglesFromVision", [angles, mirrored, speed, background])

def setRemoteMoveRobot(activated, strMoveConfig="slow", direction=None):
    send_order("setRemoteMoveRobot", [activated, strMoveConfig, direction])

def setMantainMoveRobot():
    send_order("setMantainMoveRobot")

def coordMoveRobot(x, y, theta, strMoveConfig="slow", feedback=False):
    send_order("coordMoveRobot", [x, y, theta, strMoveConfig, feedback])

def setPushRecoveryEnabled(activated): # exclusive for NAO robot
    send_order("setPushRecoveryEnabled", [activated])

####################################
#       AUTONOMOUS MOVEMENTS       #
####################################  

def setAutonomousMovements(joint_group, activated):
    send_order("setAutonomousMovements", [joint_group, activated])
    
def allowAutonomousMovements(activated): # FIXME: Deprecated
    if activated:
        send_order("setAutonomousMovements", ["Head", True])
        send_order("setAutonomousMovements", ["Arms", False])
        send_order("setAutonomousMovements", ["Legs", True])
    else:
        send_order("setAutonomousMovements", ["All", False])

def pauseAutonomousMovements():
    send_order("pauseAutonomousMovements")
    
def refreshAutonomousMovements():
    send_order("refreshAutonomousMovements")

###################################
#     ROBOT BUTTONS FUNCTIONS     #
###################################

def getLastButtonPressed():
    return send_order("getLastButtonPressed", [], True)

#################################
#       COMPLEX FUNCTIONS       #
#################################

def executeFullRoutine(speech, animation, str_audios='', anim_speed=1, background=True):
    send_order("executeFullRoutine", [speech, animation, str_audios, anim_speed, background])
    
#####################################
#     LOGS AND UPDATE FUNCTIONS     #
#####################################

def getLogFile():
    return send_order("getLogFile", [], True)
    
def unpackUpdate(update_file):
    send_order("unpackUpdate", [update_file])
    
def installUpdate():
    send_order("installUpdate")
    
def getUpdateResult():
    return send_order("getUpdateResult", [], True, ignore_errors=True)

###################################
#     ROBOT CONTROL FUNCTIONS     #
###################################

def stopAllRobotTasks():
    send_order("stopAllRobotTasks")

#########################
#    DEBUG FUNCTIONS    #
#########################
# These functions are not called in session or by the architecture.
        
def setNaoCompStarted(value):
    send_order("setNaoCompStarted", [value])

def setFallDetection(activated):
    send_order("setFallDetection", [activated])

def setTemperatureStatus(status):
    send_order("setTemperatureStatus", [status])

def getTemperatureValues():
    return send_order("getTemperatureValues", [], True)

def setPrintCalls(activated):
    return send_order("setPrintCalls", [activated])

def setFaceTracking(activated, from_app=False):
    send_order("setFaceTracking", [activated, from_app])

def clearFacesDatabase():
    send_order("clearFacesDatabase")
    
def learnFace(strFaceID="CurrentPatient"):
    send_order("learnFace", [strFaceID])

def isSomeALModuleRunning(module_names, exceptions='none'):
    return send_order("isSomeALModuleRunning", [module_names, exceptions], True)

def killSomeALModuleTasks(modules_to_kill, tasks_to_kill_ids = "all"):
    send_order("killSomeALModuleTasks", [modules_to_kill, tasks_to_kill_ids])

def killAllAnimations():
    send_order("killAllAnimations")

def executePlayAudioFile(file, file_volume=1.0, vol_type='session', t0=0.0, position=0.0, background=True):
    send_order("executePlayAudioFile", [file, file_volume, vol_type, t0, position, background])

#################################
#    PEPPER TABLET FUNCTIONS    #
#################################

def playGame(name=None):
    send_order("playGame", [name])

def setInterface(name, params):
    send_order("setInterface", [name, params])

def isReady():
    return send_order("isReady", [], True)

def getResult():
    return send_order("getResult", [], True)

def getTabletGame():
    return send_order("getTabletGame", [], True)

def startGame(game):
    send_order("startGame", [game])

def showSpeechScreen(picture, background=False): # SFF
    send_order("showSpeechScreen", [picture, background])  

def showScreenPicture(speech, background=False): # SFF
    send_order("showScreenPicture", [speech, background])   

def runBehavior(behavior_request, from_app=False, h2l_file=''):
    send_order("runBehavior", [behavior_request, from_app, h2l_file])

def runBehaviorString(behavior_string):
    send_order("runBehaviorString", [behavior_string])

def runBehaviorLows(lows_pack):
    while len(lows_pack) > 0:
        if (not isExecuting()):
            pack = lows_pack.pop(0)
            print("Pack,", len(pack))
            for subRoutine in pack:
                print("\tsubRoutine ->", subRoutine)
                exec(subRoutine)
            # while not isExecuting(): don't use as it blocks forever, if there is a non blocking lows
            #     time.sleep(0.25)
            time.sleep(1)
        time.sleep(0.5)

def binarytestA():
    bytestest = bytes(range(97, 107))
    send_order(None, [bytestest], binary_mode=2)
    
def binarytestB():
    bytestest = bytes(range(107, 117))
    send_order(None, [bytestest], binary_mode=3)

##########################
# CUSTOM SOCKET PROTOCOL #
##########################

def get_command(function, parameters):
    return {"function": function, "parameters": parameters}


# https://stackoverflow.com/a/17668009
def send_msg(sock, msg, binary_mode=0):
    m = msg
    if binary_mode == 0:
        # Serializing the message to JSON and then encoding it to UTF-8
        m = json.dumps(msg).encode('utf-8')
    # Prefix each message with a 5-byte length (network byte order)
    m = struct.pack('>IB', len(m), binary_mode) + m
    sock.sendall(m)


def recv_msg(sock):
    # Read message length and unpack it into an integer
    header = recvall(sock, 5)
    if not header:
        return None, None
    msglen, binary_mode = struct.unpack('>IB', header)
    # Read the message data
    data = recvall(sock, msglen)
    if data is None:
        return data, binary_mode
    if binary_mode == 0: # JSON mode (not binary)
        data = json.loads(data.decode('utf-8'))
    return data, binary_mode


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    verb = False
    if n >= MIN_BYTES_TO_PRINT_PROGRESS:
        verb = True
    data = bytearray()
    bytes_processed = 0
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            if verb:
                print("\n")
            return None
        if verb:
            bytes_processed = bytes_processed + len(data)
            print("Received " + str(bytes_processed) + " / " + str(n) + " bytes\r"),  # The comma avoids the final newline. \r Returns to the start of the line.
        data.extend(packet)
    if verb:
        print("\n")
    return data

