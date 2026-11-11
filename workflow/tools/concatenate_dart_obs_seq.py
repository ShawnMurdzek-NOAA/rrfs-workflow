#!/usr/bin/env python
"""
Concatenate DART obs_seq files

Shawn Murdzek
"""

# ---------------------------------------------------------------------------------------------------
# Import Modules
# ---------------------------------------------------------------------------------------------------

import datetime as dt
import sys
import argparse
import pydartdiags.obs_sequence.obs_sequence as obsq


# ---------------------------------------------------------------------------------------------------
# Main Program
# ---------------------------------------------------------------------------------------------------

def parse_in_args(argv):
    """
    Parse input arguments

    Parameters
    ----------
    argv : list
        Command-line arguments from sys.argv[1:]

    Returns
    -------
    Parsed input arguments

    """

    parser = argparse.ArgumentParser(description='Script that concatenates DART obs_seq files')

    # Positional arguments
    parser.add_argument('file_list',
                        help='Text file with a list of DART obs_seq files to concatenate',
                        type=str)

    # Optional arguments
    parser.add_argument('--out_fname',
                        dest='out_fname',
                        default='obs_seq_combined.out',
                        help='Output DART obs_seq file name',
                        type=str)

    return parser.parse_args(argv)


def read_obs_seq_files(in_fname):
    """
    Read in all obs_seq files
    """

    obs_seq_list = []
    with open(in_fname, 'r') as fptr:
        for l in fptr:
            obs_seq_list.append(obsq.ObsSequence(l.strip()))

    return obs_seq_list


if __name__ == '__main__':

    start = dt.datetime.now()
    pgm_name = 'concatenate_dart_obs_seq.py'
    print(f"\nStarting {pgm_name}")
    print(f"Time = {start.strftime('%Y%m%d %H:%M:%S')}\n")

    # Read in input files
    param = parse_in_args(sys.argv[1:])
    all_obs_seq = read_obs_seq_files(param.file_list)
    if len(all_obs_seq) == 0:
        raise ValueError(f"There are no obs_seq files in {param.file_list}")
    else:
        print(f"Concatenating together {len(all_obs_seq)} files")

    # Combine and write to a new obs_seq file
    obs_seq_comb = obsq.ObsSequence.join(all_obs_seq)
    obs_seq_comb.write_obs_seq(param.out_fname)

    print(f"\nFinished {pgm_name}")
    print(f"Elapsed time = {(dt.datetime.now() - start).total_seconds()} s\n")


"""
End concatenate_dart_obs_seq.py
"""
