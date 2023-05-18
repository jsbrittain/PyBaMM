#!/usr/bin/env bash

podman build --build-arg FORCE_FRESH_COPY=$(date +%Y%m%d-%H%M%S) --rm -f Dockerfile -t ubuntu:pybamm_mpi .
podman run --rm -it -e "TERM=xterm-256color" --name pybamm_mpi ubuntu:pybamm_mpi
