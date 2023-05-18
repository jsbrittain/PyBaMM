#!/bin/usr/env bash

set -euxo pipefail

echo $0
echo $1

# check inputs
if [ $# -ne 1 ]; then
    echo "Usage: $0 <pybamm_dir>"
    exit 1
fi

DOWNLOAD_DIR=$1
INSTALL_DIR=~/.local
CC=mpicc
MPICH=/usr/include/x86_64-linux-gnu/mpich

cd ${DOWNLOAD_DIR}

# Download dependencies
git clone https://github.com/KarypisLab/GKlib.git
git clone https://github.com/KarypisLab/METIS.git
git clone https://github.com/KarypisLab/ParMETIS.git
git clone https://github.com/xiaoyeli/superlu_dist.git

# Build GKlib
cd GKlib
make config prefix=${INSTALL_DIR}
make install
cd ..

# Build METIS
cd METIS
make config prefix=${INSTALL_DIR}
make install
cd ..

# Build ParMETIS
cd ParMETIS
make config prefix=${INSTALL_DIR} cc=${CC}
make install
cd ..

# Build SuperLU_DIST
cd superlu_dist
mkdir build && cd build
cmake .. \
    -DTPL_PARMETIS_INCLUDE_DIRS="${INSTALL_DIR}/include;${MPICH}" \
    -DTPL_PARMETIS_LIBRARIES="${INSTALL_DIR}/lib/libGKlib.a;${INSTALL_DIR}/lib/libparmetis.a;${INSTALL_DIR}/lib/libmetis.a" \
    -DTPL_ENABLE_INTERNAL_BLASLIB="ON" \
    -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR}
make install
cd ../..
