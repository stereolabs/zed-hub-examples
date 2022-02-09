#include <stdio.h>
#include <string.h>
#include <chrono>

#include <sl_iot/IoTCloud.hpp>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;

int main(int argc, char **argv) {

    STATUS_CODE status_iot;
    status_iot = IoTCloud::initNoZED("basic_app");
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initialization error " << status_iot << std::endl;
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

    status_iot = IoTCloud::stop();
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Terminating error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }
    return 0;
}
