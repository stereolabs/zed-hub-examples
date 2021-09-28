# Tutorial 1 - Basic Application

This sample shows how to make a very simple application that **connects** itself to the cloud and **sends logs**. 

[**Github repository**](https://github.com/stereolabs/cmp-examples/tree/main/tutorials/tutorial_01_basic_app)

## Requirements
You will deploy this tutorial on one of the devices installed on **your CMP workspace**. The CMP supports Jetson Nano, TX2 and Xavier or any computer. If you are using a Jetson, make sure it has been flashed. If you haven't done it already, [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:
- [Sign In the CMP and created a workspace](https://www.stereolabs.com/docs/cloud/overview/get-started/).
- [Add and Setup a device](https://www.stereolabs.com/docs/cloud/overview/get-started/#add-a-camera).

This tutorial needs Edge Agent. By default when your device is setup, Edge Agent is running on your device.

You can start it using this command, and stop it with CTRL+C (note that it's already running by default after Edge Agent installation) :
```
$ edge_agent start
```

If you want to run it in backround use :
```
$ edge_agent start -b
```

And to stop it :
```
$ edge_agent stop
```

## Build and run this tutorial for development

Run the Edge Agent installed on your device using (note that it's already running by default after Edge Agent installation) :
```
$ edge_agent start
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
./app_executable
```

## The Source Code explained

To init your application, you have to get your ```SL_APPLICATION_TOKEN``` environment variable and use it in the ```IoTCloud::init``` function. `IoTCloud::init` starts communications between your app and the cloud. It must be called before using the IOTCloud API, so before sending logs (`IoTCloud::log`), telemetry(`IoTCloud::sendTelemetry`) custom stream (`IoTCloud::setCustomVideoMat`) and others ...
```c++
    const char * application_token = ::getenv("SL_APPLICATION_TOKEN");
    STATUS_CODE status_iot = IoTCloud::init(application_token);
```
You can set the log level limit to be displayed. Every log with LOG_LEVEL below the limit will not be print.  ``` setLogLevelThreshold(LOG_LEVEL local_terminal_log_level, LOG_LEVEL cloud_log_level)```
```c++
    IoTCloud::setLogLevelThreshold(LOG_LEVEL::INFO,LOG_LEVEL::INFO);
```

You can send a simple log to the cloud with ```IoTCloud::logInfo```
```c++
    IoTCloud::log("Application connected",LOG_LEVEL::INFO);
```

You can check if your application is connected to the cloud with ```IoTCloud::isInitialized```
```c++
    if (IoTCloud::isInitialized())
        IoTCloud::log("Application connected",LOG_LEVEL::INFO);
```

Not that there are 7 log Levels : 

- 0 - DEBUG : log level for debugging
- 1 - INFO : log level for an info
- 2 - STATUS : log level for a status
- 3 - WARNING : log level for a warning
- 4 - ERROR : log level for an error
- 5 - SUCCESS : log level for a success
- 6 - DISABLED : level where no log will be sent
