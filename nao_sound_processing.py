#! /usr/bin/env python

"""Example: Get Signal from Front Microphone & Calculate its rms Power"""


import qi
import argparse
import sys
import time
import numpy as np
import os
import socket
import traceback
import struct
import json
import errno


from naoqi import ALModule
from naoqi import ALBroker

MIN_BYTES_TO_PRINT_PROGRESS = 200 * 1024
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

class SoundProcessingModuleClass(ALModule):
    """
    A simple get signal from the front microphone of Nao & calculate its rms power.
    It requires numpy.
    """
    def __init__(self, name):
        self.name = str(name)
        try:
            ALModule.__init__(self, name)
        except:
            print("[WARNING] " + self.name + " is already registered, regerenating the module ...")
            ALMemory.unregisterModuleReference(self.name)
            ALModule.__init__(self, self.name)
            
        print(self.name + " has been created.")

        # Get the service ALAudioDevice.
        self.audio_service = session.service("ALAudioDevice")
        self.isProcessingDone = False
        self.nbOfFramesToProcess = 300
        self.framesCount=0
        self.micFront = []
        self.audio_rms = []
        self.timeout = 3
        self.speaking = False
        self.threshold = -35
        self.base_level = 0.0
        self.stDev = 0.0
        self.count = 0
        self.module_name = "SoundProcessingModule"

    def startProcessing(self):
        """
        Start processing
        """
        # reset audio list and counter
        self.audio_rms = []
        self.count = 0
        # ask for the front microphone signal sampled at 16kHz
        # if you want the 4 channels call setClientPreferences(self.module_name, 48000, 0, 0)
        print("AUDIO SERVICE:", self.audio_service)
        self.audio_service.setClientPreferences(self.module_name, 16000, 3, 0)
        self.audio_service.subscribe(self.module_name)


        while self.count <= 5:
            time.sleep(0.1)
        
        self.base_level, self.stDev = self.detectBaseLevel(self.audio_rms)
        
        while self.speaking == False:
            self.speaking = self.detectVoice(self.audio_rms)
        while self.speaking == True:
            self.speaking = self.detectSilence(self.audio_rms)
        
        print("detected silence")

        self.audio_service.unsubscribe(self.module_name)

        return True

    def processRemote(self, nbOfChannels, nbOfSamplesByChannel, timeStamp, inputBuffer):
        """
        Compute RMS from mic.
        """
        self.count += 1
        # convert inputBuffer to signed integer as it is interpreted as a string by python
        self.micFront=self.convertStr2SignedInt(inputBuffer)
        # compute the rms level on front mic
        rmsMicFront = self.calcRMSLevel(self.micFront)
        self.audio_rms.append(rmsMicFront)
        print(str(rmsMicFront))

    def calcRMSLevel(self,data) :
        """
        Calculate RMS level
        """
        rms = 20 * np.log10( np.sqrt( np.sum( np.power(data,2) / len(data)  )))
        return rms

    def convertStr2SignedInt(self, data):
        """
        This function takes a string containing 16 bits little endian sound
        samples as input and returns a vector containing the 16 bits sound
        samples values converted between -1 and 1.
        """
        signedData = []
        ind = 0
        for i in range(len(data) // 2):
            value = ord(data[ind]) + (ord(data[ind + 1]) << 8)
            if value >= 32768:
                value -= 65536
            signedData.append(value / 32768.0)
            ind += 2

        return signedData
    
    def detectBaseLevel(self, data): 
        """
        Detect initial volume level in data
        """
        base_level = np.mean(data[:5])
        std = np.std(data[:5])

        print("Base level: ", base_level)
        print("Standard deviation: ", std)
        self.audio_rms = []

        return base_level, std
    
    def detectVoice(self, data): 
        """
        Detect voice in data
        """
        speaking = False
        for i in range(len(data)):
            if data[i] > self.threshold:
                # check if patient has started speaking
                speaking = True
                print("Voice detected")
        
        return speaking

    def detectSilence(self, data): 
        """
        Detect silence in data
        """
        #time_per_period = 1024 / 16000.0 # TODO: PERIOD SIZE???
        #max_silence_periods = int(self.timeout / time_per_period) # max number of periods of continuous silence
        silence_count = 0
        speaking = True

        if len(data) > 35:
            print(len(data))
            max_frames = data[-35:]
            print("base level: ", self.base_level)
            print("stDev: ", self.stDev)
            for i in range(len(max_frames)):
                print("db: ", max_frames[i])
                if max_frames[i] < self.base_level * 0.8:
                    silence_count += 1
                    
                    print("silence count: ", silence_count)
                    

            if silence_count > 35 * 0.9:
                speaking = False

        print("Speaking:", speaking)
        return speaking



if __name__ == "__main__":
    exit_gracefully = False
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")

    args = parser.parse_args()
    try:
        # Initialize qi framework.
        connection_url = "tcp://" + args.ip + ":" + str(args.port)
        app = qi.Application(["SoundProcessingModule", "--qi-url=" + connection_url])
        app.start()
        session = app.session
        ALMemory = session.service("ALMemory")
        # We need this broker to be able to construct NAOqi modules and subscribe to other modules.
        # The broker must stay alive until the program exists.
        myBroker = ALBroker("myBroker",
            "0.0.0.0",   # listen to anyone
            0,           # find a free port and use it
            args.ip,    # parent broker IP
            args.port)  # parent broker port
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + os.environ['ROBOT_IP'].lower().strip() + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    SoundProcessingModule = SoundProcessingModuleClass("SoundProcessingModule")
    

    serverSocket = socket.socket()
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    serverSocket.bind(("0.0.0.0", 9558))
    serverSocket.listen(5)

    while not exit_gracefully:
        try:
            clientConnection, clientAddress = serverSocket.accept() # Execution will stop here until something is received.
            data_received = False
            while not exit_gracefully and not data_received:
                data, binary_mode = recv_msg(clientConnection)
                data_received = True                    
                reply = None
                function_name = None
                
                if binary_mode == 0: # JSON command
                    function_name = data['function']
                    parameters = data['parameters']
                elif binary_mode == 1: # Connection ckeck
                    pass
                elif binary_mode == 2:
                    function_name = "binarytestA" 
                    parameters = [data]
                elif binary_mode == 3:
                    function_name = "binarytestB" 
                    parameters = [data]
                elif binary_mode == 10:
                    function_name = "receiveFile" 
                    parameters = [data]
                else:
                    print("Message received with unknown binary mode.")

                if function_name:
                    try:
                        reply = getattr(SoundProcessingModule, function_name)(*parameters)
                    except AttributeError as e:
                        traceback.print_exc()
                        print("ERROR: function " + function_name + " not found")
                    #mutexSocket.acquire()
                    send_msg(clientConnection, reply)
                    #mutexSocket.release()
        except IOError as e:
            if e.errno != errno.EINTR:
                print(e)
            #else:
            #    print(exception=e)
        except Exception as e:
            print(e)


    serverSocket.close()
