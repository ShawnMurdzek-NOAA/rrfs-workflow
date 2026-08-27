#!/bin/bash
# shellcheck disable=all
dart_hash=f2a13259
diag_hash=482f55dc
dart2_hash=bbd0f89

# Set necessary directories
toolsdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${toolsdir}/../.."
HOMErrfs="$( pwd )"
cd "${toolsdir}/../sideload"

# Clone DART if not done so already
if [[ -d DART ]]; then
  echo "DART/ already cloned, skipping cloning step"
else
  which git-lfs 2>/dev/null ||  module load git-lfs
  GIT_LFS_SKIP_SMUDGE=1 git clone -b DART_Regional https://github.com/syha/DART.git
  cd DART
  git checkout "${dart_hash}" &> /dev/null
  cd ..
fi

# Clone DART if not done so already
# DART version cloned above does not contain the IODA JEDI converter that we need
# Hence, we download a second version of DART
mkdir -p aux_dart
cd aux_dart
if [[ -d DART ]]; then
  echo "./aux_dart/DART/ already cloned, skipping cloning step"
else
  which git-lfs 2>/dev/null ||  module load git-lfs
  GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/NCAR/DART.git
  cd DART
  git checkout "${dart2_hash}" &> /dev/null
  cd ..
fi
cd ..

# Clone pyDARTdiags if not done so already
if [[ -d pyDARTdiags ]]; then
  echo "pyDARTdiags/ already cloned, skipping cloning step"
else
  which git-lfs 2>/dev/null ||  module load git-lfs
  GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/NCAR/pyDARTdiags
  cd pyDARTdiags
  git checkout "${diag_hash}" &> /dev/null
  cd ..
fi

# Build DART if not done so already
cd DART
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
