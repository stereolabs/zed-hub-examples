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

#include <sl_iot/HubClient.hpp>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;

int main(int argc, char **argv) {
    // Initialize the communication to ZED Hub, without a zed camera.
    STATUS_CODE status_iot;
    status_iot = HubClient::connect("basic_app");
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initialization error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    string s = "";
    status_iot = HubClient::getDeviceName(s);
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "name error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
    std::cout << "name : " << s << std::endl;

    //Set log level
    HubClient::setLogLevelThreshold(LOG_LEVEL::INFO,LOG_LEVEL::INFO);
     
    //Send a log
    HubClient::sendLog("Initialization succeeded",LOG_LEVEL::INFO);

    //Is your application connected to the cloud ?
    if (HubClient::isConnected()==STATUS_CODE::SUCCESS)
        HubClient::sendLog("Application connected",LOG_LEVEL::INFO);

    // Main loop : Sent a log to the cloud every 15s
    int i = 0;
    while (true) {
        HubClient::sendLog("Log "+std::to_string(i)+" sent.",LOG_LEVEL::INFO);
        std::this_thread::sleep_for(15s);
        i++;
    }

    // Close the communication with ZED Hub properly.
    status_iot = HubClient::disconnect();
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Terminating error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
    return 0;
}
