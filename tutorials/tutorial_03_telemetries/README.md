# Tutorial 3 - Telemetries
This tutorial shows you how to send telemetry to the cloud. This sample app opens a ZED and enable ZED tracking, meaning that you can access the camera position at each frame. Then the application gets the camera position and sends it to the cloud at each frame. Therefore the Telemetry panel will contain all the concecutive position of your camera.  

[**Github repository**](https://github.com/stereolabs/cmp-examples/tree/main/tutorials/tutorial_03_telemetries)

## Requirements
You will deploy this tutorial on one of the devices installed on your ZEDHub workspace. The ZEDHub supports Jetson Nano, TX2 and Xavier or any computer. If you are using a Jetson, make sure it has been flashed. If you haven't done it already, [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:
- [Sign In the ZEDHub and created a workspace](https://www.stereolabs.com/docs/cloud/overview/get-started/).
- [Add and Setup a device](https://www.stereolabs.com/docs/cloud/overview/get-started/#add-a-camera).
- A ZED must be plugged to this device.
- **Enable recordings** and **disable privacy mode** in the Settings panel of your device

This tutorial needs Edge Agent. By default when your device is setup, Edge Agent is running on your device.

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
./app_executable
```

## What you should see after deployment
This app have two direct consequences in the ZEDHub interface:
- A live stream should be visible
- The published telemetry should be accessible

### Live video
If you click in the **Devices** panel  on the device where the app is deployed, you should see the live video (with a delay of a few seconds).

![](./images/live_and_recordings.png " ")

###  Telemetry
If you click go in the **Telemetry** panel, you should see the telemetry of your camera position as follow:

![](./images/telemetry.png " ")


## Code Overview

This sample app opens a ZED and enable ZED tracking, meaning that you can access the camera position at each frame. Then the application gets the camera position and sends it to the cloud at each frame. Therefore the Telemetry panel will contain all the concecutive position of your camera.  

What exactly appends:

- Init IOT to enable communications with the cloud. (See tutorial_01_basic_app README for more information).

- Open the ZED with `p_zed->open(initParameters)`. (See tutorial_02_live_stream_and_recording  README for more information).

- Enable Positional Tracking with `p_zed->enablePositionalTracking(positional_tracking_param)`. (See [ZED SDK API documentation](https://www.stereolabs.com/docs/api/classsl_1_1Camera.html#a7989ae783fae435abfdf48feaf147f44) for more information).

- In a While loop, grab a new frame

```
// Main loop
    while (true) {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab(runtime_parameters);
        if (status_zed != ERROR_CODE::SUCCESS) break;
```

- Every seconds, get the camera position (Translation and rotation)

```
    if (curr_timestamp.getMilliseconds() >= prev_timestamp.getMilliseconds() + 1000) {
        // Retrieve camera position
        p_zed->getPosition(cam_pose);
        sl::Translation translation = cam_pose.getTranslation();
        sl::float3 rotation_vector = cam_pose.getRotationVector();

```

- Store the camera position inside a json and call `IoTCloud::sendTelemetry` 
A label is specified as follow `sendTelemetry(std::string label, json& value)`. It allows to improve the log consultation in the ZEDHub interface as it is possible to sort them by label.

```
    // Send Telemetry
    sl_iot::json position_telemetry;
    position_telemetry["tx"] = translation.x;
    position_telemetry["ty"] = translation.y;
    position_telemetry["tz"] = translation.z;
    position_telemetry["rx"] = rotation_vector.x;
    position_telemetry["ry"] = rotation_vector.y;
    position_telemetry["rz"] = rotation_vector.z;
    IoTCloud::sendTelemetry("camera_position", position_telemetry);
    prev_timestamp = curr_timestamp;
```

- Call IoTCloud::Refresh in order to send the current image to the cloud
(See tutorial_02_live_stream_and_recording  README for more information)

```  
    // Always refresh IoT at the end of the grab loop
    IoTCloud::refresh();
    sleep_ms(1);
```
