# Tutorial 5 - Remote Function Calls

This tutorial shows how to make an application containing a **remote function** that computes an addition called by a **remote function call**.
This tutorial does not require a ZED to be runned.

[**Github repository**](https://github.com/stereolabs/cmp-examples/tree/main/tutorials/tutorial_05_remote_function_calls)

#### What is a remote function call ?
A **remote function call** is a call to a remote function **declared and register by a CMP app**. The app described in this tutorial declares and registers the `additionCallback` remote function. 
The call to this function can be done from **any computer** connected to the internet, by using a **REST request**. The way to perform this request is explained later in this tutorial.


## Requirements
You will deploy this tutorial on one of the devices installed on **your CMP workspace**. The CMP supports Jetson Nano, TX2 and Xavier or any computer. If you are using a Jetson, make sure it has been flashed. If you haven't done it already, [flash your Jetson](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html).

To be able to run this tutorial:
- [Sign In the CMP and created a workspace](https://www.stereolabs.com/docs/cloud/overview/get-started/).
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
The application in itself only define and register a **callback function** that can be called from anywhere if the app is running. Therefore there is not a lot to see in the CMP interface. Make simply sure that your application has a **building** and finaly a **running status**.  

### Call your remote function
Before calling your remote function, you have to get the necessary values to use the REST API.

- Your **API token** that you can register from the **API panel** in CMP. Get more informations in the [REST API documenation](https://www.stereolabs.com/docs/cloud/rest-api/)

- Your **region url** that you can get using the REST API in the ```/workspaces``` endpoint. Get more informations in the [REST API documenation](https://www.stereolabs.com/docs/cloud/rest-api/workspaces/)

Exemple:
```
$ curl -s -H "Content-Type:application/json" -H "Authorization:Bearer ${your_token}" -X GET https://cloud.stereolabs.com/api/v1/workspaces

```

- Your **workspace id** that you can get using the REST API in the ```/workspaces``` endpoint. Get more informations in the [REST API documenation](https://www.stereolabs.com/docs/cloud/rest-api/workspaces/)


- Your **device id** that you can get using the REST API in the ```/workspaces/$workspace_id/devices``` endpoint. Get more informations in the [REST API documentation](https://www.stereolabs.com/docs/cloud/rest-api/devices/)


To call your remote function, simply use the script ```remote_function_call.sh``` that contains a REST request using curl with the given arguments with num1 and num2 as the numbers you want to use in your addition :

```
./remote_function_call.sh $num1 $num2 $region_url $workspace_id $device_id $access_token
```

The REST request uses this format :\
It uses the endpoint ```${region_url}/workspaces/${workspace_id}/devices/${device_id}/functions/${function_name}``` where ```function_name``` is the name of the function you registered in your application using the ```IoTCloud::registerFunction```. In this tutorial the function registered is `tuto05_add` .\
The `parameters` key of the json contained in the request contains the parameters of the function. In our case `num1` and `num2`.

```
    curl -s -H "Content-Type: application/json" \
       -H "Authorization: Bearer ${access_token}"\
       -X POST ${region_url}/workspaces/${workspace_id}/devices/${device_id}/functions/tuto05_add \
       -d "{ \
       \"parameters\": { \
         \"num1\": ${num1}, \
	 \"num2\": ${num2} \
         }\
       }"
```

You can get more informations about remote function calls in the [documentation](https://www.stereolabs.com/docs/cloud/remote-functions/call/).


## Code Overview

In the C++ code, the app is connected to the cloud by using `IoTCloud::init`, as always.

### Register your callback function
Then your remote function parameters are set. Basicly a name is given, `tuto05_add`, and the callback type is set.
Note that the callback type can be:

- CALLBACK_TYPE::ON_REMOTE_CALL

- CALLBACK_TYPE::ON_RESTART_CALL

Then the remote function is register: the function `additionCallback` associated to the `callback_params` is registered by the cloud.

```c++
    CallbackParameters callback_params;
    callback_params.setRemoteCallback("tuto05_add", CALLBACK_TYPE::ON_REMOTE_CALL, nullptr);
    //Register your callback function
    IoTCloud::registerFunction(additionCallback, callback_params);
```


### Define your callback function

A remote function must have this minimum structure:

```c++
void myRemoteFunction(FunctionEvent& event) {
    sl_iot::json params = event.getEvenParameters();

    // TODO : your custom code
    bool success = true;
    if (success){
        event.status = 0;
        event.result = result;
    }
    else{
        event.status = 1;
        event.result = "Error message";
    }
}

```

The `getEvenParameters` function get the `parameters` json that as been field in the REST request that called the remote function.
In our case params contains this json (5 and 10 are given as exemple):
```
{
    "num1": 5, 
	"num2": 10 
}
```

Then the remote function can use these parameters to do anything. In our case the 2 input values are added after making sure they are contained in `params`. The result is stored in `event.result` and the status `event.status` is set to 0 to notify that the function performed as expected.

```c++
    if (params.find("num1") != params.end() && params["num1"].is_number_integer() &&
	params.find("num2") != params.end() && params["num2"].is_number_integer()) {
        int num1 = params["num1"].get<int>();
        int num2 = params["num2"].get<int>();
        int result = num1 + num2;

	    //Log your result
        IoTCloud::log("Addition called : "+std::to_string(num1)+" + "+std::to_string(num2)+" = "+std::to_string(result),LOG_LEVEL::INFO);

        //Update the result and status of the event
        event.status = 0;
        event.result = result;

```

In case of problem the status is set to 1.
```c++
    IoTCloud::log("Addition remote function was used with wrong arguments.",LOG_LEVEL::ERROR);
    event.status = 1;
    event.result = "Addition remote function was used with wrong arguments.";
    
}
```

So we finaly have the following remote function:

```c++
void additionCallback(FunctionEvent& event) {
    //Get the parameters of the remote function call
    sl_iot::json params = event.getEvenParameters();
    //Check if parameters are present and valid
    if (params.find("num1") != params.end() && params["num1"].is_number_integer() &&
	params.find("num2") != params.end() && params["num2"].is_number_integer()) {
        int num1 = params["num1"].get<int>();
        int num2 = params["num2"].get<int>();
        int result = num1 + num2;

        //Log your result
        IoTCloud::log("Addition called : "+std::to_string(num1)+" + "+std::to_string(num2)+" = "+std::to_string(result),LOG_LEVEL::INFO);

        //Update the result and status of the event
        event.status = 0;
        event.result = result;
    } 
    else {
        IoTCloud::log("Addition remote function was used with wrong arguments.",LOG_LEVEL::ERROR);
        event.status = 1;
        event.result = "Addition remote function was used with wrong arguments.";
    }
}
```
