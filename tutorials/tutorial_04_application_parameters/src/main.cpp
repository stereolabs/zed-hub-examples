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

bool led_status_updated = false;

//Callback on led status update, it sets a boolean to true to turn off/on the led status in the main  loop.
void onLedStatusUpdate(FunctionEvent &event) {
    event.status = 0;
    led_status_updated = true;
}

int main(int argc, char **argv) {
    // Create camera object
    std::shared_ptr<sl::Camera> p_zed;
    p_zed.reset(new sl::Camera());

    //In service deployment init IoT with the SL_APPLICATION_TOKEN environment variable
    //In development you can simply init it with the application name
    const char * application_token = ::getenv("SL_APPLICATION_TOKEN");
    STATUS_CODE status_iot;
    if (!application_token) {
        status_iot = IoTCloud::init("parameter_app", p_zed);
    } else {
        status_iot = IoTCloud::init(application_token, p_zed);
    }
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initiliazation error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
    
    //Load application parameter file in development mode
    if (!application_token) {
        status_iot = IoTCloud::loadApplicationParameters("parameters.json");
        if (status_iot != STATUS_CODE::SUCCESS) {
            std::cout << "parameters.json file not found or malformated" << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    //Open the ZED camera
    sl::InitParameters initParameters;
    initParameters.camera_resolution = RESOLUTION::HD2K;
    initParameters.depth_mode = DEPTH_MODE::NONE;

    sl::ERROR_CODE status_zed = p_zed->open(initParameters);
    if (status_zed != ERROR_CODE::SUCCESS) {
        IoTCloud::log("Camera initialization error : " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    //Set your parameter callback
    CallbackParameters callback_param_led;
    callback_param_led.setParameterCallback("onLedStatusChange", "led_status", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
    IoTCloud::registerFunction(onLedStatusUpdate, callback_param_led);

    // Main loop
    while (true) {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab();
        if (status_zed != ERROR_CODE::SUCCESS) break;
        
        if (led_status_updated) {
            int curr_led_status = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS);
            bool led_status = IoTCloud::getParameter<bool>("led_status", PARAMETER_TYPE::APPLICATION, curr_led_status);
            p_zed->setCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS, led_status);
            IoTCloud::reportParameter<bool>("led_status", PARAMETER_TYPE::APPLICATION, led_status);
            led_status_updated = false;
        }

        // Insert custom code here

        // Always refresh IoT at the end of the grab loop
        IoTCloud::refresh();
    }

    // Handling camera error
    if(status_zed != ERROR_CODE::SUCCESS){
        IoTCloud::log("Grab failed, restarting camera. "+std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        p_zed->close();
        sl::ERROR_CODE e = sl::Camera::reboot(p_zed->getCameraInformation().serial_number);
    }
    //Close the camera
    else if(p_zed->isOpened())
        p_zed->close();
    
    return 0;
}
