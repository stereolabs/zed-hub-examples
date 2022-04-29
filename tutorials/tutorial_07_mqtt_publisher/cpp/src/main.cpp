#include <stdio.h>
#include <string.h>
#include <chrono>

#include <sl_iot/HubClient.hpp>
#include <csignal>
#include <ctime>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;


int main(int argc, char **argv) {

    STATUS_CODE status_iot;
    status_iot = HubClient::connect("mqtt_pub_app");
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initialization error " << status_iot << std::endl;
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

        HubClient::publishOnMqttTopic(topic_name, my_message_js, topic_prefix);
        HubClient::sendLog("MQTT message published", LOG_LEVEL::INFO);

        sleep_ms(10000); // 10 seconds
    }

    status_iot = HubClient::disconnect();
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Terminating error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    return 0;
}
  
