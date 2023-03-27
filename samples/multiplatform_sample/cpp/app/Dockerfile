ARG BUILD_IMAGE
ARG RUNTIME_IMAGE
FROM ${BUILD_IMAGE} as builder

## Compilation of the app
COPY ./sources /home/
RUN mkdir /home/build
WORKDIR /home/build
RUN cmake -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs -DCMAKE_CXX_FLAGS="-Wl,--allow-shlib-undefined" .. && \
make -j8 && mv Multiplatform_Sample /
WORKDIR /

## Output part -- send files out of docker context
ARG RUNTIME_IMAGE
FROM ${RUNTIME_IMAGE}

COPY --from=builder /Multiplatform_Sample ./
 
CMD ["/Multiplatform_Sample"]
