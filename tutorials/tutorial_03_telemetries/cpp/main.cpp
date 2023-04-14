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

int main(int argc, char **argv)
{
    // Initialize the communication to zed hub, with a zed camera.
    std::shared_ptr<sl::Camera> p_zed;
    p_zed.reset(new sl::Camera());

    STATUS_CODE status_hub;
    status_hub = HubClient::connect("telemetry_app");
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    // Open the ZED camera
    sl::InitParameters initParameters;
    initParameters.camera_resolution = RESOLUTION::HD2K;

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

    // Enable Positional Tracking
    PositionalTrackingParameters positional_tracking_param;
    positional_tracking_param.enable_area_memory = true;
    status_zed = p_zed->enablePositionalTracking(positional_tracking_param);
    if (status_zed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Enabling positional tracking failed : " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    sl::Pose cam_pose;
    sl::RuntimeParameters runtime_parameters;
    runtime_parameters.measure3D_reference_frame = sl::REFERENCE_FRAME::WORLD;
    sl::Timestamp prev_timestamp = 0;

    // Main loop
    while (true)
    {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab(runtime_parameters);
        if (status_zed != ERROR_CODE::SUCCESS)
            break;

        sl::Timestamp curr_timestamp = p_zed->getTimestamp(sl::TIME_REFERENCE::IMAGE);
        if (curr_timestamp.getMilliseconds() >= prev_timestamp.getMilliseconds() + 1000)
        {
            // Retrieve camera position
            p_zed->getPosition(cam_pose);
            sl::Translation translation = cam_pose.getTranslation();
            sl::float3 rotation_vector = cam_pose.getRotationVector();

            // Send Telemetry
            sl_hub::json position_telemetry;
            position_telemetry["tx"] = translation.x;
            position_telemetry["ty"] = translation.y;
            position_telemetry["tz"] = translation.z;
            position_telemetry["rx"] = rotation_vector.x;
            position_telemetry["ry"] = rotation_vector.y;
            position_telemetry["rz"] = rotation_vector.z;
            HubClient::sendTelemetry("camera_position", position_telemetry);
            prev_timestamp = curr_timestamp;
        }

        // Insert custom code here

        // Always update Hub at the end of the grab loop
        HubClient::update(p_zed);
        sleep_ms(1);
    }

    p_zed->disablePositionalTracking();
    
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
