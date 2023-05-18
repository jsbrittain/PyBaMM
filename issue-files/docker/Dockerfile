FROM ubuntu:latest

RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y update && \
    apt-get install -y software-properties-common
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install zsh tmux vim python3 python3-dev python3-distutils libopenblas-dev gcc gfortran curl make cmake git build-essential texlive-latex-recommended texlive-latex-extra
RUN apt-get -y install dvipng graphviz tree sudo mpich libblas-dev liblapack-dev pkg-config

RUN useradd -rm -d /home/jsb -s /bin/zsh -G sudo jsb
RUN echo 'jsb:jsb' | chpasswd
RUN echo 'root:root' | chpasswd

USER jsb
WORKDIR /home/jsb

# Python / pip / tox
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3 get-pip.py
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install "tox<4"

# Download before install
RUN git clone https://github.com/KarypisLab/GKlib.git && \
    git clone https://github.com/KarypisLab/METIS.git && \
    git clone https://github.com/KarypisLab/ParMETIS.git && \
    git clone https://github.com/xiaoyeli/superlu_dist.git

# GKLib
WORKDIR /home/jsb/GKlib
RUN make config prefix=/home/jsb/.local && \
    make && \
    make install

# METIS
WORKDIR /home/jsb/METIS
RUN make config prefix=/home/jsb/.local && \
    make install

# ParMETIS
WORKDIR /home/jsb/ParMETIS
RUN make config cc=mpicc prefix=/home/jsb/.local && \
    make install

# SuperLUDist install
WORKDIR /home/jsb/superlu_dist
RUN mkdir build && \
    cd build && \
    cmake .. \
        -DTPL_PARMETIS_INCLUDE_DIRS="/home/jsb/.local/include;/usr/include/x86_64-linux-gnu/mpich" \
        -DTPL_PARMETIS_LIBRARIES="/home/jsb/.local/lib/libGKlib.a;/home/jsb/.local/lib/libparmetis.a;/home/jsb/.local/lib/libmetis.a" \
	-DTPL_ENABLE_INTERNAL_BLASLIB="ON" \
        -DCMAKE_INSTALL_PREFIX="/home/jsb/.local" && \
    make && \
    make install
    

# PyBaMM
WORKDIR /home/jsb
RUN git clone https://github.com/jsbrittain/PyBaMM.git
WORKDIR /home/jsb/PyBaMM

#ARG FORCE_FRESH_COPY=1
COPY --chown=jsb ./PyBaMM/./ .
RUN git checkout parallel
RUN python3 -m tox -e pybamm-requires
RUN python3 -m tox -e dev
