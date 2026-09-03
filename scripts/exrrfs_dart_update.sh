#!/usr/bin/env bash
# shellcheck disable=SC1091,SC2153,SC2154,SC2034
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]: '
set -x

cpreq=${cpreq:-cpreq}
prefix=${EXTRN_MDL_SOURCE%_NCO} # remove the trailing '_NCO' if any
cd "${DATA}" || exit 1

#
#-----------------------------------------------------------------------
#
# Create necessary date strings
#
#-----------------------------------------------------------------------
#

timestr=$(date -d "${CDATE:0:8} ${CDATE:8:2}" +%Y-%m-%d_%H.%M.%S)

#
#-----------------------------------------------------------------------
#
# Copy and link input files
#
#-----------------------------------------------------------------------
#

# determine whether to begin new cycles and link correct ensembles
if [[ -r "${UMBRELLA_PREP_IC_DATA}/mem001/init.nc" ]]; then
  export START_TYPE='cold'
  initial_file='init.nc'
else
  export START_TYPE='warm'
  initial_file='mpasout.nc'
fi

# link ensembles members and define input/output files
# list_ana : List of analyses from DART filter (only include state variables)
list_ics="mpas_ics.txt"
list_lbcs="mpas_lbcs.txt"
list_ana="filter_out.txt"
touch ${list_ics}
touch ${list_lbcs}
touch ${list_ana}
mkdir -p mpas_ics
mkdir -p mpas_lbcs
mkdir -p filter_out
for i in $(seq -w 001 "${ENS_SIZE}"); do
  ln -snf "${UMBRELLA_PREP_IC_DATA}/mem${i}/${initial_file}" "mpas_ics/mem${i}.nc"
  ln -snf "${UMBRELLA_PREP_LBC_DATA}/mem${i}/lbc.${timestr}.nc" "mpas_lbcs/mem${i}.nc"
  ln -snf "${UMBRELLA_DART_FILTER_DATA}/ens_out/mem${i}.nc" "filter_out/mem${i}.nc"
  echo "mpas_ics/mem${i}.nc" >> ${list_ics}
  echo "mpas_lbcs/mem${i}.nc" >> ${list_lbcs}
  echo "filter_out/mem${i}.nc" >> ${list_ana}
done

# create a template netCDF file with both mpasout and invariant information
zeta_levels=${EXPDIR}/config/ZETA_LEVELS.txt
nlevel=$(wc -l < "${zeta_levels}")
ln -snf "${FIXrrfs}/${MESH_NAME}/${MESH_NAME}.invariant.nc_L${nlevel}_${prefix}" ./invariant.nc
${cpreq} "${UMBRELLA_PREP_IC_DATA}/mem001/${initial_file}" mpas_template.nc
ncks -A invariant.nc mpas_template.nc

# copy namelist
# Copy from COM so we ensure the settings are EXACTLY the same as DART filter
cd "${DATA}" || exit 1
${cpreq} "${COMOUT}/dart_filter/${WGF}/input.nml" .

#
#-----------------------------------------------------------------------
#
# Update MPAS ICs and LBCs (at analysis time) with DART analyses
#
#-----------------------------------------------------------------------
#

if [[ ${START_TYPE} == "warm" ]] || [[ ${START_TYPE} == "cold" && ${COLDSTART_CYCS_DO_DA^^} == "TRUE" ]]; then
  export OMP_NUM_THREADS=1

  # Update ICs
  source prep_step
  export pgm="update_mpas_states"
  ${cpreq} "${HOMErrfs}"/workflow/sideload/DART/models/mpas_atm/work/${pgm} .
  ./${pgm}
  export err=$?
  err_chk

  # Update LBCs
  # Currently no working
  echo 
  echo "LBC update not enabled yet. Skipping."
  echo
  #source prep_step
  #export pgm="update_bc"
  #${cpreq} "${HOMErrfs}"/workflow/sideload/DART/models/mpas_atm/work/${pgm} .
  #./${pgm}
  #export err=$?
  #err_chk

else
  echo "INFO: No DA at the cold start cycle"
fi

exit 0
