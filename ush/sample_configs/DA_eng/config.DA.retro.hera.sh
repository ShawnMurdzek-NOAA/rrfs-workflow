MACHINE="hera"
version="v0.00"
#RESERVATION="rrfsdet"

################################################################
#EXPT_BASEDIR="YourOwnSpace/${version}"
EXPT_SUBDIR="rrfs_test_da"

envir="para"
NET="rrfs_b"
TAG="c0v00"
MODEL="rrfs_b"
RUN="rrfs"

STMP="/scratch2/NCEPDEV/stmp3/${USER}/test_da"
PTMP="/scratch2/NCEPDEV/stmp3/${USER}/test_da"

EXTRN_MDL_DATE_JULIAN="TRUE"
################################################################

PREDEF_GRID_NAME=RRFS_CONUS_3km

. set_rrfs_config_general.sh
. set_rrfs_config_SDL_VDL_MixEn.sh

#ACCOUNT="your account on hera"

#DO_ENSEMBLE="TRUE"
#DO_ENSFCST="TRUE"
DO_DACYCLE="TRUE"
DO_SURFACE_CYCLE="TRUE"
DO_SPINUP="TRUE"
DO_SAVE_INPUT="TRUE"
DO_POST_SPINUP="FALSE"
DO_POST_PROD="TRUE"
DO_RETRO="TRUE"
DO_NONVAR_CLDANAL="TRUE"
DO_ENVAR_RADAR_REF="TRUE"
DO_SMOKE_DUST="FALSE"
DO_REFL2TTEN="FALSE"
RADARREFL_TIMELEVEL=(0)
FH_DFI_RADAR="0.0,0.25,0.5"
DO_SOIL_ADJUST="TRUE"
DO_RADDA="TRUE"
DO_BUFRSND="FALSE"
USE_FVCOM="FALSE"
PREP_FVCOM="FALSE"
DO_PARALLEL_PRDGEN="FALSE"
DO_GSIDIAG_OFFLINE="TRUE"

EXTRN_MDL_ICS_OFFSET_HRS="3"
LBC_SPEC_INTVL_HRS="1"
EXTRN_MDL_LBCS_OFFSET_HRS="6"
BOUNDARY_LEN_HRS="18"
BOUNDARY_PROC_GROUP_NUM="3"

# avaialble retro period:
# 20210511-20210531; 20210718-20210801
DATE_FIRST_CYCL="20220720"
DATE_LAST_CYCL="20220720"
CYCL_HRS=( "00" "12" )
CYCL_HRS_SPINSTART=("03" "15")
CYCL_HRS_PRODSTART=("09" "21")
CYCLEMONTH="7"
CYCLEDAY="20"

STARTYEAR=${DATE_FIRST_CYCL:0:4}
STARTMONTH=${DATE_FIRST_CYCL:4:2}
STARTDAY=${DATE_FIRST_CYCL:6:2}
STARTHOUR="00"
ENDYEAR=${DATE_LAST_CYCL:0:4}
ENDMONTH=${DATE_LAST_CYCL:4:2}
ENDDAY=${DATE_LAST_CYCL:6:2}
ENDHOUR="23"

PREEXISTING_DIR_METHOD="upgrade"
INITIAL_CYCLEDEF="${DATE_FIRST_CYCL}0300 ${DATE_LAST_CYCL}2300 12:00:00"
BOUNDARY_CYCLEDEF="${DATE_FIRST_CYCL}0000 ${DATE_LAST_CYCL}2300 06:00:00"
PROD_CYCLEDEF="00 01,02,04,05,07,08,10,11,13,14,16,17,19,20,22,23 ${CYCLEDAY} ${CYCLEMONTH} ${STARTYEAR} *"
PRODLONG_CYCLEDEF="00 0-23/3 ${CYCLEDAY} ${CYCLEMONTH} ${STARTYEAR} *"
#ARCHIVE_CYCLEDEF="${DATE_FIRST_CYCL}0700 ${DATE_LAST_CYCL}2300 24:00:00"
if [[ $DO_SPINUP == "TRUE" ]] ; then
  SPINUP_CYCLEDEF="00 03-08,15-20 ${CYCLEDAY} ${CYCLEMONTH} ${STARTYEAR} *"
fi

FCST_LEN_HRS="3"
FCST_LEN_HRS_SPINUP="1"
#FCST_LEN_HRS_CYCLES=(48 18 18 18 18 18 48 18 18 18 18 18 48 18 18 18 18 18 48 18 18 18 18 18)
for i in {0..23}; do FCST_LEN_HRS_CYCLES[$i]=3; done
for i in {0..23..3}; do FCST_LEN_HRS_CYCLES[$i]=12; done
DA_CYCLE_INTERV="1"
RESTART_INTERVAL="1"
RESTART_INTERVAL_LONG="1"
## set up post
POSTPROC_LEN_HRS="3"
POSTPROC_LONG_LEN_HRS="12"
NFHOUT_HF="1"
# 15 min output upto 18 hours
#NFHMAX_HF="2"
#NFHOUT="1"
#NSOUT_MIN="15"
#OUTPUT_FH="0.0 0.25 0.50 0.75 1.0 1.25 1.50 1.75 2.0 3.0 4.0 5.0 6.0 7.0 8.0 9.0 10.0 11.0 12.0"

USE_RRFSE_ENS="FALSE"
CYCL_HRS_HYB_FV3LAM_ENS=("00" "01" "02" "03" "04" "05" "06" "07" "08" "09" "10" "11" "12" "13" "14" "15" "16" "17" "18" "19" "20" "21" "22" "23")

SST_update_hour=01
GVF_update_hour=04
SNOWICE_update_hour=00
SOIL_SURGERY_time=2022072004
netcdf_diag=.true.
binary_diag=.false.

regional_ensemble_option=1   # 5 for RRFS ensemble

EXTRN_MDL_NAME_ICS="FV3GFS"
EXTRN_MDL_NAME_LBCS="FV3GFS"

ARCHIVEDIR="/1year/BMC/wrfruc/rrfs_b"
NCL_REGION="conus"

. set_rrfs_config.sh

NWGES="${PTMP}/nwges"  # Path to directory NWGES that save boundary, cold initial, restart files
if [[ ${regional_ensemble_option} == "5" ]]; then
  RRFSE_NWGES="/lfs/h2/emc/ptmp/emc.lam/rrfs/${version}/nwges"  # Path to RRFSE directory NWGES that mostly contains ensemble restart files for GSI hybrid.
  NUM_ENS_MEMBERS=30     # FV3LAM ensemble size for GSI hybrid analysis
  CYCL_HRS_PRODSTART_ENS=( "07" "19" )
  DO_ENVAR_RADAR_REF="TRUE"
fi
