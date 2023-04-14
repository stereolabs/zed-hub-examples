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

#include <sl_hub/HubClient.hpp>

using namespace std;
using namespace sl;
using namespace sl_hub;
using json = sl_hub::json;

#include <chrono>
#include <thread>

// Streams' loop to grab image
void stream_loop(const std::shared_ptr<Camera> &p_zed, bool &run)
{
    Mat zed_image(1280, 720, MAT_TYPE::U8_C4);

    while (run)
    {
        // grab current image
        if (p_zed->grab() == ERROR_CODE::SUCCESS)
        {
            p_zed->retrieveImage(zed_image, VIEW::LEFT, MEM::CPU, zed_image.getResolution());
            HubClient::update(p_zed, zed_image);
        }
        else
            run = false;
    }
}

int main(int argc, char **argv)
{
    // Initialize the communication to ZED Hub
    STATUS_CODE status_hub;
    status_hub = HubClient::connect("multi_stream_tutorial");
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_hub << std::endl;
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

    std::vector<std::shared_ptr<sl::Camera>> zeds(nb_detected_zed);

    // Open every detected cameras
    for (int i = 0; i < nb_detected_zed; i++)
    {
        zeds[i].reset(new sl::Camera());
        initParameters.input.setFromCameraID(i);

        ERROR_CODE err = zeds[i]->open(initParameters);
        if (err == ERROR_CODE::SUCCESS)
        {
            auto cam_info = zeds[i]->getCameraInformation();
            std::cout << "serial number: " << cam_info.serial_number << ", model: " << cam_info.camera_model << ", status: opened" << std::endl;
        }
        else
        {
            std::cout << "Error on camera " << i << " : " << err << std::endl;
            throw(new std::exception());
        }

        // Register the camera once it's open
        UpdateParameters updateParameters;

        // On Ubuntu desktop, on consumer-level GPUs, you don't have enough hardware encoder to stream multiple devices
        // and to record at the same time. https://en.wikipedia.org/wiki/Nvidia_NVENC
        // On Jetsons or on business-grade gpus, you can do whatever you want.
        updateParameters.enable_recording = false;
        status_hub = HubClient::registerCamera(zeds[i], updateParameters);
        if (status_hub != STATUS_CODE::SUCCESS)
        {
            std::cout << "Camera registration error " << status_hub << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    // Thread loops for all streams
    bool run_zeds = true;
    std::vector<thread> thread_pool(nb_detected_zed);
    for (int i = 0; i < nb_detected_zed; i++)
    {
        if (zeds[i]->isOpened())
        {
            thread_pool[i] = std::thread(stream_loop, zeds[i], ref(run_zeds));
        }
    }

    // Main loop
    while (run_zeds)
    {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    // Wait for every thread to be stopped
    for (int i = 0; i < nb_detected_zed; i++)
        if (zeds[i]->isOpened())
        {
            thread_pool[i].join();
            zeds[i]->close();
        }

    return 0;
}
