# ZED Hub examples

In this repository you will find:
- [**ZED Hub tutorials**](./tutorials/) that explain how to use the ZED Hub features in your apps and run them.
- [**ZED Hub samples**](./samples/README.md) that provide examples of ZED Hub usage and package/deploy them on ZED Hub as a service.
- [**ZED Hub scripts**](./scripts/README.md) that provide examples of ZED Hub REST API usage.

ZED Hub comes with samples demoing its main features. Each sample is written in C++ and can be deployed as a ZED Hub app. All of them are associated to a README that explains how to deploy the app and the main step of the source code. 

## What are the available ZED Hub features explained in these tutorials:

- **Live stream** : How to display your camera's live video feed in the ZED Hub interface
- **Telemetry** : How to upload and store any kind of data in order to analyze and display it later
- **Application parameters** : How to define parameters to your application, settable in the ZED Hub interface
- **Remote functions** : How to define and call a remote function
- **Video event** : How to define **Video Events**, recorded ans accessible through the interface.

## Requirements
You will deploy these tutorials on a device installed on your ZED Hub workspace. ZED Hub supports Jetson L4T and Ubuntu operating systems. If you are using a Jetson, make sure it has been flashed beforehand. If you haven't done it already, please take a look at the NVIDIA documentation to [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:
- [Sign in to ZED Hub and create a workspace](https://www.stereolabs.com/docs/cloud/overview/get-workspace/).
- [Add and setup a device](https://www.stereolabs.com/docs/cloud/overview/setup-device/).
- As most of the tutorials require a ZED camera, a ZED should be plugged to this device.

## What is a ZED Hub app ?
A ZED Hub app is an application deployed in a Docker container on a device that you installed on your ZED Hub workspace. ZED Hub's interface is optimized for camera management, and is especially adapted to the ZED 3D cameras. Therefore most of the available tutorials require a ZED to be run.

## Develop a ZED Hub app

In these [**ZED Hub tutorials**](./tutorials/) you will learn how to develop a ZED Hub app, exploring each feature.
The only requirement is to setup a device to install the Edge Agent software, which is done automatically when you register your device on ZED Hub.

Once Edge Agent has been installed, you can start the Edge Agent services using:
```
$ edge_cli start
```

> **Note**: It is already running by default after Edge Agent installation.

To stop the services, run:
```
$ edge_cli stop
```

## Deploying a ZED Hub app for production

Once you have successfully been able to run and test the apps in a development environment, you can look into deploying the same apps in production-ready environments with our [Deploy a ZED Hub app as a service](./deploy_as_a_service.md) tutorial.