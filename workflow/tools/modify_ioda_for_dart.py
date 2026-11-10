#!/usr/bin/env python
"""
Modify IODA netCDF files so they can be used in DART

Obs errors come from a GSI-style errtable.rrfs file

Shawn Murdzek with assistance from Google Gemini Pro 3.1
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
import copy


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

    parser.add_argument('--moisture_var', 
                        dest='moisture_var', 
                        default='specificHumidity',
                        choices=['specificHumidity', 'relativeHumidity', 'dewpointTemperature'],
                        help='Moisture variable to output (specificHumidity, relativeHumidity, or \
                              dewpointTemperature)', 
                        type=str)

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


def dewpt_error_from_rh_and_temp(tmpk, rh_in, t_error, rh_error):
    """
    Computes estimated uncertainty in a dewpoint observation based on temperature 
    and relative humidity observations (using finite differencing).

    Source: DART/observations/obs_converters/obs_error/dewpoint_obs_err_mod.f90
    Based on Lin and Hubbard (2004, JAMC)

    Parameters
    ----------
    tmpk : float or array
        Temperature (K)
    rh_in : float or array
        Relative humidity (decimal)
    rh_error : float or array
        Relative humidity error (decimal)
    t_error : float or array, optional
        Temperature error (K)

    Returns
    -------
    dewpt_error : float or array
        Dewpoint temperature error (K)

    """

    rh_min = 0.20
    rh_max = 1.00
    delta_rh = 0.01
    delta_t = 0.1

    # Set min RH to 20% b/c dewpoint uncertainty becomes unbounded as RH approaches 0
    rh = np.maximum(rh_in, rh_min)

    # Finite-difference approximations
    rh1 = np.maximum(rh - delta_rh, rh_min)
    rh2 = np.minimum(rh + delta_rh, rh_max)
    t1 = tmpk - delta_t
    t2 = tmpk + delta_t

    # MetPy expects dimensionless RH (0 to 1) and Temp in Kelvin
    td2_rh = mc.dewpoint_from_relative_humidity(tmpk * units.K, rh2).to('kelvin').magnitude
    td1_rh = mc.dewpoint_from_relative_humidity(tmpk * units.K, rh1).to('kelvin').magnitude
    td_deriv_rh = (td2_rh - td1_rh) / (rh2 - rh1)

    td2_t = mc.dewpoint_from_relative_humidity(t2 * units.K, rh).to('kelvin').magnitude
    td1_t = mc.dewpoint_from_relative_humidity(t1 * units.K, rh).to('kelvin').magnitude
    td_deriv_t = (td2_t - td1_t) / (t2 - t1)

    dewpt_error = np.sqrt((td_deriv_t**2 * t_error**2) + (td_deriv_rh**2 * rh_error**2))
    
    return dewpt_error


def modify_ioda(ioda, err_dict, moisture_var):
    """
    Modify an IODA xarray DataSet so that it includes obs errors and converts moisture
    """

    # Mapping between IODA variables and errtable columns
    ioda2err = {'airTemperature': 'Terr',
                'virtualTemperature': 'Terr',
                'airTemperatureAt2M': 'Terr',
                'sensibleTemperature': 'Terr',
                'specificHumidity': 'RHerr',
                'specificHumidityAt2M': 'RHerr',
                'stationPressure': 'PSerr',
                'windEastward': 'UVerr',
                'windNorthward': 'UVerr'}

    vars_to_process = list(ioda['ObsValue'].data_vars)
    for v in vars_to_process:
        if v not in ioda2err:
            print(f"WARNING: IODA variable {v} not supported. Skipping")
            continue

        obs_types = ioda['ObsType'][v].values
        unique_types = np.unique(obs_types[~np.isnan(obs_types)])

        for t in unique_types:
            cond = obs_types == t
            all_prs = ioda['MetaData']['pressure'].values[cond]

            # Interpolate obs errors based on pressure
            # Note: Pressure values MUST be increasing for np.interp
            ioda['ObsError'][v].values[cond] = np.interp(all_prs,
                                                         err_dict[t]['prs'][::-1],
                                                         err_dict[t][ioda2err[v]][::-1])

        # Moisture variable unit/error conversions
        # Assume that we are given specificHumidity by IODA file (reasonable assumption if derived 
        # from prepBUFR)
        if v in ['specificHumidity', 'specificHumidityAt2M']:

            # Determine corresponding temperature field and moisture field
            if v == 'specificHumidity':
                T_field = 'airTemperature'
                mois_field = f"{moisture_var}"
            elif v == 'specificHumidityAt2M':
                T_field = 'airTemperatureAt2M'
                mois_field = f"{moisture_var}At2M"

            # Copy over specific humidity to new moisture variable
            if moisture_var != 'specificHumidity':
                for group in ['ObsError', 'ObsType', 'ObsValue', 'QualityMarker']:
                    ioda[group][mois_field] = copy.deepcopy(ioda['ObsValue'][v])

            # Compute errors for qv
            qs = compute_qs(ioda['ObsValue'][T_field].values,
                            ioda['MetaData']['pressure'].values)
            ioda['ObsError'][v].values = ioda['ObsError'][v].values * qs

            # Convert to proper units
            # At this point for mois_field, ObsError is for RH and ObsValue is for qv
            if moisture_var == 'relativeHumidity':
                ioda['ObsValue'][mois_field].values = ioda['ObsValue'][mois_field].values / qs
                for group in ['ObsValue', 'ObsError']:
                    ioda[group][mois_field].attrs = {'long_name' : 'Relative Humidity', 'units': 'decimal'}

            elif moisture_var == 'dewpointTemperature':
                rh = ioda['ObsValue'][mois_field].values / qs
                T = ioda['ObsValue'][T_field].values
                rh_error = ioda['ObsError'][mois_field].values
                T_error = ioda['ObsError'][T_field]
                ioda['ObsValue'][mois_field].values = mc.dewpoint_from_relative_humidity(T * units.K, rh).to('kelvin').magnitude
                ioda['ObsError'][mois_field].values = dewpt_error_from_rh_and_temp(T, rh, T_error, rh_error)
                for group in ['ObsValue', 'ObsError']:
                    ioda[group][mois_field].attrs = {'long_name' : 'Dewpoint Temperature', 'units': 'K'}

    return ioda


if __name__ == '__main__':

    start = dt.datetime.now()
    pgm_name = 'modify_ioda_for_dart.py'
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
    ioda_tree = modify_ioda(ioda_tree, obs_errors, param.moisture_var)

    # Write modified IODA file
    if param.verbose == 1:
        print('Writing output...')
    ioda_tree.to_netcdf(param.out_fname)

    print(f"\nFinished {pgm_name}")
    print(f"Elapsed time = {(dt.datetime.now() - start).total_seconds()} s\n")


"""
End modify_ioda_for_dart.py
"""
