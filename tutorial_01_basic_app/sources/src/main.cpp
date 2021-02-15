#include <stdio.h>
#include <string.h>
#include <chrono>

#include <sl_iot/IoTCloud.hpp>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;

int main(int argc, char **argv) {
    //Init IoT with the SL_APPLICATION_TOKEN environment variable
    const char * application_token = ::getenv("SL_APPLICATION_TOKEN");
    STATUS_CODE status_iot = IoTCloud::init(application_token);
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initiliazation error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    //Set log level
    IoTCloud::setLogLevelThreshold(LOG_LEVEL::INFO,LOG_LEVEL::INFO);
     
    //Send a log
    IoTCloud::log("Initialization succeeded",LOG_LEVEL::INFO);

    //Is your application connected to the cloud
    if (IoTCloud::isInitialized()==STATUS_CODE::SUCCESS)
        IoTCloud::log("Application connected",LOG_LEVEL::INFO);

    // Main loop : Sent a log to the cloud each 15s
    int i = 0;
    while (true) {
        IoTCloud::log("Log "+std::to_string(i)+" sent.",LOG_LEVEL::INFO);
        std::this_thread::sleep_for(15s);
        i++;
    }

    return 0;
}
