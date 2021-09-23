#include <stdio.h>
#include <string.h>
#include <chrono>

#include <sl_iot/IoTCloud.hpp>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;

// Your addition function callback
void additionCallback(FunctionEvent& event) {
    //Get the parameters of the remote function call
    sl_iot::json params = event.getEvenParameters();
    //Check if parameters are present and valid
    if (params.find("num1") != params.end() && params["num1"].is_number_integer() &&
	params.find("num2") != params.end() && params["num2"].is_number_integer()) {
        int num1 = params["num1"].get<int>();
        int num2 = params["num2"].get<int>();
        int result = num1 + num2;

        //Log your result
        IoTCloud::log("Addition called : "+std::to_string(num1)+" + "+std::to_string(num2)+" = "+std::to_string(result),LOG_LEVEL::INFO);

        //Update the result and status of the event
        event.status = 0;
        event.result = result;
    } 
    else {
        IoTCloud::log("Addition remote function was used with wrong arguments.",LOG_LEVEL::ERROR);
        event.status = 1;
        event.result = "Addition remote function was used with wrong arguments.";
    }
}

int main(int argc, char **argv) {
    //In service deployment init IoT with the SL_APPLICATION_TOKEN environment variable
    //In development you can simply init it with the application name
    const char * application_token = ::getenv("SL_APPLICATION_TOKEN");
    STATUS_CODE status_iot;
    if (!application_token) {
        status_iot = IoTCloud::init("callback_app");
    } else {
        status_iot = IoTCloud::init(application_token);
    }
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Initiliazation error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    //Set your callback parameters. Here, the payload is set to nullptr but you can put a pointer to any thing to get it from your FunctionEvent in the callback.
    CallbackParameters callback_params;
    callback_params.setRemoteCallback("tuto05_add", CALLBACK_TYPE::ON_REMOTE_CALL, nullptr);
    //Register your callback function
    IoTCloud::registerFunction(additionCallback, callback_params);
    std::cout << "Waiting for remote function to be called." << std::endl;
    // Main loop
    while (true) {
	std::this_thread::sleep_for(1s);
    }

    return 0;
}
