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

#include <sl_hub/HubClient.hpp>

using namespace std;
using namespace sl;
using namespace sl_hub;
using json = sl_hub::json;

// Your addition function callback
void additionCallback(FunctionEvent &event)
{
    // Get the parameters of the remote function call
    std::cout << "function called !" << std::endl;
    sl_hub::json params = event.getEventParameters();

    // Check if parameters are present and valid
    if (params.contains("num1") && params["num1"].is_number_integer() &&
        params.contains("num2") && params["num2"].is_number_integer())
    {
        int num1 = params["num1"].get<int>();
        int num2 = params["num2"].get<int>();
        int result = num1 + num2;

        // Log your result
        HubClient::sendLog("Addition called : " + std::to_string(num1) + " + " + std::to_string(num2) + " = " + std::to_string(result), LOG_LEVEL::INFO);

        // Update the result and status of the event
        event.status = 0;
        event.result = result;
    }
    else
    {
        HubClient::sendLog("Addition remote function was used with wrong arguments.", LOG_LEVEL::ERROR);
        event.status = 1;
        event.result = "Addition remote function was used with wrong arguments.";
    }
}

int main(int argc, char **argv)
{
    STATUS_CODE status_hub;
    status_hub = HubClient::connect("callback_app");
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    // Set your callback parameters
    CallbackParameters callback_params;
    callback_params.setRemoteCallback("tuto05_add", CALLBACK_TYPE::ON_REMOTE_CALL);
    // Register your callback function
    HubClient::registerFunction(additionCallback, callback_params);
    
    std::cout << "Waiting for remote function to be called." << std::endl;
    
    // Main loop
    while (true)
    {
        std::this_thread::sleep_for(1s);
    }

    // Close the communication with ZED Hub properly.
    status_hub = HubClient::disconnect();
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Terminating error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    return 0;
}
