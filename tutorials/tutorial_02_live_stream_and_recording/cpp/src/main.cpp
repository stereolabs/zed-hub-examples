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
    // initialize the communication to zed hub, with a zed camera.
    std::shared_ptr<sl::Camera> p_zed;
    p_zed.reset(new sl::Camera());

    STATUS_CODE status_iot;
    status_iot = IoTCloud::init("streaming_app", p_zed);
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initiliazation error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
 
    //Open the ZED camera
    sl::InitParameters initParameters;
    initParameters.camera_resolution = RESOLUTION::HD2K;
    initParameters.depth_mode = DEPTH_MODE::NONE;

    sl::ERROR_CODE status_zed = p_zed->open(initParameters);
    if (status_zed != ERROR_CODE::SUCCESS) {
        IoTCloud::log("Camera initialization error : "\
         + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    // Main loop
    while (true) {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab();
        if (status_zed != ERROR_CODE::SUCCESS) break;
        
        // Do what you want with the data from the camera.
        // For examples of what you can do with the zed camera, visit https://github.com/stereolabs/zed-examples
            

        // Always refresh IoT at the end of the grab loop
        IoTCloud::refresh();
    }

    // Handling camera error
    if(status_zed != ERROR_CODE::SUCCESS){
        IoTCloud::log("Grab failed, restarting camera. "+\
        std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        p_zed->close();
        sl::ERROR_CODE e = sl::Camera::reboot(p_zed->getCameraInformation().serial_number);
    }
    // Close the camera
    else if(p_zed->isOpened())
        p_zed->close();

    // Close the communication with zed hub properly.
    status_iot = IoTCloud::stop();
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Terminating error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
    
    return 0;
}
