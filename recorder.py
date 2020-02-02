from array import array
from sys import byteorder
from struct import pack

import numpy as np
import time
import pyaudio
import wave

########################### STREAM PARAMETERS ##########################
chunk = 1024                      # Record in chunks of 1024 samples   #
sample_format = pyaudio.paInt16   # 16 bits per sample                 #
channels = 1                      # Microphone has 2 channels          #
fs = 44100                        # Record at 44100 samples per second #
threshold = 30000                  # Begins recording if surpassed      #
########################################################################

# Colours class from Blender Build Scripts
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def listen(filename):

    # Begin listening on the microphone
    p = pyaudio.PyAudio()
    stream = p.open(format = sample_format,
                channels = channels,
                rate = fs,
                frames_per_buffer = chunk,
                input = True,
                output = True)
    
    audio_chunk = array('h', stream.read(chunk))
    
    print (bcolors.OKGREEN + "LISTENING" + bcolors.ENDC)
    while silence(audio_chunk):
        audio_chunk = array('h', stream.read(chunk))
    
    
    ticker = 0
    clip = array('h')
    print (bcolors.FAIL + "RECORDING" + bcolors.ENDC)

    # Begin recording the data until a significant pause occurs
    while True: 

        wavelength = max(audio_chunk)/500   # Outputs some naff
        print (np.ones(int(wavelength)))    # wavelengths to terminal

        audio_chunk = array('h', stream.read(chunk))
        if byteorder == 'big':
            audio_chunk.byteswap()

        if silence(audio_chunk):
            ticker += 1
        if not silence(audio_chunk):
            ticker = 0
        if ticker > 50:
            break
        clip.extend(audio_chunk)

    # Stop and close the stream 
    stream.stop_stream()
    stream.close()

    # Terminate the PortAudio interface
    p.terminate()

    data = pack('<' + ('h'*len(clip)), *clip)

    # Save the recorded data as a WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(data)
    wf.close()
    print (bcolors.HEADER + "Saved new clip: " + filename + bcolors.ENDC)

def silence(audio_chunk):        
    return max(audio_chunk) < threshold

def main():

    clipNO = 0
    date = time.strftime("%d-%m-%Y", time.localtime())
    # Keep the program running until user force quits it
    while True:
        filename = "AudioClips/AudioClip" + str(clipNO) + "(" + date + ").wav"
        listen(filename)
        clipNO += 1

if __name__ == "__main__":
    main()
    