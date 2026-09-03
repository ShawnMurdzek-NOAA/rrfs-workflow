#!/usr/bin/env python
"""
Modify IODA obs errors so they can be used in DART

Obs errors come from a GSI-style errtable.rrfs file

shawn.s.murdzek@noaa.gov
"""

# ---------------------------------------------------------------------------------------------------
# Import Modules
# ---------------------------------------------------------------------------------------------------

import datetime as dt
import sys
import argparse
import numpy as np
import xarray as xr
import pandas as pd
import metpy.calc as mc
from metpy.units import units


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

    parser = argparse.ArgumentParser(description='Script that adds obs errors to an IODA netCDF \
                                                  file.')

    # Positional arguments
    parser.add_argument('ioda_file',
                        help='IODA netCDF file name',
                        type=str)

    parser.add_argument('err_file',
                        help='GSI-style errtable file name',
                        type=str)

    # Optional arguments
    parser.add_argument('--out_fname',
                        dest='out_fname',
                        default='out.nc',
                        help='Output IODA netCDF file name',
                        type=str)

    parser.add_argument('--verbose',
                        dest='verbose',
                        default=0,
                        help='Option to print extra output (0 = off, 1 = on)',
                        type=int)

    return parser.parse_args(argv)


def read_errtable(fname):
    """
    Parse out observation errors from an errtable file in GSI

    Parameters
    ----------
    fname : string
        Name of errtable text file

    Returns
    -------
    errors : dictionary
        A dictionary of pd.DataFrame objects containing the observation errors

    Notes
    -----
    More information about the errtable format in GSI can be found here:
    https://dtcenter.ucar.edu/com-GSI/users/docs/users_guide/html_v3.7/gsi_ch4.html#conventional-observation-errors

    """

    # Extract contents of file
    fptr = open(fname, 'r')
    contents = fptr.readlines()
    fptr.close()

    # Loop over each line
    errors = {}
    headers = ['prs', 'Terr', 'RHerr', 'UVerr', 'PSerr', 'PWerr']
    for line in contents:
        if line[5:21] == 'OBSERVATION TYPE':
            key = int(line[1:4])
            errors[key] = {}
            for h in headers:
                errors[key][h] = []
        else:
            vals = line.strip().split(' ')
            for k, h in enumerate(headers):
                errors[key][h].append(float(vals[k]))

    # Convert to DataFrame
    # Also perform unit conversions to match IODA format
    for key in errors.keys():
        errors[key] = pd.DataFrame(errors[key])
        for h in headers[1:]:
            errors[key].loc[errors[key][h] > 5e8, h] = np.nan

        # Unit conversions
        # Convert pressure from hPa > Pa
        errors[key]['prs'] = errors[key]['prs'] * 100
        errors[key]['PSerr'] = errors[key]['PSerr'] * 100

        # Convert RHerr from percent / 10 > decimal
        errors[key]['RHerr'] = errors[key]['RHerr'] * 0.1

    return errors


def compute_qs(T, p):
    """
    Compute saturation specific humidity

    Parameters
    ----------
    T : float or array
        Temperature (K)
    p : float or array
        Pressure (Pa)

    Returns
    -------
    Saturation specific humidity (unitless)

    """

    sat_mix_ratio = mc.saturation_mixing_ratio(p * units.Pa, T * units.K)
    qs = mc.specific_humidity_from_mixing_ratio(sat_mix_ratio).magnitude

    return qs


def modify_ioda(ioda, err_dict):
    """
    Modify an IODA xarray DataSet so that it includes obs errors
    """

    # Mapping between IODA variables and errtable columns
    ioda2err = {'airTemperature': 'Terr',
                'virtualTemperature': 'Terr',
                'sensibleTemperature': 'Terr',
                'specificHumidity': 'RHerr',
                'stationPressure': 'PSerr',
                'windEastward': 'UVerr',
                'windNorthward': 'UVerr'}

    ioda_vars = list(ioda['ObsValue'].data_vars)
    for v in ioda_vars:

        if v not in ioda2err:
            print(f"WARNING: IODA variable {v} not supported. Skipping")
            continue

        obs_types = ioda['ObsType'][v].values
        unique_types = np.unique(obs_types[~np.isnan(obs_types)])

        for t in unique_types:
            cond = obs_types == t
            all_prs = ioda['MetaData']['pressure'].values[cond]

            # Interpolate obs errors based on pressure
            ioda['ObsError'][v].values[cond] = np.interp(all_prs,
                                                         obs_errors[t]['prs'],
                                                         obs_errors[t][ioda2err[v]])

        # Put specificHumidity obs errors in proper units
        if v == 'specificHumidity':
            qs = compute_qs(ioda['ObsValue']['airTemperature'].values,
                            ioda['MetaData']['pressure'].values)
            ioda['ObsError'][v].values = ioda['ObsError'][v].values * qs

    return ioda


if __name__ == '__main__':

    start = dt.datetime.now()
    pgm_name = 'modify_ioda_obs_err_for_dart.py'
    print(f"\nStarting {pgm_name}")
    print(f"Time = {start.strftime('%Y%m%d %H:%M:%S')}\n")

    # Read in input files
    param = parse_in_args(sys.argv[1:])
    if param.verbose == 1:
        print('Reading inputs...')
    obs_errors = read_errtable(param.err_file)
    ioda_tree = xr.open_datatree(param.ioda_file)

    # Modify IODA file
    if param.verbose == 1:
        print('Modifying IODA files...')
    ioda_tree = modify_ioda(ioda_tree, obs_errors)

    # Write modified IODA file
    if param.verbose == 1:
        print('Writing output...')
    ioda_tree.to_netcdf(param.out_fname)

    print(f"\nFinished {pgm_name}")
    print(f"Elapsed time = {(dt.datetime.now() - start).total_seconds()} s\n")


"""
End modify_ioda_obs_err_for_dart.py
"""
