#!/bin/bash
# shellcheck disable=all
dart_hash=f2a13259

# Set necessary directories
toolsdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${toolsdir}/../.."
HOMErrfs="$( pwd )"
cd "${toolsdir}/../sideload"

# Clone DART if not done so already
if [[ -d DART ]]; then
  echo "DART/ already cloned, skipping cloning step"
  cd DART
else
  which git-lfs 2>/dev/null ||  module load git-lfs
  set -x
  GIT_LFS_SKIP_SMUDGE=1 git clone -b DART_Regional https://github.com/syha/DART.git
  cd DART
  git checkout "${dart_hash}" &> /dev/null
fi

# Build DART if not done so already
DARTdir="$( pwd )"
cd models/mpas_atm/work
if [[ -f filter ]]; then
  echo "DART already compiled. No actions performed."
else
  set -x
  COMPILER=intel
  source "${HOMErrfs}/workflow/tools/detect_machine.sh"

  module purge
  module use "${HOMErrfs}/modulefiles"
  module load "rrfs/${MACHINE}.${COMPILER}"
  module list

  cp ${HOMErrfs}/fix/dart/input.nml .
  cp ${HOMErrfs}/fix/dart/mkmf.template.${MACHINE}.${COMPILER} ${DARTdir}/build_templates/mkmf.template

  ./quickbuild.sh 

  EXEC=( filter mpas_dart_obs_preprocess update_bc update_mpas_states)
  for e in ${EXEC[@]}; do
    if [[ -f ${e} ]]; then
      mkdir -p "${HOMErrfs}/exec"
      cp ${e} "${HOMErrfs}/exec/"
    else
      echo "Missing DART executable: ${e}"
    fi
  done

fi
