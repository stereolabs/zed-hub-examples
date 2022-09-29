## App version : 
# Runtime image
# This image is for running the application
# we just copy the executable in this container

ARG BASE_IMAGE
FROM ${BASE_IMAGE}

#Install build dependencies
RUN apt-get update -y && \
DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata libpng-dev && \
     rm -rf /var/lib/apt/lists/* &&  apt-get autoremove &&  apt-get clean

#Copy your binary
COPY Camera_Viewer_Sample /
CMD ["/Camera_Viewer_Sample"]
