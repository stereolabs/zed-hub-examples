# Build Image
# This image contains all the necessary dependencies to build your sl_hub application
ARG BASE_IMAGE
FROM ${BASE_IMAGE} AS builder

#Install build dependencies
RUN apt-get update -y && \
DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata libx11-dev  && \
     rm -rf /var/lib/apt/lists/* && apt autoremove && apt clean

# Compilation
COPY ./sources/src /home/src
COPY ./sources/CMakeLists.txt /home

WORKDIR /home
RUN mkdir build
WORKDIR /home/build
RUN cmake -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs -DCMAKE_CXX_FLAGS="-Wl,--allow-shlib-undefined" .. && \
make -j3 && mv GNSS_Tacker_Sample /
WORKDIR /
RUN cd ..


