# Tutorial 9 - Multi-camera Stream

This tutorial shows you how to stream secondary cameras in addition to the main stream.

[**Github repository**](https://github.com/stereolabs/zed-hub-examples/tree/main/tutorials/tutorial_09_multi_cam_stream)

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
./ZED_Hub_Tutorial_9
```

## Code overview

The app retrieve all connected ZED cameras and store their `DeviceProperties` in a vector `devList`.

```c++
// Get detected cameras
std::vector<DeviceProperties> devList = Camera::getDeviceList();
int nb_detected_zed = devList.size();
```

```c++
// Thread loops for secondary streams
bool run_zeds = true;
std::vector<thread> thread_pool(nb_detected_zed - 1);
for (int z = 1; z < nb_detected_zed; z++)
{
    if (zeds[z].isOpened())
    {
        auto cam_info = zeds[z].getCameraInformation();
        thread_pool[z - 1] = std::thread(secondary_stream_loop, ref(zeds[z]), std::to_string(cam_info.serial_number), ref(run_zeds));
    }
}
```

Then, using a thread, every secondary streams are associated to a grad loop to make available the secondary stream (MJPEG).

```c++
// Secondary streams' loop to grab image
void secondary_stream_loop(Camera& zed, const std::string& stream_name, bool& run)
{
    std::cout << "Secondary stream (" << stream_name << ") opened" << std::endl;
    Mat zed_image(1280, 720, MAT_TYPE::U8_C4);

    while (run) {
        // grab current images and compute depth
        if (zed.grab() == ERROR_CODE::SUCCESS)
        {
            zed.retrieveImage(zed_image, VIEW::LEFT, MEM::CPU, zed_image.getResolution());
            auto status_code = HubClient::addSecondaryStream(stream_name, zed_image);
        }
        else
        {
            run = false;
        }
    }
}
```
