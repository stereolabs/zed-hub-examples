// ########################################################################
// #
// # Copyright (c) 2023, STEREOLABS.
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

#include <cstdlib>
#include <iostream>
#include <ctime>
#include <sl/Camera.hpp>
#include <sl_hub/HubClient.hpp>

using namespace std;
using namespace sl;
using namespace sl_hub;
using json = sl_hub::json;

// Constants, defined as global variables
double latitude = 48.818737;
double longitude = 2.318206;
double altitude = 0;
double max_rand = RAND_MAX * 10000.;
double getRandom()
{
    return rand() / max_rand - .00005;
}

// Parameters, defined as global variables
float dataFreq = 1.f; // in seconds

// Parameter callbacks
void onDataFreqUpdate(FunctionEvent &event)
{
    event.status = 0;
    dataFreq = HubClient::getParameter<float>("dataFreq", PARAMETER_TYPE::APPLICATION, dataFreq);
}

void onWaypoints(FunctionEvent &event)
{
    // Get the waypoints from the device parameters
    std::string waypoints = HubClient::getParameter<std::string>("waypoints", PARAMETER_TYPE::DEVICE, "[]");
    std::cout << "waypoints: " << waypoints << std::endl;

    event.status = 0;
    event.result = waypoints;
}

int main(int argc, char **argv)
{
    // Create camera object
    auto p_zed = std::make_shared<sl::Camera>();

    // Initialize the communication to ZED Hub, with a zed camera.
    STATUS_CODE status_hub;
    status_hub = HubClient::connect("gnss_app");
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    // Load application parameter file in development mode
    char *application_token = getenv("SL_APPLICATION_TOKEN");
    if (!application_token)
    {
        status_hub = HubClient::loadApplicationParameters("parameters.json");
        if (status_hub != STATUS_CODE::SUCCESS)
        {
            std::cout << "parameters.json file not found or malformated" << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    HubClient::setLogLevelThreshold(LOG_LEVEL::DEBUG, LOG_LEVEL::INFO);
    
    // Open the ZED camera
    sl::InitParameters initParameters;
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

    // Runtime parameters
    sl::RuntimeParameters rt_param;

    /*********    App parameters      *************/

    CallbackParameters callback_params;
    callback_params.setParameterCallback("onDataFreqUpdate", "dataFreq", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
    HubClient::registerFunction(onDataFreqUpdate, callback_params);

    callback_params.setParameterCallback("onWaypoints", "waypoints", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::DEVICE);
    HubClient::registerFunction(onWaypoints, callback_params);

    // get values defined by the ZED Hub interface.
    // Last argument is default value in case of failure
    dataFreq = HubClient::getParameter<float>("dataFreq", PARAMETER_TYPE::APPLICATION, dataFreq);

    /****************************/

    // Main loop

    srand(time(nullptr));
    sl::Timestamp prev_timestamp = p_zed->getTimestamp(TIME_REFERENCE::CURRENT);

    while (true)
    {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab(rt_param);
        if (status_zed != ERROR_CODE::SUCCESS)
            break;

        /*******     Define and send data   *********/

        Timestamp current_ts = p_zed->getTimestamp(TIME_REFERENCE::IMAGE);

        if ((uint64_t)(current_ts.getMilliseconds() >= (uint64_t)(prev_timestamp.getMilliseconds() + (uint64_t)dataFreq * 1000ULL)))
        {
            // Update coordinate
            latitude += getRandom();
            latitude = min(90.0, latitude);
            latitude = max(-90.0, latitude);
            longitude += getRandom();
            longitude = min(180.0, longitude);
            longitude = max(-180.0, longitude);
            altitude += getRandom();

            // Send data
            json gnss;
            gnss["layer_type"] = "geolocation";
            gnss["label"] = "GNSS_data";
            gnss["position"] = {
                {"latitude", latitude},
                {"longitude", longitude},
                {"altitude", altitude}};
            HubClient::sendDataToPeers("geolocation", gnss.dump());
            prev_timestamp = current_ts;
        }

        // Always update Hub at the end of the grab loop
        HubClient::update(p_zed);
    }

    // Handling camera error
    if (status_zed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Grab failed, restarting camera. " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        p_zed->close();
        sl::ERROR_CODE e = sl::Camera::reboot(p_zed->getCameraInformation().serial_number);
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
