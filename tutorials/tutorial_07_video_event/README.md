# Tutorial 7 - Video Event

A **video event** is **Video recording** associated to a **description** stored in one or several json.
This application shows how to define a Video Event in a ZEDHub app. This event will be available in the Video Event ZEDHub interface.
In this tutorial a video is concidered as event if **at least on person is detected** in the image. To detect people the **Object Detection** module of the SDK will be used. 

[**Github repository**](https://github.com/stereolabs/cmp-examples/tree/main/tutorials/tutorial_07_video_event)

![](./images/event_detected_people.png " ")


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

## Build and deploy this tutorial

### How to build your application (for development)

Run the Edge Agent installed on your device using (note that it's already running by default after Edge Agent installation) :
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

Then to run your app :
```
./app_executable
```

## What you should see after deployment
Make sure that the recordings are enable and that the privacy mode is disabled (Settings panel of your device, in the ZEDHub interface).
As each time a ZED is opened, you will find the **live stream** and the **recordings** in the **Video Panel** of your device as soon as your app is **running**.

A video is concidered as event if **at least on person is detected** in the image. Therefore if your app is running and that someone is seen by your ZED, you should see an Event in the Video Event panel corresponding to this situation.

![](./images/event_detected_people.png " ")

You can click on it. You have access the video and the stored data of the event. You have access to a longer video than the exact event duration ( you can watch a few seconds before and after the event). The blue line indicates which part of the video is associated to the event.

![](./images/event_visualisation.png " ")


## Code overview

### Initialisation
As usual, the app is init with `IoTCloud::init` and the ZED is started with  the ZED SDK `open` function.
The Object detection is enabled with `enableObjectDetection`.Note that the tracking is required to use it (`enablePositionalTracking` must be called).

```c++
    sl::ObjectDetectionParameters obj_det_params;
    obj_det_params.image_sync = true;
    obj_det_params.enable_tracking = true;
    obj_det_params.detection_model =  sl::DETECTION_MODEL::MULTI_CLASS_BOX;
    auto zed_error = p_zed->enableObjectDetection(obj_det_params);
```

The detection is limited to PERSONN (meaning that the Vehicles for instance are ignore), the detection threshold is set to 50:

```c++
    // Object Detection runtime parameters : detect person only
    ObjectDetectionRuntimeParameters objectTracker_parameters_rt;
    objectTracker_parameters_rt.detection_confidence_threshold = 50;
    objectTracker_parameters_rt.object_class_filter.clear();
    objectTracker_parameters_rt.object_class_filter.push_back(sl::OBJECT_CLASS::PERSON);
```


### Main loop

Each time a frame is successfuly **grabbed**, the detected object are retrieve with the `retrieveObjects` function and strored in `objects`.

Remember that the frame is part of an event as soon as **at least one person is detected**. However a **second rule** is necessary to **distinguish one event from an other**. Once again, this rule depends on your wishes. In this tutorial we decided to define a new event as soon as **no one has been seen for 10 frames**. 

A frame is defined as part of a videoEvent if the `IoTCloud::startVideoEvent` is called with the **corresponding timestamp**.
** Note** that you do not define a new Video event each time you call `IoTCloud::addVideoEvent` but you extend the current one by calling `IoTCloud::updateVideoEvent` by using the same `event.reference`.

```c++
    EventParameters event_params;
    event_params.timestamp = current_ts.getMilliseconds();
    event_params.reference = event_reference;    
    std::string event_label = "People Detection"; // or label of your choice
    json event2send; // Use to store all the data associated to the video event. 
    event2send["message"] = "Current event as reference " + event_reference;
    event2send["nb_detected_personn"] = objects.object_list.size();

    if (new_event)
        IoTCloud::startVideoEvent(event_label, event2send, event_params);
    else
        IoTCloud::updateVideoEvent(event_label, event2send, event_params);


```