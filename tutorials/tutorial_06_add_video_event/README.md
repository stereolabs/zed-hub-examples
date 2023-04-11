# Tutorial 6 - Video Event

A **Video Event** is a **video recording** associated to a **description** stored in one or several JSON.
This application shows how to define a **Video Event**in a ZED Hub app. This event will be available in the **Video Event** ZED Hub interface.
In this tutorial a video is considered as event if **at least one person is detected** in the image. To detect people the **Object Detection** module of the SDK will be used. 

![](./images/event_detected_people.png " ")


## Requirements
You will deploy these tutorials on a device installed on your ZED Hub workspace. ZED Hub supports Jetson L4T and Ubuntu operating systems. If you are using a Jetson, make sure it has been flashed beforehand. If you haven't done it already, please take a look at the NVIDIA documentation to [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:
- [Sign in to ZED Hub and create a workspace](https://www.stereolabs.com/docs/cloud/overview/get-workspace/).
- [Add and setup a device](https://www.stereolabs.com/docs/cloud/overview/setup-device/).
- A ZED must be plugged to this device.
- **Enable recordings** and **disable privacy mode** in the Settings panel of your device

This tutorial needs Edge Agent. By default when your device is setup, Edge Agent is running on your device.

You can start it using this command :
```
$ edge_cli start
```

> **Note**: It is already running by default after Edge Agent installation.

And to stop it :
```
$ edge_cli stop
```

## Build and deploy this tutorial

### How to build your application (for development)

With Edge Agent installed and running, you can build this tutorial with the following commands :
```
$ cd sources
$ mkdir build
$ cd build
$ cmake ..
$ make -j$(nproc)
```

Then run your app :
```
./ZED_Hub_Tutorial_6
```

## What you should see after deployment
Make sure that the recordings are enabled and that the privacy mode is disabled (Settings panel of your device, in the ZED Hub interface).
As each time a ZED is opened, you will find the **live stream** and the **recordings** in the **Video Panel** of your device as soon as your app is **running**.

A video is considered an event if **at least on person is detected** in the image. Therefore if your app is running and that someone is seen by your ZED, you should see an **Event** in the **Video Event panel** corresponding to this situation.

![](./images/event_detected_people.png " ")

You can click on it. You have access to the video and the stored data of the event. You have access to a longer video than the exact event duration (you can watch a few seconds before and after the event). The blue line indicates which part of the video is associated to the event.

![](./images/event_visualisation.png " ")


## Code overview - C++

### Initialization
As usual, the app is init with `HubClient::connect` and `HubClient::registerCamera` and the ZED is started with  the ZED SDK `open` function.
The **Object detection** is enabled with `enableObjectDetection`.Note that the tracking is required to use it (`enablePositionalTracking` must be called).

```c++
    sl::ObjectDetectionParameters obj_det_params;
    obj_det_params.image_sync = true;
    obj_det_params.enable_tracking = false;
    obj_det_params.detection_model = sl::OBJECT_DETECTION_MODEL::MULTI_CLASS_BOX_FAST;
    zed_error = p_zed->enableObjectDetection(obj_det_params);
```

The detection is limited to PERSON (meaning for instance that the Vehicles are ignored), the detection threshold is set to 50:

```c++
    ObjectDetectionRuntimeParameters objectTracker_parameters_rt;
    objectTracker_parameters_rt.detection_confidence_threshold = 50;
    objectTracker_parameters_rt.object_class_filter.clear();
    objectTracker_parameters_rt.object_class_filter.push_back(sl::OBJECT_CLASS::PERSON);
```


### Main loop

Each time a frame is successfully **grabbed**, the detected object are retrieved with the `retrieveObjects` function and stored in `objects`.

Remember that the frame is part of an event as soon as **at least one person is detected**. However a **second rule** is necessary to **distinguish one event from an other**. Once again, this rule depends on how you define it. In this tutorial we decided to define a new event as soon as **no one has been seen for 10 frames**. 

A frame is defined as part of a videoEvent if the `HubClient::startVideoEvent` is called with the **corresponding timestamp**.
> **Note**: You should not define a new Video event each time you call `HubClient::addVideoEvent` but you should extend the current one by calling `HubClient::updateVideoEvent` by using the same `event.reference`.

```c++
    EventParameters event_params;
    event_params.timestamp = current_ts.getMilliseconds();
    event_params.reference = event_reference;
    std::string event_label = "People Detection"; // or label of your choice
    json event2send;                              // Use to store all the data associated to the video event.
    event2send["message"] = "Current event as reference " + event_reference;
    event2send["nb_detected_person"] = objects.object_list.size();

    if (new_event || !first_event_sent)
    {
        HubClient::startVideoEvent(p_zed, event_label, event2send, event_params);
        first_event_sent = true;
        std::cout << "Event started" << std::endl;
    }
    else
    {
        HubClient::updateVideoEvent(p_zed, event_label, event2send, event_params);
        std::cout << "Event updated" << std::endl;
    }
```