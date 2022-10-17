///////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2022, STEREOLABS.
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

#include <sl_iot/HubClient.hpp>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;

// Secondary streams' loop to grab image
void secondary_stream_loop(Camera& zed, const std::string& stream_name, bool& run)
{
    std::cout << "Secondary stream (" << stream_name << ") opened" << std::endl;
    Mat zed_image(1280, 720, MAT_TYPE::U8_C4);

    while (run) {
        // grab current images and compute depth
        if (zed.grab() == ERROR_CODE::SUCCESS)
        {
            zed.retrieveImage(zed_image, VIEW::LEFT, MEM::CPU, zed_image.getResolution());
            auto status_code = HubClient::addSecondaryStream(stream_name, zed_image);
        }
        else
        {
            run = false;
        }
    }
}

int main(int argc, char **argv)
{
    STATUS_CODE status_iot;
    // Initialize the communication to ZED Hub
    status_iot = HubClient::connect("multi_stream_tutorial");
    if (status_iot != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    // Get detected cameras
	std::vector<DeviceProperties> devList = Camera::getDeviceList();
    int nb_detected_zed = devList.size();
    
    if (nb_detected_zed == 0)
    {
        std::cout << "No ZED Detected, exit program" << std::endl;
        exit(EXIT_FAILURE);
    }
    
    std::cout << nb_detected_zed << " ZED detected" << std::endl;

    InitParameters initParameters;
    initParameters.camera_resolution = RESOLUTION::HD720;
    initParameters.camera_fps = 30;
    initParameters.depth_mode = DEPTH_MODE::NONE;

    std::vector<Camera> zeds(nb_detected_zed);

    // Open every detected cameras
    for (int z = 0; z < nb_detected_zed; z++)
    {
        initParameters.input.setFromCameraID(z);
        ERROR_CODE err = zeds[z].open(initParameters);
        if (err == ERROR_CODE::SUCCESS)
        {
            auto cam_info = zeds[z].getCameraInformation();
            std::cout << "serial number: " << cam_info.serial_number << ", model: " <<  cam_info.camera_model << ", status: opened" << std::endl;
        }
        else
        {
            std::cout << " Error: " << err << std::endl;
            zeds[z].close();
        }
    }

    if (zeds.size() <= 0)
        exit(EXIT_FAILURE);

    // Register the first camera as the main one
    std::shared_ptr<Camera> p_zed;
    p_zed.reset(&zeds[0]);
    HubClient::registerCamera(p_zed);

    // Thread loops for secondary streams
    bool run_zeds = true;
    std::vector<thread> thread_pool(nb_detected_zed - 1);
    for (int z = 1; z < nb_detected_zed; z++)
    {
        if (zeds[z].isOpened())
        {
            auto cam_info = zeds[z].getCameraInformation();
            thread_pool[z - 1] = std::thread(secondary_stream_loop, ref(zeds[z]), std::to_string(cam_info.serial_number), ref(run_zeds));
        }
    }

    // Main loop
    while (run_zeds)
    {
        // Grab a new frame from the ZED
        auto status_zed = p_zed->grab();

        if (status_zed != ERROR_CODE::SUCCESS) break;

        // Always update IoT at the end of the grab loop
        HubClient::update();
    }
    
    run_zeds = false;
    p_zed->close();
    
    // Wait for every thread to be stopped
    for (int z = 1; z < nb_detected_zed; z++)
        if (zeds[z].isOpened()) 
            thread_pool[z].join();

    return 0;
}
