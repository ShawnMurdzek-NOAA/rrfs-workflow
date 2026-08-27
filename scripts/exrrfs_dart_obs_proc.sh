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
# Add obs errors to IODA files and convert to obs_seq files
#
#-----------------------------------------------------------------------
#

# Obs errors to add to IODA files
ln -snf "${FIXrrfs}/dart/errtable.rrfs" .

# Copy over DART IODA to obs_seq converter
cp -r ${HOMErrfs}/workflow/sideload/aux_dart/DART/pytools/pyjedi/src/pyjedi .

# Loop over all obs
for ob in ${all_obs[@]}; do
  ioda_name="ioda_${ob}.nc"
  full_path="${COMOUT}/ioda_bufr/${WGF}/${ioda_name}"
  if [[ -s ${full_path} ]]; then
    ln -snf "${full_path}" "${ioda_name}"
    
    # File names
    ioda_err="${ob}_with_err.nc"
    obs_seq_out="${ob}_ob_seq.out"
    pyjedi_yaml="${ob}.yml"
    ln -snf "${FIXrrfs}/dart/${pyjedi_yaml}" .

    # Add obs errors to IODA file
    python ${HOMErrfs}/workflow/tools/modify_ioda_obs_err_for_dart.py ${ioda_name} errtable.rrfs --out_fname ${ioda_err}

    # Convert to obs_seq file
    python -m pyjedi.ioda2obsq ${pyjedi_yaml} ${ioda_err} ${obs_seq_out}

  else
    echo "WARNING: The following IODA file is NOT available"
    echo ${full_path}
  fi
done

#
#-----------------------------------------------------------------------
#
# Combine obs_seq files into a single file
#
#-----------------------------------------------------------------------
#

obs_seq_names=( *ob_seq.out )
n_files=${#obs_seq_names[@]}
if [[ ${n_files} == 0 ]]; then
  echo "ERROR: No DART obs_seq files created"
  exit 1
elif [[ ${n_files} == 1 ]]; then
  cp ${obs_seq_names[@]} obs_seq.out
else
  echo "ERROR: Cannot handle multiple DART obs_seq files yet"
  echo "Choose a single observation type in all_obs and try again"
  exit 1
fi

# Save final obs_seq file
${cpreq} obs_seq.out "${COMOUT}/dart_obs_proc/${WGF}/obs_seq.out"

exit 0
