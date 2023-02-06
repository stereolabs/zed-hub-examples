# Tutorial 10 - Metadata Stream

This tutorial shows you how to stream skeletons in addition of the video stream.

[**Github repository**](https://github.com/stereolabs/zed-hub-examples/tree/main/tutorials/tutorial_10_metadata_stream)

## Requirements

You will deploy this tutorial on one of the devices installed on **your ZED Hub workspace**. The ZED Hub supports Jetson Nano, TX2 and Xavier or any computer. If you are using a Jetson, make sure it has been flashed. If you haven't done it already, [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:

- [Sign In the ZED Hub and create a workspace](https://www.stereolabs.com/docs/cloud/overview/get-started/).
- [Add and Setup a device](https://www.stereolabs.com/docs/cloud/overview/get-started/#add-a-camera).

This tutorial needs Edge Agent. By default when your device is setup, Edge Agent is running on your device.

You can start it using this command, and stop it with CTRL+C (note that it's already running by default after Edge Agent installation) :

```
$ edge_cli start
```

If you want to run it in background use :

```
$ edge_cli start -b
```

And to stop it :

```
$ edge_cli stop
```

## Build and run this tutorial for development

Run the Edge Agent installed on your device using (note that it's already running by default after Edge Agent installation) :

```
$ edge_cli start
```

Then to build your app :

```
$ mkdir build
$ cd build
$ cmake ..
$ make -j$(nproc)
```

Then to run your app :

```
./ZED_Hub_Tutorial_10
```

## Code overview

Retrieve the detection results.

```c++
p_zed->retrieveObjects(objects, obj_det_rt_params);
```

Send the detection results.

```c++
HubClient::update(p_zed, objects);
```
