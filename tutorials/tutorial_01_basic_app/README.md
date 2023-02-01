# Tutorial 1 - Basic Application

This sample shows how to make a very simple application that **connects** itself to the cloud and **sends logs**. 

[**Github repository**](https://github.com/stereolabs/zed-hub-examples/tree/main/tutorials/tutorial_01_basic_app)

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
./ZED_Hub_Tutorial_1
```

## The Source Code explained

To init your application, use the `HubClient::connect` function that starts communications between your app and the cloud. It must be called before using the HubClient API, so before sending logs (`HubClient::sendLog`), telemetry(`HubClient::sendTelemetry`) and others. Then, register your zed camera to the client.
```c++
    STATUS_CODE status_iot = HubClient::connect("basic_app");
```
You can set the log level limit to be displayed. Every log with LOG_LEVEL below the limit will not be print.  ``` setLogLevelThreshold(LOG_LEVEL local_terminal_log_level, LOG_LEVEL cloud_log_level)```
```c++
    HubClient::setLogLevelThreshold(LOG_LEVEL::INFO,LOG_LEVEL::INFO);
```

You can send a simple log to the cloud with ```HubClient::sendLogInfo```
```c++
    HubClient::sendLog("Application connected",LOG_LEVEL::INFO);
```

You can check if your application is connected to the cloud with ```HubClient::isConnected```
```c++
    if (HubClient::isInitialized())
        HubClient::sendLog("Application connected",LOG_LEVEL::INFO);
```

Not that there are 7 log Levels : 

- 0 - DEBUG : log level for debugging
- 1 - INFO : log level for an info
- 2 - STATUS : log level for a status
- 3 - WARNING : log level for a warning
- 4 - ERROR : log level for an error
- 5 - SUCCESS : log level for a success
- 6 - DISABLED : level where no log will be sent
