#!/usr/bin/env bash
# shellcheck disable=all
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]: '
set -x
date
#
export HOMErrfs=${HOMErrfs} #comes from the workflow at runtime
export FIXrrfs=${FIXrrfs:-${HOMErrfs}/fix}
#

# Create and enter working directory
workdir="${COMOUT}/dart_perfect_model_obs/${WGF}/"
mkdir -p ${workdir}
cd ${workdir}

# Link DART obs_seq.out
ln -snf "${COMOUT}/dart_obs_proc/${WGF}/obs_seq.out" .

# Link required MPAS files
hist_time=$( date -d "${CDATE::8} ${CDATE:8:2}" "+%Y-%m-%d_%H.%M.%S" )
prefix=${EXTRN_MDL_SOURCE%_NCO}
zeta_levels=${EXPDIR}/config/ZETA_LEVELS.txt
nlevel=$(wc -l < "${zeta_levels}")
ln -snf "${NRPATH}/history.${hist_time}.nc" "history.nc"
ln -snf "${FIXrrfs}/${MESH_NAME}/${MESH_NAME}.invariant.nc_L${nlevel}_${prefix}" ./invariant.nc

# Create mpas_template.nc file
${cpreq} "history.nc" mpas_template.nc
ncks -A invariant.nc mpas_template.nc

# Copy and update namelist
${cpreq} "${FIXrrfs}/dart/input.nml" .
sed -i "s={ASSIMILATION_PERIOD_SECONDS}=$(( 2*DART_DA_HALF_WINDOW ))=" input.nml

# Run perfect_model_obs
${cpreq} "${HOMErrfs}"/workflow/sideload/DART/models/mpas_atm/work/perfect_model_obs .
./perfect_model_obs
export err=$?
err_chk

# Clean up
rm mpas_template.nc

exit 0
