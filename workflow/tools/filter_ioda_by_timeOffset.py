#!/usr/bin/env python
"""
Filter IODA netCDF file so it only contains observations with certain timeOffset values

shawn.s.murdzek@noaa.gov
"""

# ---------------------------------------------------------------------------------------------------
# Import Modules
# ---------------------------------------------------------------------------------------------------

import datetime as dt
import sys
import argparse
import xarray as xr


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
    parser = argparse.ArgumentParser(description='Script that filters obs in an IODA netCDF \
                                                  based on timeOffset.')

    # Positional arguments
    parser.add_argument('ioda_file',
                        help='IODA netCDF file name',
                        type=str)

    # Optional arguments
    parser.add_argument('--out_fname',
                        dest='out_fname',
                        default='out.nc',
                        help='Output IODA netCDF file name',
                        type=str)

    parser.add_argument('--min',
                        dest='min_timeOffset',
                        default=-1800.,
                        help='Minimum timeOffset value',
                        type=float)

    parser.add_argument('--max',
                        dest='max_timeOffset',
                        default=1800.,
                        help='Maximum timeOffset value',
                        type=float)

    parser.add_argument('--verbose',
                        dest='verbose',
                        default=0,
                        help='Option to print extra output (0 = off, 1 = on)',
                        type=int)

    return parser.parse_args(argv)


def filter_ioda_by_timeOffset(dt, min_offset, max_offset):
    """
    Filter DataSet by min/max timeOffset values
    """

    mask = (dt['/MetaData']['timeOffset'] > min_offset) & (dt['/MetaData']['timeOffset'] < max_offset)

    return dt.map_over_datasets(lambda ds: ds.where(mask, drop=True))


if __name__ == '__main__':

    start = dt.datetime.now()
    pgm_name = 'filter_ioda_by_timeOffset.py'
    print(f"\nStarting {pgm_name}")
    print(f"Time = {start.strftime('%Y%m%d %H:%M:%S')}\n")

    # Read in input files
    param = parse_in_args(sys.argv[1:])
    if param.verbose == 1:
        print('Reading inputs...')
    ioda_tree = xr.open_datatree(param.ioda_file)

    # Modify IODA file
    if param.verbose == 1:
        print('Filtering IODA files...')
    ioda_tree = filter_ioda_by_timeOffset(ioda_tree, param.min_timeOffset, param.max_timeOffset)

    # Write modified IODA file
    if param.verbose == 1:
        print('Writing output...')
    ioda_tree.to_netcdf(param.out_fname)

    print(f"\nFinished {pgm_name}")
    print(f"Elapsed time = {(dt.datetime.now() - start).total_seconds()} s\n")


"""
End filter_ioda_by_timeOffset.py
"""
