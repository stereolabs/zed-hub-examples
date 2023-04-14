# Tutorial 4 - Application Parameters

This tutorial shows how to use custom device and application parameters in your application. These parameters can be modified by everyone in the ZED Hub interface.
This sample starts a ZED exactly as [tutorial_02_live_stream_and_recording](/tutorials/tutorial_02_live_stream_and_recording/README.md) does, but it also define one parameter. The first one indicates whether the camera LED must be on or off.

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

## Build and run this tutorial for development

With Edge Agent installed and running, you can build this tutorial with the following commands :
```
$ mkdir build
$ cd build
$ cmake ..
$ make -j$(nproc)
```

This application use application parameters. Move the `parameters.json` file to the path you specified in the `HubClient::loadApplicationParameters` function.
```
$ cp ../parameters.json .
```

Then to run your app :
```
./ZED_Hub_Tutorial_4
```

To dynamically change the application parameters and activate callbacks, edit the `parameters.json` file.

## Code overview

Here are the elements you have to add to your code when you want to define a new device / application parameters:

- Add the application parameter to the `app.json` file. If not done, the parameter won't be available in the ZED Hub interface.

- Associate a callback function to the parameter. Thanks to that the callback is triggered when the parameter value is modified in the interface. It is a way to notifier a parameter's value modification.

- Write the callback. On parameter's value modification you can do whatever you want

- Use the parameter to do something. In our case we modify the LED status using the SDK API.

Lets detail these steps:

### Associate the parameter to a callback

The application parameters are defined in the `parameters.json` and associated to a default value. When this value is modified in the interface you are so far not notified of this modification in your app (even if the new value is available). To be notified of a parameter modification, you need to associate your parameter to a callback in your C++ code.

In our case we want:
- the `app_param` application parameter in the `parameters.json` file to be associated with the `onAppParamUpdate` callback function
- the `led_status` device parameter set in the **Device Parameters Panel** to be associated with the `onLedStatusChange` callback function.

We can do this in three steps:

- load the application parameters file to the callback with `loadApplicationParameters`.

> **Note**: This is only needed for development. When you will deploy your app as a service, you'll need to put those parameters in your `app.json`. Please have a look to the sample **Camera Viewer sample** and **Object Detection sample** to understand how it works:

```c++
    // Load application parameter file in development mode
    char *application_token = getenv("SL_APPLICATION_TOKEN");
    if (!application_token)
    {
        status_hub = HubClient::loadApplicationParameters("parameters.json");
        if (status_hub != STATUS_CODE::SUCCESS)
        {
            std::cout << "parameters.json file not found or malformated"
                      << std::endl;
            exit(EXIT_FAILURE);
        }
    }
```

- associate the parameter to the callback with `setParameterCallback`:

```c++
    CallbackParameters callback_param_led;
    callback_param_led.setParameterCallback("onLedStatusChange", "led_status", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
    
    ...

    CallbackParameters callback_app_param;
    callback_app_param.setParameterCallback("onAppParamUpdate", "app_param", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
```

- declare this association to the cloud :

```c++
    HubClient::registerFunction(onLedStatusUpdate, callback_param_led);
    ...
    HubClient::registerFunction(onAppParamUpdate, callback_app_param);
```

So we finally have:
```c++
    // Set your parameter callback
    CallbackParameters callback_param_led;
    callback_param_led.setParameterCallback("onLedStatusChange", "led_status", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
    HubClient::registerFunction(onLedStatusUpdate, callback_param_led);

    CallbackParameters callback_app_param;
    callback_app_param.setParameterCallback("onAppParamUpdate", "app_param", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
    HubClient::registerFunction(onAppParamUpdate, callback_app_param);
```

### Add a callback function

Your parameters have been associated to callbacks but these callbacks needs to be written.
A parameter callback must at least have the following structure:
```c++
void myCallbackName(FunctionEvent &event)
{
    event.status = 0;

    // TODO
}
```
It can contains everything, but keep in mind that it is called each time the associated parameter is modified. You can of course get the new parameter value inside the callback by using the `HubClient::getParameter` function.

In our case we only store the fact that the parameter has been modified inside the `led_status_updated` global variable.

```c++
bool led_status_updated = true;
string app_param = "";

// Callback on led status update, it sets a boolean to true to turn off/on the led status in the main loop.
void onLedStatusUpdate(FunctionEvent &event)
{
    event.status = 0;
    led_status_updated = true;
    std::cout << "Led Status updated !" << std::endl;
}

// Callback on app_param update, it log its new value
void onAppParamUpdate(FunctionEvent &event)
{
    event.status = 0;
    app_param = HubClient::getParameter<std::string>("app_param", PARAMETER_TYPE::APPLICATION, app_param);
    std::cout << "App Param updated: " << app_param << std::endl;
}
```

> **Note**: The callbacks name `onLedStatusUpdate` and `onAppParamUpdate` must correspond to the first parameter of their corresponding `setParameterCallback` functions.

```c++
    CallbackParameters callback_param_led;
    callback_param_led.setParameterCallback("onLedStatusChange", "led_status", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);

    ...
    
    CallbackParameters callback_app_param;
    callback_app_param.setParameterCallback("onAppParamUpdate", "app_param", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
```

### Use the updated parameter value

Your parameters are now totally integrated in the application and can be used for any purpose. In our case we wait for a modification of its value to do something: when the parameter is modified in the user interface, the callbacks are triggered. The new value is therefore accessible by calling `HubClient::getParameter`.

One callback also set `led_status_updated` to `True` and the other one print the value of `app_param`.

In the main loop of the application:
- The current led status is retrieved from the **Camera Settings** in order to use it as default value.
- The new parameter value is retrieved thanks to `HubClient::getParameter`
    > **Note**: `curr_led_status` is used as default value in the case where `getParameter` fails.
    ```c++
        bool led_status = HubClient::getParameter<bool>("led_status", PARAMETER_TYPE::DEVICE, curr_led_status);
    ```

- Then the LED status is physically modified by calling the SDK function `setCameraSettings`.
- A log is set to the cloud to notify the parameter value that has been used with the function `HubClient::reportParameter`.

    ```c++
        if (led_status_updated)
        {
            int curr_led_status = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS);
            bool led_status = HubClient::getParameter<bool>("led_status", PARAMETER_TYPE::DEVICE, curr_led_status);
            p_zed->setCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS, led_status);
            HubClient::reportParameter<bool>("led_status", PARAMETER_TYPE::DEVICE, led_status);
            led_status_updated = false;
        }
    ```


Finally with these four steps we easily added a parameter to the initial application [tutorial_02_live_stream_and_recording](/tutorials/tutorial_02_live_stream_and_recording/README.md) and we used its values.


## Next steps

Note that the parameters panel can be quite complex. Please have a look at the sample **Camera Viewer sample** and **Object Detection sample** to understand how it works.


