#!/usr/bin/env bash
# shellcheck disable=all
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]: '
set -x
date
#
export HOMErrfs=${HOMErrfs} #comes from the workflow at runtime
export EXECrrfs=${EXECrrfs:-${HOMErrfs}/exec}
export FIXrrfs=${FIXrrfs:-${HOMErrfs}/fix}
export PARMrrfs=${PARMrrfs:-${HOMErrfs}/parm}
export USHrrfs=${USHrrfs:-${HOMErrfs}/ush}
#

# Create and enter working directory
workdir="${COMOUT}/dart_diags/${WGF}/"
mkdir -p ${workdir}
cd ${workdir}

# Link DART obs_seq.final
ln -snf "${COMOUT}/dart_filter/${WGF}/obs_seq.final" .

# Run pyDARTdiags
pyDARTdiags_dir="${HOMErrfs}/workflow/sideload/pyDARTdiags"
export PYTHONPATH="${PYTHONPATH}:${pyDARTdiags_dir}/src"
${HOMErrfs}/workflow/sideload/run_dart_diags.py

exit 0
