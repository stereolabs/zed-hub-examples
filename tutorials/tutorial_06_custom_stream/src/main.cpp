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
    status_iot = IoTCloud::init("custom_streaming_app", p_zed);
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initiliazation error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    //Open the ZED camera
    sl::InitParameters initParameters;
    initParameters.camera_resolution = RESOLUTION::HD720;
    initParameters.depth_mode = DEPTH_MODE::ULTRA;

    sl::ERROR_CODE status_zed = p_zed->open(initParameters);
    if (status_zed != ERROR_CODE::SUCCESS) {
        IoTCloud::log("Camera initialization error : " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    //Your Mat where your custom image will be retrieved
    sl::Mat imgLeftCustom;

    // Main loop
    while (true) {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab();
        if (status_zed != ERROR_CODE::SUCCESS) break;

        // Retrieve depth image
        p_zed->retrieveImage(imgLeftCustom, sl::VIEW::DEPTH, sl::MEM::CPU);

        // Insert custom code here

        imgLeftCustom.timestamp.setMilliseconds(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count());
        // Use this function to set the current image of your live stream
        IoTCloud::setCustomVideoMat(imgLeftCustom, imgLeftCustom.timestamp.getMilliseconds());

        // Always refresh IoT at the end of the grab loop
        IoTCloud::refresh();
    }

    imgLeftCustom.free();
    IoTCloud::purgeVideoStream();

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
