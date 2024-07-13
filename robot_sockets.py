import os, sys
import struct
import socket
from threading import Thread, currentThread, Lock
import time
import json

sys.path.append(os.environ['LIBS_PATH'])

import inrrobot

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
MAIN_SERVICE_IP = s.getsockname()[0]
ROBOT_PUBLISHER_SOCKET_PORT = int(os.environ['ROBOT_PUBLISHER_SOCKET_PORT'])
ROBOT_AUDIO_SOCKET_PORT = int(os.environ['ROBOT_AUDIO_SOCKET_PORT'])
ROBOT_IMAGE_SOCKET_PORT = int(os.environ['ROBOT_IMAGE_SOCKET_PORT'])
s.close()

exit_gracefully = False
robot_connected = False
all_robot_sockets_connected = False

publisher_socket = {
    "name": "publisher_socket",
    "port": ROBOT_PUBLISHER_SOCKET_PORT,
    "socket": None,
    "connection": None, # This is the connection address.
    "lock": Lock(),
    "connected": False,
    "connecting": False
}
audio_socket = {
    "name": "audio_socket",
    "port": ROBOT_AUDIO_SOCKET_PORT,
    "socket": None,
    "connection": None,
    "lock": Lock(),
    "connected": False,
    "connecting": False
}

robot_sockets_list = [publisher_socket, audio_socket]

def get_ip():
    h = inrrobot.sync_get_host()
    if h:
        return h["ip"]
    else:
        return None

def connection_robot():
    global exit_gracefully
    global robot_connected
    global all_robot_sockets_connected
    framerate = 10/60.0
    
    first_connection = True
    
    while not exit_gracefully:
        h = inrrobot.sync_get_host()
        try:        
            isRobotIdle = inrrobot.isExecuting()
            
            if not h or isRobotIdle is None: # Explicit comparison
                isConnectedRobot = False
                inrrobot.connect_async()
            else:
                isConnectedRobot = True

        except Exception as e:
            isConnectedRobot = False
            inrrobot.connect_async()
              
        if isConnectedRobot:
            if first_connection or not robot_connected:
                print("Robot connected: " + str(get_ip()))      
                robot_connected = True
        elif first_connection or robot_connected:
            print("Robot disconnected")
            robot_connected = False
            dispose_all_robot_sockets()
            all_robot_sockets_connected = False
            
        first_connection = False

        time.sleep(framerate)

def dispose_socket(socket_dict):
    ''' Needs a 'socket_dict'. This function closes the socket, sets it to None and sets its 'connected' status to False. 
    '''
    if socket_dict["connection"]:
        socket_dict["connection"].close()
        socket_dict["connection"] = None
    if socket_dict["socket"]:
        socket_dict["socket"].close()
        socket_dict["socket"] = None
    socket_dict["connected"] = False
    print("[INFO] " + socket_dict["name"] + " disposed.")

def dispose_all_robot_sockets():
    for socket_dict in robot_sockets_list:
        socket_dict["lock"].acquire()
        dispose_socket(socket_dict)
        socket_dict["lock"].release()

def create_and_connect_socket(socket_dict):
    socket_dict["connecting"] = True

    # Create a socket TCP/IP
    socket_dict["socket"] = None
    socket_dict["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_dict["socket"].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to an IP address and port
    socket_dict["socket"].bind((MAIN_SERVICE_IP, socket_dict["port"]))
    socket_dict["socket"].setblocking(False)
    socket_dict["socket"].settimeout(5)

    # Listen for incoming connections
    socket_dict["socket"].listen(1)

    # Accept a connection
    try:
        conn, addr = socket_dict["socket"].accept()
        if conn:
            print("Connection to " + socket_dict["name"] + " from " + str(addr) + ": OK")
            socket_dict["connection"] = conn
            socket_dict["connected"] = True
    except socket.error as e:
        print(socket_dict["name"], e)

    socket_dict["connecting"] = False

def robot_sockets_manager():
    global robot_sockets_list
    global all_robot_sockets_connected
    global robot_connected

    print("[INFO] " + currentThread().getName() + " STARTED")
    
    while not exit_gracefully:
        time.sleep(1) # Delay to properly detect changes in robot_connected variable.

        while ((not robot_connected) or all_robot_sockets_connected) and not exit_gracefully: # Wait for the robot to be connected.
            time.sleep(1)

        all_robot_sockets_connected = True
        for socket_dict in robot_sockets_list: # Check if any socket is disconnected.
            if not socket_dict["connected"] or exit_gracefully:
                all_robot_sockets_connected = False
                break

        # If any socket is disconnected, all are disposed and we ask robot for reconnection.
        if not all_robot_sockets_connected and robot_connected and not exit_gracefully:
            for socket_dict in robot_sockets_list:
                socket_dict["lock"].acquire()
                dispose_socket(socket_dict)
                socket_dict["lock"].release()
            inrrobot.startRobotSubscriptorConnection(str(MAIN_SERVICE_IP), retries=1)
            time.sleep(1)
            # Try to stablish sockets connection.
            for socket_dict in robot_sockets_list:
                if not socket_dict["connected"]:
                    socket_dict["lock"].acquire()
                    create_and_connect_socket(socket_dict)
                    socket_dict["lock"].release()

            all_robot_sockets_connected = True

            for socket_dict in robot_sockets_list: # Check if connection has worked.
                if not socket_dict["connected"]:
                    all_robot_sockets_connected = False
                    break

    print("[INFO] " + currentThread().getName() + " FINISHED")

def robot_data_listener(socket_dict):
    global robot_connected
    global robot_faces_detection
    global all_robot_sockets_connected

    print("[INFO] " + currentThread().getName() + " STARTED")

    while not exit_gracefully:
        if socket_dict["connected"] and socket_dict["connection"] and robot_connected and not exit_gracefully:
            inrrobot.maintainRobotSubscriptorConnection(str(MAIN_SERVICE_IP), retries=1)
            # Receive data from the robot
            message_complete = True

            if socket_dict["connection"]:
                header = socket_dict["connection"].recv(4)
                msg_length = struct.unpack('>I', header)[0]
                header = socket_dict["connection"].recv(4)
                binary_mode = struct.unpack('>I', header)[0]

                # Now, we get the complete message
                received_data = b''
                data_length = int(msg_length)

                #print("[DEBUG] binary_mode", binary_mode, "msg_length", msg_length)
                while len(received_data) < data_length or not message_complete and socket_dict["connection"]:
                    remaining_data = socket_dict["connection"].recv(data_length - len(received_data))
                    if not remaining_data:
                        message_complete = False
                    received_data += remaining_data

                if len(received_data) == data_length:
                    if binary_mode == 1:
                        try:
                            audio = received_data
                            with open(MAIN_PATH + '/robot_recording.ogg', 'wb') as file:
                                file.write(audio)
                            if len(audio) < min_duration * 1000:
                                print("The audio is too short.")
                            else:
                                print("Audio received.")
                        except Exception as e:
                            print(e)
                            socket_dict["connected"] = False
                            all_robot_sockets_connected = False
            
                else:
                    print("[WARNING] " + currentThread().getName() + ": Robot message uncomplete ---> Pub-sub connection lost")
                    socket_dict["connected"] = False
                    all_robot_sockets_connected = False
            
            else:
                print("[WARNING] " + currentThread().getName() + ": length_prefix not valid ---> Pub-sub connection lost")
                socket_dict["connected"] = False
                all_robot_sockets_connected = False

        else:
            time.sleep(1)
            #print("[DEBUG]", socket_dict["name"], "waiting")

    print("[INFO] " + currentThread().getName() + " FINISHED")

###############
# MAIN THREAD #
###############

thread_icebox = Thread(target=connection_robot, args=())
thread_icebox.start()

t_pub_sub_manager = Thread(target=robot_sockets_manager, name="robot_sockets_manager_thread")
t_pub_sub_manager.start()
for socket_dict in robot_sockets_list:
    thread_name = socket_dict["name"] + "_listener_thread"
    t_pub_sub = Thread(target=robot_data_listener, args=([socket_dict]), name=thread_name)
    t_pub_sub.start()
    
exit = input()
exit_gracefully = True


