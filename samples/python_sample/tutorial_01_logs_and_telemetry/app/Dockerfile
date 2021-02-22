## App version : 

FROM stereolabs/iot:0.22.0-runtime-jetson-jp4.4

#Install build dependencies
RUN apt-get update -y && \
DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && \
     rm -rf /var/lib/apt/lists/* &&  apt-get autoremove &&  apt-get clean

RUN apt-get update -y && \
     DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata locales && \
     apt-get install -y --no-install-recommends python3-dev python3-pip python3-scipy \
          python3-setuptools python3-wheel libfreetype6-dev pkg-config && \
     rm -rf /var/lib/apt/lists/* && apt-get autoremove && apt-get clean

RUN pip3 install paho-mqtt    

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN cd / && mkdir src
ADD src /src
WORKDIR /src
#Copy your binary
CMD ["python3", "-u", "main.py"]