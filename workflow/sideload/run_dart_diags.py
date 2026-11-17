#!/usr/bin/env python
"""
Plot observation-space diagnostics for DART experiments using pyDARTdiags and obs_seq.final

shawn.s.murdzek@noaa.gov
"""

# ---------------------------------------------------------------------------------------------------
# Import Modules
# ---------------------------------------------------------------------------------------------------

import datetime as dt
import numpy as np

import matplotlib
matplotlib.use('Agg')  # Prevents plots from popping up owing to plt.show() in pyDARTdiag.matplots functions
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap

import cartopy.crs as ccrs
import cartopy.feature as cfeature

from pydartdiags.matplots import matplots as mp  # noqa: E402
import pydartdiags.obs_sequence.obs_sequence as obsq  # noqa: E402


# ---------------------------------------------------------------------------------------------------
# Program
# ---------------------------------------------------------------------------------------------------

def plot_vprofs(obs):
    """
    Plot vertical profiles of RMSE, bias, and total spread

    Adapted from: https://github.com/NCAR/pyDARTdiags/blob/main/examples/03_diagnostics/plot_profiles.py
    """

    # Determine all observation types
    all_types = obs.df['type'].unique()

    # Make a separate plot for each type
    # p_lvls is in Pa, sfc_lvls is in m ASL
    p_lvls = np.arange(0, 100001, 5000)
    sfc_lvls = list(range(0, 401, 100)) + list(range(600, 1001, 200)) + list(range(1500, 5001, 500))
    for t in all_types:

        # Determine vertical coordinate
        vcoord = obs.df.loc[obs.df['type'] == t, 'vert_unit'].values[0]

        # Make plots
        if vcoord == 'pressure (Pa)':
            fig = mp.plot_profile(obs, p_lvls, t, bias=True, rmse=True, totalspread=True)  # noqa: F841
        elif vcoord == 'surface (m)':
            fig = mp.plot_profile(obs, sfc_lvls, t, bias=True, rmse=True, totalspread=True)  # noqa: F841
        else:
            print(f"WARNING: Unknown vcoord in plot_vprofs: {vcoord}")

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
        fig = mp.plot_rank_histogram(obs, t, ens_size)  # noqa: F841
        plt.savefig(f"rank_hist_{t}.png", dpi=200)

    return None


def plot_spatial_dist_qc(obs):
    """
    Plot spatial distribution of obs color-coded by QC flag

    Inspiration: https://ncar.github.io/pyDARTdiags/examples/02_visualizing/plot_qc_hover.html
    Use CartoPy instead of plotly to make it easier to save static files
    """

    # Determine all observation types
    all_types = obs.df['type'].unique()

    # Make a separate plot for each type
    for t in all_types:
        df = obs_seq.df.loc[obs_seq.df['type'] == t, :]

        # Create figure using Lambert Conformal map projection
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.LambertConformal())

        # Add basemap
        ax.set_extent([-125.0, -66.5, 22.0, 52.0], crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.8)
        ax.add_feature(cfeature.STATES, linewidth=0.3, edgecolor='gray')

        # Define a discrete colormap with 9 bins
        #discrete_cmap = plt.get_cmap('plasma', 9)
        tab10 = plt.get_cmap('tab10')
        discrete_cmap = ListedColormap(tab10.colors[:9])

        # Plot data
        cax = ax.scatter(df['longitude'], 
                         df['latitude'], 
                         c=df['DART_quality_control'],
                         s=6,
                         vmin=-0.5,
                         vmax=8.5,
                         cmap=discrete_cmap,
                         transform=ccrs.PlateCarree())

        # Add colorbar
        cbar = plt.colorbar(cax, ax=ax, orientation='horizontal', pad=0.05, ticks=range(9))
        cbar.set_label('DART QC flag', size=12)

        # Add title
        ax.set_title(f"DART QC flags for {t}", size=16)

        plt.tight_layout()
        plt.savefig(f"spatial_dist_QC_{t}.png", dpi=200)
        plt.close(fig)

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
    #plot_vprofs(obs_seq)

    # Make ranked histogram plots
    #plot_rank_hist(obs_seq)

    # Make spatial distribution of QC flags plots
    plot_spatial_dist_qc(obs_seq)

    print(f"\nFinished {pgm_name}")
    print(f"Elapsed time = {(dt.datetime.now() - start).total_seconds()} s\n")

"""
End run_dart_diags.py
"""
