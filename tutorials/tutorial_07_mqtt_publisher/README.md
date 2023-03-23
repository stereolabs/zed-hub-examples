# Tutorial 7 - MQTT Publisher

This tutorial shows you how to communicate between apps through ZED Hub.

## Requirements
You will deploy these tutorials on a device installed on your ZED Hub workspace. ZED Hub supports Jetson L4T and Ubuntu operating systems. If you are using a Jetson, make sure it has been flashed beforehand. If you haven't done it already, please take a look at the NVIDIA documentation to [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:
- [Sign in to ZED Hub and create a workspace](https://www.stereolabs.com/docs/cloud/overview/get-workspace/).
- [Add and setup a device](https://www.stereolabs.com/docs/cloud/overview/setup-device/).

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
./ZED_Hub_Tutorial_7
```

## What you should see after deployment

The app publishes a basic message on the MQTT topic `/v1/local_network/my_custom_data`. A log is published each time a message is sent.

## Code overview

First the app must be **initialized**. It allows to connect the app to the local broker.

```c++
    status_iot = HubClient::connect("pub_app");
    if (status_iot != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
```
Then the MQTT topic parameters are set.
```c++
    std::string topic_name = "/my_custom_data";
```

Finally a message is sent every 10 seconds
```c++
    // Main loop
    while (true)
    {
        const auto p1 = std::chrono::system_clock::now();

        json my_message_js;
        my_message_js["message"] = "Hello World";
        my_message_js["my_custom data"] = 54;
        my_message_js["timestamp"] = std::chrono::duration_cast<std::chrono::seconds>(p1.time_since_epoch()).count();

        HubClient::publishOnTopic(topic_name, my_message_js);
        HubClient::sendLog("Message published", LOG_LEVEL::INFO);

        sleep_ms(10000); // 10 seconds
    }
```
