# Examples using ZED Hub

In this repository you will find:
- [**Tutorials**](./tutorials/) that explain how to use the ZED Hub features in your apps and run them.
- [**Samples**](./samples/README.md) that provide examples of ZED Hub usage and package/deploy them on ZED Hub as a service.
- [**Scripts**](./scripts/README.md) that provide examples of ZED Hub REST API usage.

## What features are explained in these tutorials:

- **Stream video** : How to display your camera's live video feed in the ZED Hub interface with WebRTC
- **Send telemetry** : How to upload and store any kind of data in order to analyze and display it later
- **Application parameters** : How to remotely interact with your application with parameters that you can change remotely.
- **Remote functions** : How to define and call a remote function
- **Send video events** : How to send Video Events, recorded ans accessible through the interface.
- **Stream metadata** : How to send body tracking, point clouds to the cloud with WebRTC.

## Requirements
To connect your app to ZED Hub, you'll need to
- [Have a ZED Hub account](https://hub.stereolabs.com).
- [Connect your device](https://www.stereolabs.com/docs/cloud/overview/setup-device/).
- A ZED camera is recommended .

ZED Hub supports Jetson Linux and Ubuntu operating systems.

## Connect your app to ZED Hub
In the [**tutorials**](./tutorials/), you will learn how to connect a C++ or python app to ZED Hub and use its features.
In the [**samples**](./samples/), you will learn how to package your app with docker, deploy it to ZED Hub and run it through the platform on all your devices. This is the recommended workflow for production-ready environments. Check out [How to deloy an app as a service](./deploy_as_a_service.md) tutorial for more details