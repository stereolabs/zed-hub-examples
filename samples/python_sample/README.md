# CMP app python tutorial

This repository contains simple tutorials that show you how to use some of the CMP features in a **Python app**. Note that **python is not the recommended language** to develop a CMP app. **You should prefer C++**, especialy if you want to use the CMP Video features (Live video, recordings). Many **C++ tutorials** are available and will allow you to quickly develop your first apps even if you are not familiar with this language.

## Python app limitations

Be aware of the following limitation compared to a C++ app:
- You can open and read a ZED in a python App but **you can neither send the live video to the CMP nor record the video using the CMP**. 
- You can not define **Video Events**.
- The C++ IOT library is not available in Python yet. It makes the CMP features **more difficult** to use. The available tutorials are here to show you how to use them anyway.

## Python tutorials
- **Logs and telemetry**: This tuto shows you how to use a MQTT topic to send logs and telemetry to the cloud
- **App parameters**: This tutorial shows you how to get the parameter's values defined in the CMP interface.