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

## Deploying a ZED Hub app for production

Once you have successfully been able to run and test the apps in a development environment, you can look into deploying the same apps in production-ready environments with our [Deploy a ZED Hub app as a service](./deploy_as_a_service.md) tutorial.

## Next steps
These samples and tutorials can be used as starting points to develop your own app. There are some additionnal, more advanced tutorials available, which can be used and modified in order to fit your specific needs.
