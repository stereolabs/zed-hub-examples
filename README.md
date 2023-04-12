# ZED Hub

ZED Hub is a module that allows your application based on ZED SDK to connect to the cloud.

## Overview

<table>
  <tbody>
    <tr>
      <td align="center"><b>Applications management</b></td>
      <td align="center"><b>Live WebRTC stream</b></td>
      <td align="center"><b>Devices monitoring</b></td>
    </tr>
    <tr></tr>
    <tr>
      <td align="center"><img alt="Applications management" src="https://user-images.githubusercontent.com/101094358/231520425-f4634ef2-b3a5-4638-a1d1-7cc9a1afed7f.gif"></a></td>
      <td align="center"><img alt="Live WebRTC Stream" src="https://user-images.githubusercontent.com/101094358/231516124-cf1d21d0-be53-4d12-88db-b622cc0f7a5f.gif"></a></td>      
      <td align="center"><img alt="Devices monitoring" src="https://user-images.githubusercontent.com/101094358/231521084-9f226479-3a01-4506-a3c2-78b572087d82.gif"></a></td>       
    </tr>
    <tr></tr>
    <tr>
      <td align="center"><b>System Metrics</b></td>
      <td align="center"><b>Telemetry</b></td>
      <td align="center"><b>Events</b></td>
    </tr>
    <tr>
      <td align="center"><img alt="System metrics" src="https://user-images.githubusercontent.com/101094358/231516885-b9f09aac-6b80-4a4d-9721-25a08e1b0397.gif"></a></td>
        <td align="center"><img alt="Telemetry" src="https://user-images.githubusercontent.com/101094358/231509333-2a17c7bf-5d4e-47d1-8961-a78d8f280af6.gif"></a></td>
      <td align="center"><img alt="Events" src="https://user-images.githubusercontent.com/101094358/231516332-d62989b9-61b7-4afc-8c31-91010cbd0133.gif"></a></td>
    </tr>
  <tbody>
</table>

In this repository you will find:
- [**Tutorials**](./tutorials/) that explain how to connect any app to ZED Hub and use the main features.
- [**Samples**](./samples/README.md) that provide complete examples of production-ready applications. You can have more details about [How to deploy an app as a service](./deploy_as_a_service.md) for production environments.
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