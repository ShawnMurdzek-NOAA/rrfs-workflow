#!/usr/bin/env python3
"""
Filter near-surface observations (e.g., ADPSFC) so that only the observations closest to the analysis time are retained

Google Gemini Pro 3.1, reviewed and edited by Shawn Murdzek
"""

import argparse
import xarray as xr
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser(
        description="Filter JEDI IODA netCDF to retain one observation per station and report type with the smallest absolute timeOffset (negative ties preferred)."
    )
    parser.add_argument("-i", "--input", required=True, help="Input IODA netCDF file path")
    parser.add_argument("-o", "--output", required=True, help="Output IODA netCDF file path")
    parser.add_argument("--filter-qc", action="store_true", 
                        help="Drop observations before selection if QualityMarker >= 4 for all variables in specific clusters.")
    args = parser.parse_args()

    # Load the file as a DataTree to support newer IODA group structures.
    # decode_cf=False prevents xarray from altering JEDI-specific missing values/scale factors.
    dt = xr.open_datatree(args.input, decode_cf=False)

    # Extract variables from the MetaData group
    try:
        station_node = dt['MetaData']['stationIdentification']
        report_type_node = dt['MetaData']['prepbufrReportType']
        time_node = dt['MetaData']['timeOffset']
    except KeyError as e:
        raise KeyError(f"Missing expected variable in 'MetaData' group: {e}. Verify IODA file version.")

    # Identify the location dimension name (typically 'nlocs')
    nlocs_dim = time_node.dims[0]
    initial_obs = time_node.sizes[nlocs_dim]

    # Load into a pandas DataFrame. The DataFrame index inherently tracks the original nlocs indices.
    df = pd.DataFrame({
        'station': station_node.values.astype(str),
        'report_type': report_type_node.values.astype(str),
        'timeOffset': time_node.values
    })

    # Optional QC filtering step
    if args.filter_qc:
        try:
            qm = dt['QualityMarker']
            
            def is_bad_qc(var_name):
                if var_name not in qm:
                    # If the variable doesn't exist, we can't definitively say it has bad QC
                    return np.zeros(initial_obs, dtype=bool)
                
                # Cast to float safely handles potential NaNs even if the native type is int
                vals = qm[var_name].values.astype(float)
                return (vals >= 4.0) & (~np.isnan(vals))

            # Cluster 1 (thermodynamic variables): Must ALL be >= 4 and not NaN
            c1_bad = (is_bad_qc('airTemperatureAt2M') & 
                      is_bad_qc('specificHumidityAt2M'))
            
            # Cluster 2 (kinematic variables): Must ALL be >= 4 and not NaN
            c2_bad = (is_bad_qc('windEastward') & 
                      is_bad_qc('windNorthward'))
            
            # An entry is dropped if either cluster is completely bad
            drop_mask = c1_bad | c2_bad
            
            # Filter the dataframe (keeps original indices intact for dt.isel later)
            df = df[~drop_mask]
            
        except KeyError:
            print("Warning: 'QualityMarker' group not found in dataset. Skipping QC filter.")

    # Calculate the absolute time offset
    df['abs_timeOffset'] = df['timeOffset'].abs()

    # Sort the DataFrame. 
    # Sorting by 'abs_timeOffset' ascending gets the smallest absolute differences first.
    # The secondary sort on 'timeOffset' ascending acts as the tie-breaker: 
    # between -10 and 10, -10 sorts first and wins.
    df_sorted = df.sort_values(by=['abs_timeOffset', 'timeOffset'])

    # Group by BOTH station and report type, then extract the original index of the first row
    keep_indices = df_sorted.groupby(['station', 'report_type']).head(1).index.values

    # Sort indices to maintain the original spatial/chronological order of the file
    keep_indices = np.sort(keep_indices)

    # Apply the index filter to the entire DataTree.
    # dt.isel() applies the slice across every variable in every group that shares the location dimension.
    dt_filtered = dt.isel({nlocs_dim: keep_indices})
    
    final_obs = dt_filtered['MetaData']['timeOffset'].sizes[nlocs_dim]

    # Write out the filtered IODA file with all nested groups perfectly preserved
    dt_filtered.to_netcdf(args.output, format='NETCDF4')

    # Print requested statistics
    print(f"Initial number of observations: {initial_obs}")
    print(f"Final number of observations:   {final_obs}")

if __name__ == "__main__":

    pgm = 'filter_sfc_obs_by_closest_timeOffset.py'
    print(f"\nStarting {pgm}")
    main()
    print(f"\nFinished {pgm}")


"""
End filter_sfc_obs_by_closest_timeOffset.py
"""
