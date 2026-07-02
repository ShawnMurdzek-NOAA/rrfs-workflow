#!/bin/bash
# shellcheck disable=all
dart_hash=f2a13259
#
toolsdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${toolsdir}/../sideload"
if [[ -d DART ]]; then
  echo "DART/ already cloned, no actions."
else
  which git-lfs 2>/dev/null ||  module load git-lfs
  set -x
  GIT_LFS_SKIP_SMUDGE=1 git clone -b DART_Regional https://github.com/syha/DART.git
  cd DART
  git checkout "${dart_hash}" &> /dev/null
fi
