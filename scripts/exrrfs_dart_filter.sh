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

# DART uses time in days/seconds since 1 Jan 1601
# Must specify timezone as UTC, otherwise difference is incorrect
# (this is because they had no timezones in 1601)
ref_time=$(TZ=UTC date -d "16010101" +%s)
cdate_sec=$(TZ=UTC date -d "${CDATE:0:8} ${CDATE:8:2}" +%s)
diff=$(( cdate_sec - ref_time ))

# Only consider obs within ob_offset sec of analysis time
ob_offset=5400
ob_start=$(( diff - ob_offset ))
ob_end=$(( diff + ob_offset ))

first_obs_days="$(( ob_start / 86400 ))"
first_obs_seconds="$(( ob_start % 86400 ))"
last_obs_days="$(( ob_end / 86400 ))"
last_obs_seconds="$(( ob_end % 86400 ))"

init_time_days="$(( diff / 86400 ))"
init_time_seconds="$(( diff % 86400 ))"

#
#-----------------------------------------------------------------------
#
# Copy and link input files
#
#-----------------------------------------------------------------------
#

# copy observations files from COM directory
${cpreq} "${COMOUT}/dart_obs_proc/${WGF}/obs_seq.out" .

# determine whether to begin new cycles and link correct ensembles
do_DAcycling='false'
if [[ -r "${UMBRELLA_PREP_IC_DATA}/mem001/init.nc" ]]; then
  export START_TYPE='cold'
  initial_file='init.nc'
else
  export START_TYPE='warm'
  initial_file='mpasout.nc'
fi

# link ensembles members and define input/output files
priors="filter_in.txt"
posteriors="filter_out.txt"
touch ${priors}
touch ${posteriors}
mkdir -p ens_in
mkdir -p "${UMBRELLA_DART_FILTER_DATA}/ens_out"
for i in $(seq -w 001 "${ENS_SIZE}"); do
  ln -snf "${UMBRELLA_PREP_IC_DATA}/mem${i}/${initial_file}" "ens_in/mem${i}.nc"
  echo "ens_in/mem${i}.nc" >> ${priors}
  echo "${UMBRELLA_DART_FILTER_DATA}/ens_out/mem${i}.nc" >> ${posteriors}
done

# create a template netCDF file with both mpasout and invariant information
zeta_levels=${EXPDIR}/config/ZETA_LEVELS.txt
nlevel=$(wc -l < "${zeta_levels}")
ln -snf "${FIXrrfs}/${MESH_NAME}/${MESH_NAME}.invariant.nc_L${nlevel}_${prefix}" ./invariant.nc
${cpreq} "${UMBRELLA_PREP_IC_DATA}/mem001/${initial_file}" mpas_template.nc
ncks -A invariant.nc mpas_template.nc
cd "${DATA}" || exit 1

# copy namelist
cd "${DATA}" || exit 1
${cpreq} "${FIXrrfs}/dart/input.nml" .

#
#-----------------------------------------------------------------------
#
# Update namelist
#
#-----------------------------------------------------------------------
#

sed -i "s={ENS_SIZE}=${ENS_SIZE}=" input.nml
sed -i "s={INIT_TIME_DAYS}=${init_time_days}=" input.nml
sed -i "s={INIT_TIME_SECONDS}=${init_time_seconds}=" input.nml
sed -i "s={FIRST_OBS_DAYS}=${first_obs_days}=" input.nml
sed -i "s={FIRST_OBS_SECONDS}=${first_obs_seconds}=" input.nml
sed -i "s={LAST_OBS_DAYS}=${last_obs_days}=" input.nml
sed -i "s={LAST_OBS_SECONDS}=${last_obs_seconds}=" input.nml
sed -i "s={ASSIMILATION_PERIOD_SECONDS}=$(( 2*ob_offset ))=" input.nml

#
#-----------------------------------------------------------------------
#
# Run DART filter program
#
#-----------------------------------------------------------------------
#

if [[ ${START_TYPE} == "warm" ]] || [[ ${START_TYPE} == "cold" && ${COLDSTART_CYCS_DO_DA^^} == "TRUE" ]]; then
  export OMP_NUM_THREADS=1

  source prep_step
  ${cpreq} "${HOMErrfs}"/workflow/sideload/DART/models/mpas_atm/work/filter .
  ${MPI_RUN_CMD} ./filter
  # check the status
  export err=$?
  err_chk

  # copy desired output files to COMOUT
  cp obs_seq.out "${COMOUT}/dart_filter/${WGF}"
  cp obs_seq.final "${COMOUT}/dart_filter/${WGF}"
  cp dart_log.out "${COMOUT}/dart_filter/${WGF}"

else
  echo "INFO: No DA at the cold start cycle"
fi

exit 0
