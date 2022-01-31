#include <stdio.h>
#include <string.h>
#include <chrono>

#include <sl/Camera.hpp>
#include <sl_iot/IoTCloud.hpp>
#include <csignal>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;


int main(int argc, char **argv) {
    // Create camera object
    std::shared_ptr<sl::Camera> p_zed;
    p_zed.reset(new sl::Camera());

    STATUS_CODE status_iot;
    status_iot = IoTCloud::init("telemetry_app", p_zed);
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initiliazation error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
    
    //Open the ZED camera
    sl::InitParameters initParameters;
    initParameters.camera_resolution = RESOLUTION::HD2K;

    sl::ERROR_CODE status_zed = p_zed->open(initParameters);
    if (status_zed != ERROR_CODE::SUCCESS) {
        IoTCloud::log("Camera initialization error : " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    //Enable Positional Tracking
    PositionalTrackingParameters positional_tracking_param;
    positional_tracking_param.enable_area_memory = true;
    status_zed = p_zed->enablePositionalTracking(positional_tracking_param);
    if (status_zed != ERROR_CODE::SUCCESS) {
        IoTCloud::log("Enabling positional tracking failed : " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    sl::Pose cam_pose;
    sl::RuntimeParameters runtime_parameters;
    runtime_parameters.measure3D_reference_frame = sl::REFERENCE_FRAME::WORLD;
    sl::Timestamp prev_timestamp = 0;
    // Main loop
    while (true) {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab(runtime_parameters);
        if (status_zed != ERROR_CODE::SUCCESS) break;

        sl::Timestamp curr_timestamp = p_zed->getTimestamp(sl::TIME_REFERENCE::IMAGE);
        if (curr_timestamp.getMilliseconds() >= prev_timestamp.getMilliseconds() + 1000) {
            // Retrieve camera position
            p_zed->getPosition(cam_pose);
            sl::Translation translation = cam_pose.getTranslation();
            sl::float3 rotation_vector = cam_pose.getRotationVector();

            // Send Telemetry
            sl_iot::json position_telemetry;
            position_telemetry["tx"] = translation.x;
            position_telemetry["ty"] = translation.y;
            position_telemetry["tz"] = translation.z;
            position_telemetry["rx"] = rotation_vector.x;
            position_telemetry["ry"] = rotation_vector.y;
            position_telemetry["rz"] = rotation_vector.z;
            IoTCloud::sendTelemetry("camera_position", position_telemetry);
            prev_timestamp = curr_timestamp;
        }

        // Insert custom code here

        // Always refresh IoT at the end of the grab loop
        IoTCloud::refresh();
        sleep_ms(1);
    }

    p_zed->disablePositionalTracking();
    // Handling camera error
    if(status_zed != ERROR_CODE::SUCCESS){
        IoTCloud::log("Grab failed, restarting camera. "+std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        p_zed->close();
        sl::ERROR_CODE e = sl::Camera::reboot(p_zed->getCameraInformation().serial_number);
    }
    //Close the camera
    else if(p_zed->isOpened())
        p_zed->close();
    
    status_iot = IoTCloud::stop();
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Terminating error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
    return 0;
}
