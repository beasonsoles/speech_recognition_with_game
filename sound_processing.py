#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

"""Example: Get Signal from Front Microphone & Calculate its rms Power"""


import qi
import argparse
import sys
import time
import numpy as np

from naoqi import ALModule
from naoqi import ALBroker


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
        self.module_name = "SoundProcessingModule"

    def startProcessing(self):
        """
        Start processing
        """
        # ask for the front microphone signal sampled at 16kHz
        # if you want the 4 channels call setClientPreferences(self.module_name, 48000, 0, 0)
        print "AUDIO SERVICE:", self.audio_service
        self.audio_service.setClientPreferences(self.module_name, 16000, 3, 0)
        self.audio_service.subscribe(self.module_name)

        while self.isProcessingDone == False:
            time.sleep(1)

        self.audio_service.unsubscribe(self.module_name)

    def processRemote(self, nbOfChannels, nbOfSamplesByChannel, timeStamp, inputBuffer):
        """
        Compute RMS from mic.
        """
        self.framesCount = self.framesCount + 1

        if (self.framesCount <= self.nbOfFramesToProcess):
            # convert inputBuffer to signed integer as it is interpreted as a string by python
            self.micFront=self.convertStr2SignedInt(inputBuffer)
            #compute the rms level on front mic
            rmsMicFront = self.calcRMSLevel(self.micFront)
            print str(rmsMicFront)
        else :
            self.isProcessingDone=True

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


if __name__ == "__main__":
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
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    SoundProcessingModule = SoundProcessingModuleClass("SoundProcessingModule")
    SoundProcessingModule.startProcessing()
