// ########################################################################
// #
// # Copyright (c) 2022, STEREOLABS.
// #
// # All rights reserved.
// #
// # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// # A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// # OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// # SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// # LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// # DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// # THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
// #
// ########################################################################

#include <stdio.h>
#include <string.h>
#include <chrono>

#include <sl/Camera.hpp>
#include <sl_iot/HubClient.hpp>
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
void onInitParamUpdate(FunctionEvent &event)
{
    event.status = 0;
    HubClient::sendLog("Init Parameters Update. Re-opening the camera.", LOG_LEVEL::INFO);
    run = false;
}

///
/// \brief Callback generated when LED status has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onLedStatusUpdate(FunctionEvent &event)
{
    event.status = 0;
    sdk_guard.lock();
    int curr_led_status = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS);
    bool led_status = HubClient::getParameter<bool>("led_status", PARAMETER_TYPE::DEVICE, curr_led_status);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS, led_status);
    sdk_guard.unlock();
    HubClient::reportParameter<bool>("led_status", PARAMETER_TYPE::DEVICE, led_status);
}

///
/// \brief Callback generated when GAMMA video settings has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onGammaUpdate(FunctionEvent &event)
{
    event.status = 0;
    sdk_guard.lock();
    int curr_gamma = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::GAMMA);
    int gamma = HubClient::getParameter<int>("camera_gamma", PARAMETER_TYPE::DEVICE, curr_gamma);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::GAMMA, gamma);
    sdk_guard.unlock();
    HubClient::purgeVideoStream();
    HubClient::reportParameter<int>("camera_gamma", PARAMETER_TYPE::DEVICE, gamma);
}

///
/// \brief Callback generated when GAMMA video settings has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onGainUpdate(FunctionEvent &event)
{
    event.status = 0;
    sdk_guard.lock();
    int curr_gain = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::GAIN);
    int gain = HubClient::getParameter<int>("camera_gain", PARAMETER_TYPE::DEVICE, curr_gain);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::GAIN, gain);
    sdk_guard.unlock();
    HubClient::purgeVideoStream();
    HubClient::reportParameter<int>("camera_gain", PARAMETER_TYPE::DEVICE, gain);
}

///
/// \brief Callback generated when AEC/AGC video settings has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onAutoExposureUpdate(FunctionEvent &event)
{
    event.status = 0;
    sdk_guard.lock();
    int curr_auto_exposure = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::AEC_AGC);
    bool auto_exposure = HubClient::getParameter<bool>("camera_auto_exposure", PARAMETER_TYPE::DEVICE, curr_auto_exposure);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::AEC_AGC, auto_exposure);
    sdk_guard.unlock();
    HubClient::purgeVideoStream();
    HubClient::reportParameter<bool>("camera_auto_exposure", PARAMETER_TYPE::DEVICE, auto_exposure);
}

///
/// \brief Callback generated when Exposure video settings has been changed on the cloud interface
/// \param event from FunctionEvent
///
void onExposureUpdate(FunctionEvent &event)
{
    event.status = 0;
    sdk_guard.lock();
    int curr_exposure = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::EXPOSURE);
    int exposure = HubClient::getParameter<int>("camera_exposure", PARAMETER_TYPE::DEVICE, curr_exposure);
    p_zed->setCameraSettings(sl::VIDEO_SETTINGS::EXPOSURE, exposure);
    sdk_guard.unlock();
    HubClient::purgeVideoStream();
    HubClient::reportParameter<int>("camera_exposure", PARAMETER_TYPE::DEVICE, exposure);
}

///
/// \brief Callback generated when the ap parameter local_stream has been modified in the interface.
/// the stream mode of the zed is enabled or disabled depending on the value
/// \param event from FunctionEvent
///
void onLocalStreamUpdate(FunctionEvent &event)
{
    event.status = 0;
    local_stream_change = true;
    bool local_stream = HubClient::getParameter<bool>("local_stream", PARAMETER_TYPE::APPLICATION, false);

    if (local_stream)
    {

        StreamingParameters stream_param;
        stream_param.codec = sl::STREAMING_CODEC::H264;

        // restart streaming with new parameters
        p_zed->disableStreaming();
        auto zed_error = p_zed->enableStreaming(stream_param);
        if (zed_error != ERROR_CODE::SUCCESS)
        {
            std::cout << "[onAppStreamParamUpdate] " << sl::toVerbose(zed_error) << "\nExit program." << std::endl;
            p_zed->close();
            exit(EXIT_FAILURE);
        }
    }
    else
    {
        p_zed->disableStreaming();
    }
}

void updateInitParamsFromCloud(sl::InitParameters &parameters)
{
    std::string reso_str = HubClient::getParameter<std::string>("camera_resolution", PARAMETER_TYPE::DEVICE, sl::toString(parameters.camera_resolution).c_str());
    if (reso_str == "HD2K")
        parameters.camera_resolution = RESOLUTION::HD2K;
    else if (reso_str == "HD720")
        parameters.camera_resolution = RESOLUTION::HD720;
    else if (reso_str == "HD1080")
        parameters.camera_resolution = RESOLUTION::HD1080;
    else if (reso_str == "WVGA")
        parameters.camera_resolution = RESOLUTION::VGA;

    HubClient::reportParameter<std::string>("camera_resolution", PARAMETER_TYPE::DEVICE, reso_str);

    parameters.camera_image_flip = HubClient::getParameter<int>("camera_image_flip", PARAMETER_TYPE::DEVICE, (int)parameters.camera_image_flip);
    HubClient::reportParameter<int>("camera_image_flip", PARAMETER_TYPE::DEVICE, (int)parameters.camera_image_flip);

    parameters.camera_fps = HubClient::getParameter<int>("camera_fps", PARAMETER_TYPE::DEVICE, parameters.camera_fps);
    HubClient::reportParameter<int>("camera_fps", PARAMETER_TYPE::DEVICE, (int)parameters.camera_fps);
}

int main(int argc, char **argv)
{
    // Create ZED Object
    p_zed.reset(new sl::Camera());

    STATUS_CODE status_iot;
    status_iot = HubClient::connect("camera_viewer");
    if (status_iot != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
    status_iot = HubClient::registerCamera(p_zed);

    // Load application parameter file in development mode
    char *application_token = ::getenv("SL_APPLICATION_TOKEN");
    if (!application_token)
    {
        status_iot = HubClient::loadApplicationParameters("parameters.json");
        if (status_iot != STATUS_CODE::SUCCESS)
        {
            std::cout << "parameters.json file not found or malformated" << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    // Init logger (optional)
    HubClient::setLogLevelThreshold(LOG_LEVEL::DEBUG, LOG_LEVEL::DEBUG);

    // Setup Init Parameters
    initParameters.camera_resolution = RESOLUTION::HD2K;
    initParameters.depth_mode = DEPTH_MODE::NONE;
    initParameters.sdk_verbose = true;
    initParameters.sdk_gpu_id = -1;

    // -------------------HubClient::log- MAIN LOOP -------------------------------
    // Get Init Parameters from cloud parameters
    updateInitParamsFromCloud(initParameters);
    
    // Override parameters
    initParameters.sdk_verbose = true;
    initParameters.sensors_required = true;

    // Open init parameters
    sl::ERROR_CODE errZed = p_zed->open(initParameters);
    if (errZed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Camera initialization error : " + std::string(toString(errZed)), LOG_LEVEL::ERROR);
        full_run = false;
        exit(EXIT_FAILURE);
    }

    // Setup callback for parameters

    CallbackParameters callback_param;
    callback_param.setParameterCallback("onParamChange", "camera_resolution|camera_fps|camera_image_flip", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
    HubClient::registerFunction(onInitParamUpdate, callback_param);

    CallbackParameters callback_param_auto_exposure;
    callback_param_auto_exposure.setParameterCallback("onAutoExposureChange", "camera_auto_exposure", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
    HubClient::registerFunction(onAutoExposureUpdate, callback_param_auto_exposure);

    CallbackParameters callback_param_exposure;
    callback_param_exposure.setParameterCallback("onExposureChange", "camera_exposure", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
    HubClient::registerFunction(onExposureUpdate, callback_param_exposure);

    CallbackParameters callback_param_gain;
    callback_param_gain.setParameterCallback("onGainChange", "camera_gain", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
    HubClient::registerFunction(onGainUpdate, callback_param_exposure);

    CallbackParameters callback_param_gamma;
    callback_param_gamma.setParameterCallback("onGammaChange", "camera_gamma", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
    HubClient::registerFunction(onGammaUpdate, callback_param_gamma);

    CallbackParameters callback_param_stream;
    callback_param_stream.setParameterCallback("onLocalStreamChange", "local_stream", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
    HubClient::registerFunction(onLocalStreamUpdate, callback_param_stream);

    bool local_stream = HubClient::getParameter<bool>("local_stream", PARAMETER_TYPE::APPLICATION, false);
    if (local_stream)
    {
        StreamingParameters stream_param;
        stream_param.codec = sl::STREAMING_CODEC::H264;
        p_zed->enableStreaming(stream_param);
    }

    HubClient::reportParameter<bool>("local_stream", PARAMETER_TYPE::APPLICATION, local_stream);

    while (true)
    {
        sdk_guard.lock();
        auto err = p_zed->grab();
        sdk_guard.unlock();

        if (err == ERROR_CODE::SUCCESS)
        {
            HubClient::update();
        }
        else
        {
            int size_devices = sl::Camera::getDeviceList().size();
            HubClient::sendLog("Camera grab error: " + std::string(sl::toString(err)) + ". ( Number of camera detected : " + to_string(size_devices) + " ) ", LOG_LEVEL::ERROR);
            break;
        }
    }

    if (p_zed->isOpened())
        p_zed->close();

    status_iot = HubClient::disconnect();
    if (status_iot != STATUS_CODE::SUCCESS)
    {
        std::cout << "Terminating error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    // Out
    return 0;
}
