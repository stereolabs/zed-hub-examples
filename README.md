# ZED Hub examples

In this repository you will find:
- [**ZED Hub tutorials**](./tutorials/) that explain how to use the ZED Hub features in your apps and run them.
- [**Sample apps**](./samples/README.md) that provide you examples of ZED Hub usage and package/deploy them on ZED Hub as a service.

ZED Hub comes with samples demoing its main features. Each sample is writen in C++ and can be deployed as a ZED Hub app. All of them are associated to a Readme that explains how to deploy the app and the main step of the source code. 

[**Github repository**](https://github.com/stereolabs/cmp-examples)

## What are the available ZED Hub features explained in these tutorials:

- Live stream : How to display your camera's live video feed in the ZED Hub interface
- Telemetry : How to upload and store any kind of data in order to analyse and display it later 
- Application parameters: How to define parameters to your application, settable in the ZED Hub interface
- Remote functions: How to define and call a remote function
- Custum stream : How to replace your live camera stream by images of your choice
- Video event : How to define Video Events, reccorded ans accessible through the interface.

## Requirements
You will deploy these tutorials on one of the devices installed on your ZED Hub workspace. ZED Hub supports Jetson Nano, TX2 and Xavier or any computer. If you are using a Jetson, make sure it has been flashed. If you haven't done it already, [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:
- [Sign In the ZED Hub and create a workspace](https://www.stereolabs.com/docs/cloud/overview/get-started/).
- [Add and Setup a device](https://www.stereolabs.com/docs/cloud/overview/get-started/#add-a-camera).
- As most of the tutorials require a ZED camera, a ZED should be plugged to this device.

## What is a ZED Hub app ?
A ZED Hub app is an application deployed in a Docker container on one of the devices that you installed on your ZED Hub workspace. Note that it can be coded in the langage of your choice and is not limited to a camera usage. It can be everything: a web server, a sensor reporter, an alert notifier, a node-red application ... However the ZED Hub interface is optimized for camera managment, and is especialy adapted to the ZED 3D cameras. Therefore most of the available tutorials requires a ZED to be run.

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
A ZED Hub app is run in a Docker container. The [ZED Hub documentation](https://www.stereolabs.com/docs/cloud/applications/) explains in detail how an app is structured and deployed. 
To deploy an app you need to upload a .zip file that contains at least:
- a docker-compose.yml describing how the application should be run
- a runtime dockerfile listing the steps and commands to compile and run the application.
- an app.json file that describes your application, specifies its name and release name and defines the parameters (see tutorial_04_application_parameters for more information about it)
- the source code or the executable 

#### Developing an app in C++
We recommend you develop your app in C++, as the ZED Hub C++ API **sl_IOT** makes it easier to use the ZED Hub features.
The provided tutorials are a good starting point for your own apps. Here is how they should be used:

```
.
├── app
│   └── Dockerfile
├── app.json
├── docker-compose.yml
├── README.md
└── sources
    ├── CMakeLists.txt
    ├── Dockerfile
    └── src
        └── main.cpp 
```

**Build stage**: 
The source code needs to be compiled before deploying the app. The code is compiled inside a dedicated docker image. To run the associated container you just need to run 
```
$ edge_cli build
```
 This command, installed with Edge Agent in your device setup, will ask on which kind of device you will deploy your app and will set the `Dockerfile` parameters accordingly. The `Dockerfile` describes the build stage. It generates binaries, stored in the `./app` folder. Then, an `app.zip` file is generated (still by the edge_cli build command). This `app.zip` file is your packaged app and is ready to be deployed. It contains : 
- docker-compose.yml
- app.json 
- Dockerfile
- the binaries generated during the **build stage**
- an icon.png image (optional)

**Deployment stage**:  
Now you just need to deploy your app using the ZED Hub interface:
- In your workspace, in the **Applications** section, click on **Create a new app** 
- Get the .zip an Drag’n’Drop in the dedicated area
- Select the devices on which you want to deploy the app and press **Deploy** 


## Docker complement
This section describes in more detail the different Docker related files used by the ZED Hub.

> **Note** : You will need a bit of experience with docker. (As long as you know and understand the basics of building and running a container you’ll be more than fine)

### docker-compose.yml
The **docker-compose.yml** file is the first file that is read when the "app" app is deployed. It mainly indicates the path to the runtime Dockerfile that indicates how the app must be run. It also configures the Docker environment.
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

The runtime Dockerfile is the file that describes what your **Docker image** or **app** must do when deployed. It indicates which script or executable must be run. In the example below, the binary `app_executable` is run.

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

The build Dockerfile is **only used for C++ applications** and is **not part of your app** meaning that it is never packaged in the .zip file. It describes the image used to compile your C++ code. This image is similar to the runtime image (the image used to run your app) but contains additionnal tools required to build the source code and that your runtime image does not need. 

The build Dockerfile is used by the `edge_cli build` command and generates one or several **binaries**. These binaries are then used by the runtime image described by the runtime dockerfile.



## Next steps
These 7 samples/tutorials can be used as starting points to develop your own app. There are some additionnal, more advanced tutorials available, which can be used and modified in order to fit your specific needs.

### Uploading a new release
Let's suppose you have modified one of the tutorials and want to deploy your updated version.

- Modify the `app.json` file by giving it another release name. 
```js
    //...
    "release":{
        "name": "1.0.0",  //modify 1.0.0 by a name of your choice. We recommend to keep the x.x.x version scheme
      //... 
    }
    //...
```
You just have to follow the same build and deployment stages than those described in each tutorial.
