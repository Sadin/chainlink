# Chainlink
#
# A script to automate concatenative synthesis
#
# Raymond Viviano
# January 31st, 2019
# rayvivianomusic@gmail.com

# Dependencies
from __future__ import print_function
import os, sys, getopt, traceback
import wave, sndhdr, wavio
import numpy as np 
import multiprocessing as mp
from os.path import isdir, isfile, abspath, join


# Function Definitions
def process_options():
    """
        Process command line arguments for file inputs, outputs, verbosity,
        chunk length, multiprocessing, and number of cores to use. Also provide 
        an option for help. Return input dirs, ouput dir, and verbosity level. 
        Print usage and exit if help requested.
    """

    # Define usage
    usage = """
    Usage: python chainlink.py --input1 <arg> --input2 <arg> --output <arg> 
                               --chunk_size <arg> [-v] [-m] [-c cores] [-h]

    Mandatory Options:

    --input1      Directory containing wav files to recreate with concatenative 
                  synthesis. Can contain other files, but this script will only
                  process the wavs within.

    --input2      Directory conatining the "chain links," or a bunch of wavs that
                  the script will use to recreate the wavs in 'input1'

    --output      Directory where you want the script to save output

    --chunk_size  Number between 10 and 1000. The chunk size in milleseconds, 
                  where a chunk is the segment of a sample from input1 that gets
                  replaced by a segment of the same size from a sample within 
                  the input2 directory

    Optional Options:

    -v            Turn verbosity on - increases text output the script generates

    -m            Turn multiprocessing on - leverages multicore systems

    -c            Number of cores to use, defaults to 2 if multiprocessing is 
                  specified but the user doesn't pass an argument to this option

    -h            Print this usage message and exit
    """

    # Set verbosity to false
    is_verbose = False

    # Set multiprocessing to false
    is_mp = False

    # Set number of cores to use for multiprocessing to 2 as a default
    cores = 2

    # Checks that mandatory options provided. This variable should equal 4 
    # before continuing execution of the script
    mandatory_checks = 0

    # Get commandline options and arguments
    options, _ = getopt.getopt(sys.argv[1:], "hvmc:", ["input1=", "input2=", 
                               "output=", "chunk_size="])

    for opt, arg in options:
        if opt == "--input1":
            if arg is not None:
                input_dir1 = arg
                mandatory_checks += 1
        if opt == "--input2": 
            if arg is not None:
                input_dir2 = arg 
                mandatory_checks += 1
        if opt == "--output":
            if arg is not None:
                output_dir = arg
                mandatory_checks += 1 
        if opt == "--chunk_size":
            if arg is not None:
                chunk_size = int(arg)
                mandatory_checks += 1
        if opt == "-v":
            is_verbose = True
        if opt == "-m":
            is_mp = True
        if opt == "-c":
            cores = arg
        if opt == "-h":
            print(usage)
            sys.exit(0)

    # Make sure that arguments existed for all mandatory options
    if mandatory_checks != 4:
        print(os.linesep + 'Errors detected with mandatory options')
        print(usage)
        sys.exit(1)

    # Verify usability of passed arguments
    check_options(input_dir1, input_dir2, output_dir, chunk_size, usage)

    # Return options for audio processing
    return input_dir1, input_dir2, output_dir, chunk_size, is_verbose, is_mp, cores


def check_options(input_dir1, input_dir2, output_dir, chunk_size, usage):
    """
        Make sure the supplied options are meaningful. Separate from the 
        process_options function to curb function length.
    """

    # Check all arguments before printing usage message
    is_invalid = False

    # Check that input directories exist
    if not isdir(input_dir1):
        print("Input directory 1 does not exist")
        is_invalid = True

    if not isdir(input_dir2):
        print("Input directory 2 does not exist")
        is_invalid = True

    # Check that there are indeed wav files in input dirs 1 and 2
    for f in os.listdir(input_dir1):
        hdr = sndhdr.what(join(input_dir1, f))
        if hdr is not None:
            if hdr[0] == 'wav':
                break
    else:
        print("No wavs in input directory 1")
        is_invalid = True

    for f in os.listdir(input_dir2):
        hdr = sndhdr.what(join(input_dir2, f))
        if hdr is not None:
            if hdr[0] == 'wav':
                break
    else:
        print("No wavs in input directory 2")
        is_invalid = True

    # Check if output directory exists. If it doesn't try to make the dir tree
    if not isdir(output_dir):
        try:
            os.makedirs(output_dir)
        except:
            traceback.print_exc(file=sys.stdout)
            is_invalid = True

    # Verify that chunk size is between 10 and 1000
    if isinstance(chunk_size, int):
        if (chunk_size < 10) or (chunk_size > 1000):
            print("Chunk size must be between 10 and 1000 (milliseconds)")
            is_invalid = True
    else:
        print("Chunk size must be an integer between 10 and 1000")
        is_invalid = True
            
    # If problem(s) with arguments, print usage and exit
    if is_invalid:
        print(usage)
        sys.exit(1)


def load_wav(wave_filepath):
    """ 
        Convenience function to load the wav file but also to get all the 
        additional data into other variables to use later

        Input: Filepath to wav 

        Output: Complete wave_read object and the named tuple with params
    """
    # Open wav_read object and extract useful parameter information
    wav = wave.open(wave_filepath, 'rb')
    params = wav.getparams()
    framerate = wav.getframerate()
    nframes = wav.getnframes()

    # Convert bytes object to numpy array. Relatively straightforward for
    # 16 bit and 32 bit audio, pain in the ass for 24 bit audio. This is why the
    # script is dependent on the wavio package  
    wav_np = wavio.read(wave_filepath)                                           


    return wav, params, framerate, nframes, wav_np


def write_wav():
    pass


def convert_ms_to_frames(chunk_size_ms, framerate):
    """ 
        Convert chunk size in milleconds to chunk size in number of frames
    
        Framerate is in hz (cycles per second), chunk_size is in ms

        So we need to multiply framerate by chunk_size_ms/1000 to get the
        chunk size in frames. Round down to nearest int.
    """
    return int(framerate * (chunk_size_ms / 1000.0))


def main():
    """
        TODO: Write this docstring
    """
    input_dir1, input_dir2, output_dir, chunk_size, is_verbose, is_mp, cores = process_options()

    for f in os.listdir(input_dir1):
        wv_hdr = sndhdr.what(join(input_dir1, f))
        if wv_hdr is not None:
            if wv_hdr[0] == 'wav':
                print('File is a wav, printing hdr')
                print(wv_hdr)
                wv, wv_params, wv_framerate, wv_nframes, wv_np = load_wav(join(input_dir1, f))
                print('Printing wav params')
                print(wv_params)
                print('chunk size in ms ', chunk_size)
                chunk_size_frms = convert_ms_to_frames(chunk_size, wv_framerate)
                print('chunk size in frames ', chunk_size_frms)
                # Sample width in bytes
                print('sample width in bytes')
                print(wv.getsampwidth())
                # # Pull all frames from wav into a bytes object, convert to np vector
                # wv_frames_byte = wv.readframes(wv_nframes)
                # print(type(wv_frames_byte))
                # # print(wv_frames_byte)
                print(wv_np.data)
                
            else:
                continue


if __name__ == "__main__":
    main()