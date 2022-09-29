# Tutorial 7 - MQTT Publisher

This tutorial shows you how to communicate between apps through ZED Hub.

[**Github repository**](https://github.com/stereolabs/zed-hub-examples/tree/main/tutorials/tutorial_07_mqtt_publisher)

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

The app publishes a basic message on the MQTT topic `/v1/local_network/my_custom_data`. A log is published each time a message is sent. 

## Code overview

First the app must be **Init**. It allows to connect the app to the local brocker.

```c++
    //Init sl_iot
    const char * application_token = ::getenv("SL_APPLICATION_TOKEN");
    STATUS_CODE status_iot = HubClient::connect(application_token);
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "HubClient " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    status_iot = HubClient::registerCamera(p_zed);
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Camera registration error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
```
Then the MQTT topic parameters are set.
```c++
    TARGET topic_prefix = TARGET::LOCAL_NETWORK;
    std::string topic_name = "/my_custom_data";
```

Finally a message is sent every 10 seconds
```c++
    // Main loop
    while (true) {

        const auto p1 = std::chrono::system_clock::now();

        json my_message_js;
        my_message_js["message"] = "Hello World";
        my_message_js["my_custom data"] = 54;
        my_message_js["timestamp"] = std::chrono::duration_cast<std::chrono::seconds>(p1.time_since_epoch()).count();

        HubClient::publishOnMqttTopic(topic_name, my_message_js, topic_prefix);
        sleep_ms(10000); // 10 seconds
    }
```
