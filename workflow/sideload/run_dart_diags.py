#!/usr/bin/env python
"""
Plot observation-space diagnostics for DART experiments using pyDARTdiags and obs_seq.final

shawn.s.murdzek@noaa.gov
"""

#---------------------------------------------------------------------------------------------------
# Import Modules
#---------------------------------------------------------------------------------------------------

import datetime as dt
import numpy as np

import matplotlib
matplotlib.use('Agg')  # to prevent plots from poppin up
import matplotlib.pyplot as plt

import pydartdiags.obs_sequence.obs_sequence as obsq
from pydartdiags.matplots import matplots as mp


#---------------------------------------------------------------------------------------------------
# Program
#---------------------------------------------------------------------------------------------------

def plot_vprofs(obs):
    """
    Plot vertical profiles of RMSE, bias, and total spread

    Adapted from: https://github.com/NCAR/pyDARTdiags/blob/main/examples/03_diagnostics/plot_profiles.py
    """

    # Determine all observation types
    all_types = obs.df['type'].unique()

    # Make a separate plot for each type
    # plvls is in Pa
    plvls = np.arange(0, 100001, 5000)
    for t in all_types:
        fig = mp.plot_profile(obs, plvls, t, bias=True, rmse=True, totalspread=True)
        plt.savefig(f"vprof_{t}.png", dpi=200)

    return None


def plot_rank_hist(obs):
    """
    Plot rank histograms

    Adapted from: https://github.com/NCAR/pyDARTdiags/blob/main/examples/03_diagnostics/plot_rank_histogram.py
    """

    # Determine all observation types
    all_types = obs.df['type'].unique()

    # Determine ensemble size
    all_col = list(obs.df.columns)
    prior = []
    for c in all_col:
        try:
            if c[:21] == 'prior_ensemble_member':
                prior.append(c)
        except IndexError:
            continue
    ens_size = len(prior)

    # Make a separate plot for each type
    for t in all_types:
        fig = mp.plot_rank_histogram(obs, t, ens_size)
        plt.savefig(f"rank_hist_{t}.png", dpi=200)

    return None


if __name__ == '__main__':

    start = dt.datetime.now()
    pgm_name = 'run_dart_diags.py'
    print(f"\nStarting {pgm_name}")
    print(f"Time = {start.strftime('%Y%m%d %H:%M:%S')}\n")

    # Read in obs_seq.final file
    obs_seq_name = 'obs_seq.final'
    obs_seq = obsq.ObsSequence(obs_seq_name)

    # Make vertical profile plots
    plot_vprofs(obs_seq)

    # Make ranked histogram plots
    plot_rank_hist(obs_seq)

    print(f"\nFinished {pgm_name}")
    print(f"Elapsed time = {(dt.datetime.now() - start).total_seconds()} s\n")

"""
End run_dart_diags.py
"""
