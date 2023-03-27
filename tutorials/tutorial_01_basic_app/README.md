# Tutorial 1 - Basic Application

This tutorial shows how to make a very simple application that **connects** itself to the cloud and **sends logs**. 

## Requirements
You will deploy these tutorials on a device installed on your ZED Hub workspace. ZED Hub supports Jetson L4T and Ubuntu operating systems. If you are using a Jetson, make sure it has been flashed beforehand. If you haven't done it already, please take a look at the NVIDIA documentation to [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:
- [Sign in to ZED Hub and create a workspace](https://www.stereolabs.com/docs/cloud/overview/get-workspace/).
- [Add and setup a device](https://www.stereolabs.com/docs/cloud/overview/setup-device/).

This tutorial needs Edge Agent. You can start it using this command :
```
$ edge_cli start
```

> **Note**: It is already running by default after Edge Agent installation.

And to stop it :
```
$ edge_cli stop
```

## Build and run this tutorial for development

With Edge Agent installed and running, you can build this tutorial with the following commands :
```
$ mkdir build
$ cd build
$ cmake ..
$ make -j$(nproc)
```

Then run your app :
```
./ZED_Hub_Tutorial_1
```

## The Source Code explained

To initialize your application, use the `HubClient::connect` function that starts communications between your app and the cloud. It must be called before using the HubClient API, so before sending logs (`HubClient::sendLog`), telemetry (`HubClient::sendTelemetry`) and others.
```c++
    STATUS_CODE status_iot;
    status_iot = HubClient::connect("basic_app");
```
You can set the log level limit to be displayed. Every log with LOG_LEVEL below the limit will not be print.  ``` setLogLevelThreshold(LOG_LEVEL local_terminal_log_level, LOG_LEVEL cloud_log_level)```
```c++
    HubClient::setLogLevelThreshold(LOG_LEVEL::INFO, LOG_LEVEL::INFO);
```

You can send a simple log to the cloud with ```HubClient::sendLogInfo```
```c++
    HubClient::sendLog("Application connected", LOG_LEVEL::INFO);
```

You can check if your application is connected to the cloud with ```HubClient::isInitialized```
```c++
    if (HubClient::isInitialized() == STATUS_CODE::SUCCESS)
        HubClient::sendLog("Application connected", LOG_LEVEL::INFO);
```

Not that there are 7 log Levels : 

- 0 - DEBUG : log level for debugging
- 1 - INFO : log level for an info
- 2 - STATUS : log level for a status
- 3 - WARNING : log level for a warning
- 4 - ERROR : log level for an error
- 5 - SUCCESS : log level for a success
- 6 - DISABLED : level where no log will be sent
