# Tutorial 8 - MQTT Subscriber

> **NOTE**: This tutorial should be run with the tutorial 7 : **MQTT Publisher**

This tutorial shows you how to communicate between apps through ZED Hub. It subscribes to a MQTT topics and send a log to notify that the messages have been received.

[**Github repository**](https://github.com/stereolabs/zed-hub-examples/tree/main/tutorials/tutorial_08_mqtt_subscriber)

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
./ZED_Hub_Tutorial_8
```

## What you should see after deployment

The app subscribes to the MQTT topic where the MQTT Publisher Tutorial publishes: `/v1/local_network/my_custom_data`. A log is published each time a message is received.

![](./images/logs.png " ")


## Code overview
The app must be **init** to be connected to the local Broker.
The app subscribes to the topic `/v1/local_network/my_custom_data` composed of the topic prefix `/v1/local_network` and the topic name `my_custom_data`.
When a message is received the callback `onDataReceived` is triggered.

```c++
//Init sl_iot
STATUS_CODE sc = HubClient::connect(val);
if (sc != STATUS_CODE::SUCCESS) {
    HubClient::sendLog("Failed to Init Cloud", LOG_LEVEL::ERROR);
    exit(EXIT_FAILURE);
}

sc = HubClient::registerCamera(p_zed);
if (status_iot != STATUS_CODE::SUCCESS) {
    HubClient::sendLog("Failed to register the camera", LOG_LEVEL::ERROR);
    exit(EXIT_FAILURE);
}


// Topic to listen
TARGET topic_prefix = TARGET::LOCAL_NETWORK;
std::string topic_name = "/my_custom_data";

//
HubClient::subscribeToMqttTopic(topic_name, onDataReceived, topic_prefix);
```

`onDataReceived` is defined as follows. Each time a message is received, a log is sent and the message is also displayed in the runtime terminal.

```c++
void onDataReceived(std::string topic, std::string message, TARGET target, void* arg)
{
    std::cout << "Message received !" << std::endl;
    json my_raw_data = json::parse(message);
    std::cout << "My received message : " << my_raw_data << std::endl;
    HubClient::sendLog("MQTT message received on topic " + topic,LOG_LEVEL::INFO);
}
```
