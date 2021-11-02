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

float grab_fps = 0;
std::shared_ptr<sl::Camera> p_zed;
sl::InitParameters initParameters;

std::mutex sdk_guard;
bool run = true;
bool full_run = true;
bool local_stream_change = false;

///
/// \brief Callback generated when init parameters have been changed on the cloud interface
/// \param event from FunctionEvent
///
void onInitParamUpdate(FunctionEvent &event) {
    event.status = 0;
    IoTCloud::log("Init Parameters Update. Re-opening the camera.",LOG_LEVEL::INFO);
    run=false;
}

///
/// \brief Callback generated when LED status has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onLedStatusUpdate(FunctionEvent &event) {
    event.status = 0;
    sdk_guard.lock();
    int curr_led_status = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS);
    bool led_status = IoTCloud::getParameter<bool>("led_status", PARAMETER_TYPE::DEVICE, curr_led_status);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS, led_status);
    sdk_guard.unlock();
    IoTCloud::reportParameter<bool>("led_status", PARAMETER_TYPE::DEVICE, led_status);
}

///
/// \brief Callback generated when GAMMA video settings has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onGammaUpdate(FunctionEvent &event) {
    event.status = 0;
    sdk_guard.lock();
    int curr_gamma = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::GAMMA);
    int gamma = IoTCloud::getParameter<int>("camera_gamma", PARAMETER_TYPE::DEVICE, curr_gamma);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::GAMMA, gamma);
    sdk_guard.unlock();
    IoTCloud::purgeVideoStream();
    IoTCloud::reportParameter<int>("camera_gamma", PARAMETER_TYPE::DEVICE, gamma);
}

///
/// \brief Callback generated when GAMMA video settings has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onGainUpdate(FunctionEvent &event) {
    event.status = 0;
    sdk_guard.lock();
    int curr_gain = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::GAIN);
    int gain = IoTCloud::getParameter<int>("camera_gain", PARAMETER_TYPE::DEVICE, curr_gain);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::GAIN, gain);
    sdk_guard.unlock();
    IoTCloud::purgeVideoStream();
    IoTCloud::reportParameter<int>("camera_gain", PARAMETER_TYPE::DEVICE, gain);
}

///
/// \brief Callback generated when AEC/AGC video settings has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onAutoExposureUpdate(FunctionEvent &event) {
    event.status = 0;
    sdk_guard.lock();
    int curr_auto_exposure = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::AEC_AGC);
    bool auto_exposure = IoTCloud::getParameter<bool>("camera_auto_exposure", PARAMETER_TYPE::DEVICE, curr_auto_exposure);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::AEC_AGC, auto_exposure);
    sdk_guard.unlock();
    IoTCloud::purgeVideoStream();
    IoTCloud::reportParameter<bool>("camera_auto_exposure", PARAMETER_TYPE::DEVICE, auto_exposure);
}

///
/// \brief Callback generated when Exposure video settings has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onExposureUpdate(FunctionEvent &event) {
    event.status = 0;
    sdk_guard.lock();
    int curr_exposure = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::EXPOSURE);
    int exposure = IoTCloud::getParameter<int>("camera_exposure", PARAMETER_TYPE::DEVICE, curr_exposure);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS, exposure);
    sdk_guard.unlock();
    IoTCloud::purgeVideoStream();
    IoTCloud::reportParameter<int>("camera_exposure", PARAMETER_TYPE::DEVICE, exposure);
}


///
/// \brief Callback generated when the ap parameter local_stream has been modified in the interface.
/// the stream mode of the zed is enabled or disabled depending on the value
/// \param event from FunctionEvent
///
void onLocalStreamUpdate(FunctionEvent &event) {
    event.status = 0;
    local_stream_change = true;
    bool local_stream = IoTCloud::getParameter<bool>("local_stream", PARAMETER_TYPE::APPLICATION, false);

    if (local_stream){

        StreamingParameters stream_param;
        stream_param.codec = sl::STREAMING_CODEC::H264;

        //restart streaming with new parameters
        p_zed->disableStreaming();
        auto zed_error = p_zed->enableStreaming(stream_param);
        if (zed_error != ERROR_CODE::SUCCESS) {
            std::cout << "[onAppStreamParamUpdate] "<<sl::toVerbose(zed_error) << "\nExit program." << std::endl;
            p_zed->close();
            exit(EXIT_FAILURE);
        }
    }
    else{
        p_zed->disableStreaming();
    }
}

void applyInitParameters(sl::InitParameters &parameters) {
    std::string reso_str = IoTCloud::getParameter<std::string>("camera_resolution", PARAMETER_TYPE::DEVICE, sl::toString(parameters.camera_resolution).c_str());
    if (reso_str == "HD2K")
        parameters.camera_resolution = RESOLUTION::HD2K;
    else if (reso_str == "HD720")
        parameters.camera_resolution = RESOLUTION::HD720;
    else if (reso_str == "HD1080")
        parameters.camera_resolution = RESOLUTION::HD1080;
    else if (reso_str == "WVGA")
        parameters.camera_resolution = RESOLUTION::VGA;
    
    IoTCloud::reportParameter<std::string>("camera_resolution", PARAMETER_TYPE::DEVICE, reso_str);

    parameters.camera_image_flip = IoTCloud::getParameter<int>("camera_image_flip", PARAMETER_TYPE::DEVICE, (int)parameters.camera_image_flip);
    IoTCloud::reportParameter<int>("camera_image_flip", PARAMETER_TYPE::DEVICE, (int)parameters.camera_image_flip);

    parameters.camera_fps = IoTCloud::getParameter<int>("camera_fps", PARAMETER_TYPE::DEVICE, parameters.camera_fps);
    IoTCloud::reportParameter<int>("camera_fps", PARAMETER_TYPE::DEVICE, (int)parameters.camera_fps);
}

void main_loop() {

    // Get Init Parameters from cloud parameters
    applyInitParameters(initParameters);
    // Override parameters
    initParameters.sdk_verbose = true;
    initParameters.sensors_required = true;

    // Open init parameters
    sl::ERROR_CODE errZed = p_zed->open(initParameters);
    if (errZed != ERROR_CODE::SUCCESS) {
        IoTCloud::log("Camera initialization error : " + std::string(toString(errZed)), LOG_LEVEL::ERROR);
        full_run = false;
        exit(EXIT_FAILURE);
    }

    // Setup callback for parameters
    if (run) {
        CallbackParameters callback_param;
        callback_param.setParameterCallback("onParamChange", "camera_resolution|camera_fps|camera_image_flip" ,CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
        IoTCloud::registerFunction(onInitParamUpdate, callback_param);

        CallbackParameters callback_param_led;
        callback_param_led.setParameterCallback("onLedStatusChange", "led_status" ,CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
        IoTCloud::registerFunction(onLedStatusUpdate, callback_param_led);

        CallbackParameters callback_param_auto_exposure;
        callback_param_auto_exposure.setParameterCallback("onAutoExposureChange", "camera_auto_exposure" ,CALLBACK_TYPE::ON_PARAMETER_UPDATE,PARAMETER_TYPE::DEVICE);
        IoTCloud::registerFunction(onAutoExposureUpdate, callback_param_auto_exposure);

        CallbackParameters callback_param_exposure;
        callback_param_exposure.setParameterCallback("onExposureChange", "camera_exposure" ,CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
        IoTCloud::registerFunction(onExposureUpdate, callback_param_exposure);

        CallbackParameters callback_param_gain;
        callback_param_gain.setParameterCallback("onGainChange", "camera_gain" ,CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
        IoTCloud::registerFunction(onGainUpdate, callback_param_exposure);

        CallbackParameters callback_param_gamma;
        callback_param_gamma.setParameterCallback("onGammaChange", "camera_gamma" ,CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
        IoTCloud::registerFunction(onGammaUpdate, callback_param_gamma);

        CallbackParameters callback_param_stream;
        callback_param_stream.setParameterCallback("onLocalStreamChange", "local_stream" ,CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
        IoTCloud::registerFunction(onLocalStreamUpdate, callback_param_stream);

    }

    bool local_stream = IoTCloud::getParameter<bool>("local_stream", PARAMETER_TYPE::APPLICATION, false);
    if (local_stream) {
        StreamingParameters stream_param;
        stream_param.codec = sl::STREAMING_CODEC::H264;
        p_zed->enableStreaming(stream_param);
    }

    IoTCloud::reportParameter<bool>("local_stream", PARAMETER_TYPE::APPLICATION, local_stream);
    run = true;
    int frame = 0;
    int grab_fps_warning_state = 0;
    long long timestamp_warning_grab_fps = 0;
    unsigned long long last_ts = 0;
    unsigned long long curr_ts = 0;
    while (run) {
        sdk_guard.lock();
        auto err = p_zed->grab();
        sdk_guard.unlock();
        if (err == ERROR_CODE::SUCCESS) {
            grab_fps = p_zed->getCurrentFPS();
            //Detect fps warning
            if (frame > 40) {
                if (grab_fps <= 5) {
                    switch(grab_fps_warning_state){
                    case 0:
                        timestamp_warning_grab_fps = p_zed->getTimestamp(sl::TIME_REFERENCE::CURRENT).getMilliseconds();
                        grab_fps_warning_state=1;
                        break;
                    case 1:
                        if (p_zed->getTimestamp(sl::TIME_REFERENCE::CURRENT).getMilliseconds()-timestamp_warning_grab_fps>5*1000) { //warning if too low during at least 5 seconds
                            IoTCloud::log("Grab fps low " + to_string((int)grab_fps), LOG_LEVEL::WARNING);
                            grab_fps_warning_state=2;
                        }
                        break;
                    default:
                        break;
                    }
                } else grab_fps_warning_state = 0;
            }
            IoTCloud::refresh();
        } else {
            std::string error_str = sl::toString(err).c_str();
            int size_devices = sl::Camera::getDeviceList().size();
            IoTCloud::log("Camera grab error: "+error_str+". ( Number of camera detected : "+ to_string(size_devices) + " ) ", LOG_LEVEL::ERROR);
            if (p_zed->isOpened())
                p_zed->close();

            run = false;
            full_run = false;
        }
    }
    if (p_zed->isOpened())
        p_zed->close();

}

int main(int argc, char **argv) {
    //Create ZED Object
    p_zed.reset(new sl::Camera());
    
    STATUS_CODE status_iot;
    status_iot = IoTCloud::init("camera_viewer", p_zed);
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

    // Init logger (optional)
    IoTCloud::setLogLevelThreshold(LOG_LEVEL::DEBUG,LOG_LEVEL::DEBUG);

    // Setup Init Parameters
    initParameters.camera_resolution = RESOLUTION::HD2K;
    initParameters.depth_mode = DEPTH_MODE::NONE;
    initParameters.sdk_verbose = true;
    initParameters.sdk_gpu_id = -1;

    // -------------------- MAIN LOOP -------------------------------
    while (full_run) {
        main_loop();
        sl::sleep_ms(30);
    }

    // Out
    return 0;
}
