import os
import time

def count_clips():

    # Get current working directory
    cur_path = os.getcwd()

    # Get list of all file in AudioClips directory
    dirListing = os.listdir(cur_path + "/AudioClips") 

    # Count number audio clips in file
    numClips = len([file for file in dirListing if "AudioClip" in file])

    return numClips

def main():
    while (True):
        print (count_clips())
        time.sleep(1)


if __name__ == "__main__":
    main()
    