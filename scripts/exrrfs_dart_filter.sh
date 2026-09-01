#!/usr/bin/env bash
# shellcheck disable=SC1091,SC2153,SC2154,SC2034
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]: '
set -x

cpreq=${cpreq:-cpreq}
prefix=${EXTRN_MDL_SOURCE%_NCO} # remove the trailing '_NCO' if any
cd "${DATA}" || exit 1

start_time=$(date -d "${CDATE:0:8} ${CDATE:8:2}" +%Y-%m-%d_%H:%M:%S)
timestr=$(date -d "${CDATE:0:8} ${CDATE:8:2}" +%Y-%m-%d_%H.%M.%S)
time_min="${subcyc:-00}"
#
zeta_levels=${EXPDIR}/config/ZETA_LEVELS.txt
nlevel=$(wc -l < "${zeta_levels}")
ln -snf "${FIXrrfs}/${MESH_NAME}/${MESH_NAME}.invariant.nc_L${nlevel}_${prefix}" ./invariant.nc
#
# link observations files
#
mkdir -p OBS_DIR
ln -snf "${UMBRELLA_DART_OBS_PROC_DATA}/obs_seq.out" "OBS_DIR/obs_seq.out"
#
# determine whether to begin new cycles and link correct ensembles
#
do_DAcycling='false'
if [[ -r "${UMBRELLA_PREP_IC_DATA}/mem001/init.nc" ]]; then
  export START_TYPE='cold'
  initial_file='init.nc'
else
  export START_TYPE='warm'
  initial_file='mpasout.nc'
fi
#
# link ensembles members and define input/output files
#
priors="filter_in.txt"
posteriors="filter_out.txt"
touch ${priors}
touch ${posteriors}
mkdir -p ens_in
mkdir -p ens_out
for i in $(seq -w 001 "${ENS_SIZE}"); do
  ln -snf "${UMBRELLA_PREP_IC_DATA}/mem${i}/${initial_file}" "ens_in/mem${i}.nc"
  echo "ens_in/mem${i}.nc" >> ${priors}
  echo "ens_out/mem${i}.nc" >> ${posteriors}
done
#
# enter the run directory again
#
cd "${DATA}" || exit 1
#
# copy namelist
cp "${FIXrrfs}/dart/input.nml"

if [[ ${START_TYPE} == "warm" ]] || [[ ${START_TYPE} == "cold" && ${COLDSTART_CYCS_DO_DA^^} == "TRUE" ]]; then
  export OMP_NUM_THREADS=1

  source prep_step
  ${cpreq} "${HOMErrfs}"/workflow/sideload/DART/models/mpas_atm/work/filter .
  ${MPI_RUN_CMD} ./filter
  # check the status
  export err=$?
  err_chk

  # copy desired output files to COMOUT
  cp -r OBS_DIR "${COMOUT}/dart_filter/${WGF}"

else
  echo "INFO: No DA at the cold start cycle"
fi
