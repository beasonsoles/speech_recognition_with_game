#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

"""Example: Get Signal from Front Microphone & Calculate its rms Power"""


import qi
import argparse
import sys
import numpy as np
import os

class SoundProcessingModule(object):
    """
    A simple get signal from the front microphone of Nao & calculate its rms power.
    It requires numpy.
    """

    def __init__( self, app):
        """
        Initialise services and variables.
        """
        super(SoundProcessingModule, self).__init__()
        app.start()
        session = app.session

        # Get the service ALAudioDevice.
        self.audio_service = session.service("ALAudioDevice")
        #self.isProcessingDone = False
        #self.nbOfFramesToProcess = 20
        #self.framesCount=0
        self.micFront = []
        self.audio_rms = []
        self.timeout = 3
        self.speaking = False
        self.threshold = 35
        self.module_name = "SoundProcessingModule"

    def startProcessing(self):
        """
        Start processing
        """
        # ask for the front microphone signal sampled at 16kHz
        # if you want the 4 channels call setClientPreferences(self.module_name, 48000, 0, 0)
        self.audio_service.setClientPreferences(self.module_name, 16000, 3, 0)
        self.audio_service.subscribe(self.module_name)

        self.threshold = self.detectBaseLevel(self.audio_rms)
        while self.speaking == False:
            self.speaking = self.detectVoice(self.audio_rms, self.threshold)
        while self.speaking == True:
            self.speaking = self.detectSilence(self.audio_rms, self.threshold)

        self.audio_service.unsubscribe(self.module_name)

    def processRemote(self, nbOfChannels, nbOfSamplesByChannel, timeStamp, inputBuffer):
        """
        Compute RMS from mic.
        """

        # convert inputBuffer to signed integer as it is interpreted as a string by python
        self.micFront=self.convertStr2SignedInt(inputBuffer)
        #compute the rms level on front mic
        rmsMicFront = self.calcRMSLevel(self.micFront)
        self.audio_rms.append(rmsMicFront)
        print(str(rmsMicFront))

    def calcRMSLevel(self,data) :
        """
        Calculate RMS level
        """
        rms = 20 * np.log10( np.sqrt( np.sum( np.power(data,2) / len(data)  )))
        return rms

    def convertStr2SignedInt(self, data) :
        """
        This function takes a string containing 16 bits little endian sound
        samples as input and returns a vector containing the 16 bits sound
        samples values converted between -1 and 1.
        """
        signedData=[]
        ind=0
        for i in range (0,len(data)/2) :
            signedData.append(data[ind]+data[ind+1]*256)
            ind=ind+2

        for i in range (0,len(signedData)) :
            if signedData[i]>=32768 :
                signedData[i]=signedData[i]-65536

        for i in range (0,len(signedData)) :
            signedData[i]=signedData[i]/32768.0

        return signedData
    
    def detectBaseLevel(self, data): 
        """
        Detect initial volume level in data
        """
        threshold = np.mean(data[:5])

        print("Base level: ", threshold)
        return threshold
    
    def detectVoice(self, data, threshold): 
        """
        Detect voice in data
        """
        speaking = False
        for i in range(len(data)):
            if data[i] > threshold:
                # check if patient has started speaking
                speaking = True
                print("Voice detected")
        
        return speaking

    def detectSilence(self, data, threshold): 
        """
        Detect silence in data
        """
        time_per_period = 1024 / 16000 # TODO: PERIOD SIZE???
        max_silence_periods = int(self.timeout / time_per_period) # max number of periods of continuous silence
        silence_count = 0
        silence = True

        for i in range(len(data)):
            if data[i] > threshold:
                # patient is speaking
                silence_count = 0
            else:
                print("Silence detected")
                # patient is silent
                silence_count += 1
                if silence_count >= max_silence_periods:
                    # patient has not spoken for more than 3 seconds
                    print("Timeout reached")
                    silence = True
                else: 
                    silence = False

        return silence


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")

    args = parser.parse_args()
    try:
        # Initialize qi framework.
        connection_url = "tcp://" + os.environ['ROBOT_IP'].lower().strip() + ":" + str(args.port)
        app = qi.Application(["SoundProcessingModule", "--qi-url=" + connection_url])
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    MySoundProcessingModule = SoundProcessingModule(app)
    app.session.registerService("SoundProcessingModule", MySoundProcessingModule)
    MySoundProcessingModule.startProcessing()
