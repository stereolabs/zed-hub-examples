# ZED Hub examples

In this repository you will find:
- [**ZED Hub tutorials**](./tutorials/) that explain how to use the ZED Hub features in your apps and run them.
- [**Sample apps**](./samples/README.md) that provide you examples of ZED Hub usage and package/deploy them on ZED Hub as a service.

ZED Hub comes with samples demoing its main features. Each sample is writen in C++ and can be deployed as a ZED Hub app. All of them are associated to a Readme that explains how to deploy the app and the main step of the source code. 

[**Github repository**](https://github.com/stereolabs/cmp-examples)

## What are the ZED Hub features available and explained in these tutorials:

- Live stream : How to display  your camera live video in the ZED Hub interface
- Telemetry : How to upload and store any kind of data in order to analyse and display it later 
- Application parameters: How to define parameters to your application, settable in the ZED Hub interface
- Remote functions: How to define and call a remote function
- Custum stream : How to replace your live camera stream by images of your choice
- Video event : How to define Video Events, reccorded ans accessible through the interface.

## Requirements
You will deploy these tutorials on one of the devices installed on your ZED Hub workspace. ZED Hub supports Jetson Nano, TX2 and Xavier or any computer. If you are using a Jetson, make sure it has been flashed. If you haven't done it already, [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:
- [Sign In the ZED Hub and created a workspace](https://www.stereolabs.com/docs/cloud/overview/get-started/).
- [Add and Setup a device](https://www.stereolabs.com/docs/cloud/overview/get-started/#add-a-camera).
- As most of the tutorials require a ZED camera, a ZED should be plugged to this device.

## What is a ZED Hub app ?
A ZED Hub app is an application deployed in a Docker container on one of the devices that you installed on your ZED Hub workspace. Note that it can be coded in the langage of your choice and is not limited to a camera usage. It can be everything: a web server, a sensor reporter, an alert notifier, a node-red application ... However the ZED Hub interface is optimized for the camera managment, and is especialy adapted to the ZED 3D cameras. Therefore most of the available tutorials requires a ZED to be runned.

## Develop a ZED Hub app

In these [**ZED Hub tutorials**](./tutorials/) you will learn how to develop a ZED Hub app, exploring each feature.
The only requirement is to setup a device to install the Edge Agent software and the sl_iot library.

You can start it using this command, and stop it with CTRL+C (note that it's already running by default after Edge Agent installation) :
```
$ edge_cli start
```

If you want to run it in backround use :
```
$ edge_cli start -b
```

And to stop it :
```
$ edge_cli stop
```

## Deploy a ZED Hub app a service

For production, you need to deploy your application on your device as a service, using Docker.
Here is the full explanation on how to do it. Examples are available on [**Sample apps**](./samples/).

### General structure
A ZED Hub app is runned in a Docker container. The [ZED Dreate a new app** 
- Get the .zip an Drag’n’Drop in the dedicated area
- Select the devices on which you want to deploy  the app and press **Deploy** 


## Docker complement
Here are some explaination about the docker related files.  

> **Note** : You need a bit of experience with docker. (As long as you know and understand the basics of building and running a container you’ll be more than fine)

### docker-compose.yml
The **docker-compose.yml** file is the first file that is read when app app is deployed. It many indicates the path to the runtime Dockerfile that indicates how the app must be runned. It also configure the Docker environment.
```
version: '2.3'
services:
  tuto01_service:
    build :
        context : ./app
        dockerfile : Dockerfile
        args :
            BASE_IMAGE: stereolabs/iot:0.22.0-runtime-jetson-jp4.4
    runtime: nvidia
    privileged: true
    network_mode: "host"
    environment:
        - NVIDIA_DRIVER_CAPABILITIES=all
```

In this example the container of the application will run the **tuto01_service** service. This service will use the Dockerfile named **Dockerfile** in the `./app` folder. This Dockerfile will be read with the parameter **BASE_IMAGE** set to `stereolabs/iot:0.22.0-runtime-jetson-jp4.4` by default.


### Runtime Dockerfile

The runtime Dockerfile is the file that described what your **Docker image** or **app** must do when deployed. Basicly it indicates which script or executable must be runned. In the exemple bellow the binary `app_executable` is runned.

```
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

#Install build dependencies
RUN apt-get update -y && \
DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata libpng-dev && \
     rm -rf /var/lib/apt/lists/* &&  apt-get autoremove &&  apt-get clean

#Copy your binary
COPY app_executable /
CMD ["/app_executable"]

```

### Build Dockerfile

The build Dockerfile is **only used for the c++ applications** and is **not part of your app** meaning that it is never package in the .zip file. It descibes the image used to compile your c++ code. This image is similar to the runtime image (the image used to run your app) but may contain tools required to build the source code and that your runtime image does not need. 

The build Dockerfile is used by the `edge_cli build` command and generate one ore several **binaries**. These binaries are then used by the runtime Image described bu the runtime dockerfile.



## Next steps
These 7 samples/tutorials can be used as starting point to devlop your own app. Some other tutorials are available to help you to identify where and how modifing these app in order to adapte them to your needs.

### How to upload a new release?
Lets supposed you modified one of the tutorials and want to deploy this new version.

- Modify the `app.json` file by giving an other release name. 
```js
    //...
    "release":{
        "name": "1.0.0",  //modify 1.0.0 by a name of your choice. You are advice to keep the x.x.x shape
      //... 
    }
    //...
```
You just have to follow the same build and deployment stages than those described in each tutorial.
