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
#include <sl_iot/HubClient.hpp>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;

// Constants, defined as global variables
double latitude = 48.818737;
double longitude = 2.318206;
double altitude = 0;
double max_rand = RAND_MAX * 10000.;
double getRandom() {
    return rand() / max_rand - .00005;
}

// Parameters, defined as global variables
float telemetryFreq = 1.f; // in seconds


// Parameter callbacks
void onTelemetryUpdate(FunctionEvent &event)
{
    event.status = 0;
    telemetryFreq = HubClient::getParameter<float>("telemetryFreq", PARAMETER_TYPE::APPLICATION, telemetryFreq);
    HubClient::sendLog("New parameters : telemetryFreq modified", LOG_LEVEL::INFO);
}

int main(int argc, char **argv) {
    // Create camera object
    auto p_zed = std::make_shared<sl::Camera>();

    STATUS_CODE status_iot;
    status_iot = HubClient::connect("gps_app");
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
    
    HubClient::setLogLevelThreshold(LOG_LEVEL::DEBUG, LOG_LEVEL::INFO);
    // Open the ZED camera
    sl::InitParameters initParameters;
    sl::ERROR_CODE status_zed = p_zed->open(initParameters);
    if (status_zed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Camera initialization error : " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    // Runtime parameters
    sl::RuntimeParameters rt_param;

    /*********    App parameters      *************/

    CallbackParameters callback_telemetry_param;
    callback_telemetry_param.setParameterCallback("onTelemetryUpdate", "telemetryFreq", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
    HubClient::registerFunction(onTelemetryUpdate, callback_telemetry_param);

    // get values defined by the Zed Hub interface.
    // Last argument is default value in case of failure
    telemetryFreq = HubClient::getParameter<float>("telemetryFreq", PARAMETER_TYPE::APPLICATION, telemetryFreq);

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
        

        /*******     Define and send Telemetry   *********/
        
        Timestamp current_ts = p_zed->getTimestamp(TIME_REFERENCE::IMAGE);

        if ((uint64_t)(current_ts.getMilliseconds() >= (uint64_t)(prev_timestamp.getMilliseconds() + (uint64_t)telemetryFreq * 1000ULL)))
        {
            // Update coordinate
            latitude += getRandom();
            latitude = min(90.0, latitude);
            latitude = max(-90.0, latitude);
            longitude += getRandom();
            longitude = min(180.0, longitude);
            longitude = max(-180.0, longitude);
            altitude += getRandom();

            // Send Telemetry
            json gps;
            gps["layer_type"] = "geolocation";
            gps["position"] = {
                {"latitude", latitude},
                {"longitude", longitude},
                {"altitude", altitude}
            };
            gps["position"]["uncertainty"] = {
                {"eph", NULL},
                {"epv", NULL},
            };
            gps["velocity"] = {
                {"x", NULL},
                {"y", NULL},
                {"z", NULL}
            };
            gps["rotation"] = {
                {"x", NULL },
                {"y", NULL},
                {"z", NULL}
            };
            gps["epoch_timestamp"] = current_ts.getMilliseconds();
            HubClient::sendTelemetry("GPS_data", gps);
            prev_timestamp = current_ts;
        }
        
        // Always update IoT at the end of the grab loop
        HubClient::update();
    }

    // Handling camera error
    if (status_zed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Grab failed, restarting camera. " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        p_zed->close();
        sl::ERROR_CODE e = sl::Camera::reboot(p_zed->getCameraInformation().serial_number);
    }
    // Close the camera
    else if (p_zed->isOpened())
        p_zed->close();

    status_iot = HubClient::disconnect();
    if (status_iot != STATUS_CODE::SUCCESS)
    {
        std::cout << "Terminating error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    return 0;
}
