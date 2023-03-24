# ZED Hub Samples

In addition to the **ZED Hub tutorials**, some sample apps are available.

- [**Camera Viewer Sample**](/samples/camera_viewer_sample/README.md) corresponds to the app "Camera Viewer" available on each device. The source code is available and explained here.
It consists in:
    - A basic setup of the camera
    - A video stream
    - Callbacks that allow to modify video parameters of the camera (exposure, gamma, etc.)

- [**Object Detection Sample**](/samples/object_detection_sample/README.md) demonstrates what can be done very simple with object detection. It consists in:
    - A object detection setup of the camera
    - A custom video streamed where we highlight detected person with ```opencv```
    - Callbacks that enables / disables a few parameter : highlighting, events, telemetry, etc.

- [**GNSS Tracker Sample**](/samples/gnss_tracker_sample/README.md) show how to send GNSS data to the **Maps page** with a random walk. It consists in:
    - A basic setup of the camera
    - A video stream
    - WebRTC messages simulating a random walk
    - Callbacks that determine the data sending frequency and that retrieve waypoints

- [**Multiplatform Sample**](/samples/multiplatform_sample/README.md) shows how to create an app that can be deploy on every platform.