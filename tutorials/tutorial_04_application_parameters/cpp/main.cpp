///////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2023, STEREOLABS.
//
// All rights reserved.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
///////////////////////////////////////////////////////////////////////////

#include <stdio.h>
#include <string.h>
#include <chrono>

#include <sl/Camera.hpp>
#include <sl_hub/HubClient.hpp>
#include <csignal>

using namespace std;
using namespace sl;
using namespace sl_hub;
using json = sl_hub::json;

bool led_status_updated = true;
string app_param = "";

// Callback on led status update, it sets a boolean to true to turn off/on the led status in the main loop.
void onLedStatusUpdate(FunctionEvent &event)
{
    event.status = 0;
    led_status_updated = true;
    std::cout << "Led Status updated !" << std::endl;
}

// Callback on app_param update, it log its new value
void onAppParamUpdate(FunctionEvent &event)
{
    event.status = 0;
    app_param = HubClient::getParameter<std::string>("app_param", PARAMETER_TYPE::APPLICATION, app_param);
    std::cout << "App Param updated: " << app_param << std::endl;
}

int main(int argc, char **argv)
{
    // Create camera object
    std::shared_ptr<sl::Camera> p_zed;
    p_zed.reset(new sl::Camera());

    STATUS_CODE status_hub;
    status_hub = HubClient::connect("parameter_app");
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    // Open the ZED camera
    sl::InitParameters initParameters;
    initParameters.camera_resolution = RESOLUTION::HD2K;
    initParameters.depth_mode = DEPTH_MODE::NONE;

    sl::ERROR_CODE status_zed = p_zed->open(initParameters);
    if (status_zed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Camera initialization error : " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    // Register the camera once it's open
    UpdateParameters updateParameters;
    status_hub = HubClient::registerCamera(p_zed, updateParameters);
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Camera registration error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    // Load application parameter file in development mode
    char *application_token = getenv("SL_APPLICATION_TOKEN");
    if (!application_token)
    {
        status_hub = HubClient::loadApplicationParameters("parameters.json");
        if (status_hub != STATUS_CODE::SUCCESS)
        {
            std::cout << "parameters.json file not found or malformated"
                      << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    // Set your parameter callback
    CallbackParameters callback_param_led;
    callback_param_led.setParameterCallback("onLedStatusChange", "led_status", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
    HubClient::registerFunction(onLedStatusUpdate, callback_param_led);

    CallbackParameters callback_app_param;
    callback_app_param.setParameterCallback("onAppParamUpdate", "app_param", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
    HubClient::registerFunction(onAppParamUpdate, callback_app_param);

    // Main loop
    while (true)
    {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab();
        if (status_zed != ERROR_CODE::SUCCESS)
            break;

        if (led_status_updated)
        {
            int curr_led_status;
            status_zed = p_zed->getCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS, curr_led_status);
            bool led_status = HubClient::getParameter<bool>("led_status", PARAMETER_TYPE::DEVICE, curr_led_status);
            p_zed->setCameraSettings(sl::VIDEO_SETTINGS::LED_STATUS, led_status);
            HubClient::reportParameter<bool>("led_status", PARAMETER_TYPE::DEVICE, led_status);
            led_status_updated = false;
        }

        // Always update Hub at the end of the grab loop
        // without giving a sl::Mat, it will retrieve the RGB image automatically.
        HubClient::update(p_zed);
    }

    // Handling camera error
    if (status_zed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Grab failed, restarting camera. " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        p_zed->close();
        sl::Camera::reboot(p_zed->getCameraInformation().serial_number);
    }

    // Close the camera
    if (p_zed->isOpened())
        p_zed->close();

    status_hub = HubClient::disconnect();
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Terminating error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    return 0;
}
