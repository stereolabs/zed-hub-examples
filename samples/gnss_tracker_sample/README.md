# GNSS Tracker

This sample shows how to send GNSS data in a ZED Hub Application to display them in the **Map page**.
It also explains how to generate:

- **Logs** that give information about the application's status
- **WebRTC messages** that contain data to be displayed in ZED Hub's **Map page**
- A **Callback function** that retrieves waypoints created in ZED Hub's **Map page**

The application defines **parameters** that can be modified in the ZED Hub interface to change the application's behavior while its running.

## Requirements

This sample is a mix of the **basic tutorials** provided in the `tutorials` folder. We recommend to **read and test them** before running this sample. These tutorials provide a lot of information on ZED Hub features and will make it easier to understand the **GNSS Tracker Sample**.

You will deploy these tutorials on a device installed on your ZED Hub workspace. ZED Hub supports Jetson L4T and Ubuntu operating systems. If you are using a Jetson, make sure it has been flashed beforehand. If you haven't done it already, please take a look at the NVIDIA documentation to [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:

- [Sign in to ZED Hub and create a workspace](https://www.stereolabs.com/docs/cloud/overview/get-workspace/).
- [Add and setup a device](https://www.stereolabs.com/docs/cloud/overview/setup-device/).
- A ZED must be plugged to this device.

## Build and deploy this tutorial

### How to build your application (for development)

Run the Edge Agent installed on your device using :

```
$ edge_cli start
```

Then to build your app :

```
$ cd sources
$ mkdir build
$ cd build
$ cmake ..
$ make -j$(nproc)
```

This application defines application parameters in order to modify its behavior while it is running. Move the `parameters.json` file to the path you specified in the `HubClient::loadApplicationParameters` function.

```
$ cp ../parameters.json .
```

Then to run your app :

```
./GNSS_Tracker_Sample
```

To dynamically change the parameters and activate their callbacks, edit the `parameters.json` file.

### How to build your application (for service deployment)

To build your app just run:

```
$ cd /PATH/TO/gnss_tracker_sample
$ edge_cli build
```

This command is available by installing Edge Agent on your device.

- The command will ask for the **device type** (Jetson or x86) on which you want to deploy this app.
- The command will also ask for your **device cuda version**. If you do not know it you can find it in the **Info** section of your device in the ZED Hub interface.
- Finally you will be asked the **sl_iot version** you want to use. The default one is the one installed on your device with Edge Agent. It corresponds to the base docker image used to build your app docker image. You can chose the default one, or look for the [most recent version available on Docker Hub](https://hub.docker.com/r/stereolabs/iot/tags?page=1&ordering=last_updated).

### How to deploy your application

Packages your app by generating a app.zip file using :

```
$ edge_cli build
```

You can now [deploy your app](https://www.stereolabs.com/docs/cloud/applications/deployment/) using the ZED Hub interface:

- In your workspace, in the **Applications** section, click on **Create a new app**
- Select the ZIP file containing the application in your filesystem
- Select the devices on which you want to deploy the app and press **Deploy**

## What you should see after deployment

### Live video

A video with bounding boxes around detected persons should be available in the **Video panel**.

### Logs

The logs should inform you about the app status.

### Maps

The GNSS data should be displayed on a map in the **Map page** on ZED Hub.

### Parameters

The following parameter can be used to modify your application's behavior:

- **Data frequency**: Data frequency defines how often data are produced by the application. Every second by default.

## Code overview

### Parameters callback

The following callbacks are defined in this sample and will be triggered when a parameter is modified in ZED Hub.

Callback for `dataFreq` application parameter

```c++
void onDataFreqUpdate(FunctionEvent &event)
{
    event.status = 0;
    dataFreq = HubClient::getParameter<float>("dataFreq", PARAMETER_TYPE::APPLICATION, dataFreq);
}
```

Callback for `waypoints` device parameter (as waypoints are sent as device parameter)

```c++
void onWaypoints(FunctionEvent &event)
{
    // Get gnss waypoints from the device parameters
    std::string waypoints = HubClient::getParameter<std::string>("waypoints", PARAMETER_TYPE::DEVICE, "[]");
    std::cout << "waypoints: " << waypoints << std::endl;

    event.status = 0;
    event.result = waypoints;
}
```

### Initialization

The application is initialized using `HubClient::connect`, the ZED camera is started with the ZED SDK `open` method and registered to ZED Hub using `HubClient::registerCamera`.

### Main loop

- **WebRTC messages** containing GNSS position (which is randomly generated) are sent to the `geolocation` label to all connected peers.

```c++
Timestamp current_ts = p_zed->getTimestamp(TIME_REFERENCE::IMAGE);

if ((uint64_t)(current_ts.getMilliseconds() >= (uint64_t)(prev_timestamp.getMilliseconds() + (uint64_t)dataFreq * 1000ULL)))
{
    // Update coordinate
    latitude += getRandom();
    latitude = min(90.0, latitude);
    latitude = max(-90.0, latitude);
    longitude += getRandom();
    longitude = min(180.0, longitude);
    longitude = max(-180.0, longitude);
    altitude += getRandom();

    // Send data
    json gnss;
    gnss["layer_type"] = "geolocation";
    gnss["label"] = "GNSS_data";
    gnss["position"] = {
        {"latitude", latitude},
        {"longitude", longitude},
        {"altitude", altitude}};
    HubClient::sendDataToPeers("geolocation", gnss.dump());
    prev_timestamp = current_ts;
}
```
