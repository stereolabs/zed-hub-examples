# Tutorial 10 - Metadata Stream

This tutorial shows how to stream 3D skeleton data to ZED Hub, in addition to the video stream. You will be able to view the streamed data in the **Video panel** of your device.

## Requirements

You will deploy this tutorial on one of the devices installed on **your ZED Hub workspace**. The ZED Hub supports Jetson Nano, TX2 and Xavier or any computer. If you are using a Jetson, make sure it has been flashed. If you haven't done it already, [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:

- [Sign in to ZED Hub and create a workspace](https://www.stereolabs.com/docs/cloud/overview/get-workspace/).
- [Add and setup a device](https://www.stereolabs.com/docs/cloud/overview/setup-device/).

This tutorial requires Edge Agent to be installed and running in order to connect to ZED Hub. You can make sure it is running and connected by using:

```
$ edge_cli status
```

If it is not running, you can restart the service using:

```
$ edge_cli restart
```

## Build and run this tutorial for development

With Edge Agent installed and running, you can build this tutorial with the following commands:

```
$ mkdir build
$ cd build
$ cmake ..
$ make -j$(nproc)
```

Then run your app :

```
./ZED_Hub_Tutorial_10
```

## Code overview

This tutorial is focused on retrieving and streaming 3D skeleton data from a ZED camera. Retrieving this data is done through the ZED SDK method:

```c++
p_zed->retrieveObjects(objects, obj_det_rt_params);
```

Once the data is retrieved in an `sl::Objects` instance, the data is sent for every main loop iteration with:

```c++
HubClient::update(p_zed, objects);
```
