# Deploy a ZED Hub app a service

For production, you need to deploy your application on your device as a service, using Docker.
Here is the full explanation on how to do it. Examples are available on [**Sample apps**](./samples/).

## General structure
A ZED Hub app is run in a Docker container. The [ZED Hub documentation](https://www.stereolabs.com/docs/cloud/applications/) explains in detail how an app is structured and deployed.
To deploy an app you need to upload a .zip file that contains at least:
- a docker-compose.yml describing how the application should be run
- a runtime dockerfile listing the steps and commands to compile and run the application.
- an app.json file that describes your application, specifies its name and release name and defines the parameters (see tutorial_04_application_parameters for more information about it)
- the source code or the executable

We provide tutorials and sample to develop your app in C++ and Python. The samples are especially made to describe how to deploy an app as a service.

### Developing an app in C++

With C++, your app should fit with this design :

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
The `Dockerfile` in source is dedicated to build your app. `edge_cli` will help you build an app targeting a jetson platform from your linux machine. If you just want to target your own machine, you can simply build your app with `cmake`.

**Build stage**:
The source code needs to be compiled before deploying the app. The code is compiled inside a dedicated docker image. To run the associated container you just need to run
```
$ cd /your/app/folder
$ edge_cli build .
```
This command, installed with Edge Agent in your device setup, will ask on which kind of device you will deploy your app and will set the `Dockerfile` parameters accordingly. The `Dockerfile` describes the build stage. It generates binaries, stored in the `./app` folder.

### Developing an app in Python
With Python, your app should fit with this design :

```
.
├── app
│   └── Dockerfile
│   └── main.py
│   └── ...other sources files...
├── app.json
├── docker-compose.yml
└── README.md

```
Python dos not need any build stage.

### Deploy stage
The deploy stage consists in create a .zip file containing
- app/Dockerfile
- app/<your_app> the binaries generated during the **build stage**, or the source in case your using Python.
- app.json
- docker-compose.yml
- an icon.png image (optional)

There is an automated command to do that :
```
$ cd /your/app/folder
$ edge_cli deploy .
```
`app.zip` file is generated. It is ready to be deployed.

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
            BASE_IMAGE: stereolabs/iot:0.63.0-runtime-jetson-jp4.4
    runtime: nvidia
    privileged: true
    network_mode: "host"
    environment:
        - NVIDIA_DRIVER_CAPABILITIES=all
```

In this example the container of the application will run the **tuto01_service** service. This service will use the Dockerfile named **Dockerfile** in the `./app` folder. This Dockerfile will be read with the parameter **BASE_IMAGE** set to `stereolabs/iot:0.63.0-runtime-jetson-jp4.4` by default.


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

The build Dockerfile is **only used for C++ applications** and is **not part of your app** meaning that it is never packaged in the .zip file. It describes the image used to compile your C++ code. This image is similar to the runtime image (the image used to run your app) but contains additional tools required to build the source code and that your runtime image does not need.

The build Dockerfile is used by the `edge_cli build` command and generates one or several **binaries**. These binaries are then used by the runtime image described by the runtime dockerfile.

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
