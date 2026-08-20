#!/usr/bin/env bash
# shellcheck disable=SC1091,SC2154,SC2086,SC2068
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]: '
set -x

prefix=${EXTRN_MDL_SOURCE%_NCO} # remove the trailing '_NCO' if any
cpreq=${cpreq:-cpreq}
cd "${DATA}" || exit 1

#
#-----------------------------------------------------------------------
#
# Observation types to consider
#
#-----------------------------------------------------------------------
#

# Only support AIRCAR for now, may add other obs later
all_obs=( "aircar" )

#
#-----------------------------------------------------------------------
#
# Add obs errors to IODA files
#
#-----------------------------------------------------------------------
#

# Obs errors to add to IODA files
ln -snf "${FIXrrfs}/dart/errtable.rrfs" .

# Add obs errors
for ob in ${all_obs[@]}; do
  ioda_name="ioda_${ob}.nc"
  full_path="${COMOUT}/ioda_bufr/${WGF}/${ioda_name}"
  if [[ -s ${full_path} ]]; then
    ln -snf "${full_path}" "${ioda_name}"
    python ${HOMErrfs}/workflow/tools/modify_ioda_obs_err_for_dart.py ${ioda_name} errtable.rrfs --out_fname ${ob}_with_err.nc
  else
    echo "WARNING: The following IODA file is NOT available"
    echo ${full_path}
  fi
done

#
#-----------------------------------------------------------------------
#
# Convert to DART obs_seq files
#
#-----------------------------------------------------------------------
#

# To be added later

# Update later so this saves the final obs_seq files, not the intermediate IODA files
for ob in ${all_obs[@]}; do
  ${cpreq} ${ob}_with_err.nc "${COMOUT}/dart_obs_proc/${WGF}/${ob}_with_err.nc"
done

exit 0
