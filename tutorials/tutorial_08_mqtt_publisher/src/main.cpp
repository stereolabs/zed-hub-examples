#include <stdio.h>
#include <string.h>
#include <chrono>

#include <sl_iot/IoTCloud.hpp>
#include <csignal>
#include <ctime>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;


int main(int argc, char **argv) {

    //In service deployment init IoT with the SL_APPLICATION_TOKEN environment variable
    //In development you can simply init it with the application name
    const char * application_token = ::getenv("SL_APPLICATION_TOKEN");
    STATUS_CODE status_iot;
    if (!application_token) {
        status_iot = IoTCloud::init("mqtt_pub_app");
    } else {
        status_iot = IoTCloud::init(application_token);
    }
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initiliazation error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    TARGET topic_prefix = TARGET::LOCAL_NETWORK;
    std::string topic_name = "/my_custom_data";

    // Main loop
    while (true) {

        const auto p1 = std::chrono::system_clock::now();

        json my_message_js;
        my_message_js["message"] = "Hello World";
        my_message_js["my_custom data"] = 54;
        my_message_js["timestamp"] = std::chrono::duration_cast<std::chrono::seconds>(p1.time_since_epoch()).count();

        IoTCloud::publishOnMqttTopic(topic_name, my_message_js, topic_prefix);
        IoTCloud::log("MQTT message published", LOG_LEVEL::INFO);

        sleep_ms(10000); // 10 seconds
    }

    return 0;
}
  
