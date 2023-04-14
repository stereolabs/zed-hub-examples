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

#include <chrono>
#include <sl_hub/HubClient.hpp>

using namespace std;
using namespace sl;
using namespace sl_hub;
using json = sl_hub::json;

int main(int argc, char **argv)
{
    // Initialize the communication to ZED Hub, without a zed camera.
    STATUS_CODE status_hub;
    status_hub = HubClient::connect("pub_app");
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    // The name of the topic we will publish our message in
    std::string topic_name = "/my_custom_data";

    // Main loop
    while (true)
    {
        const auto p1 = std::chrono::system_clock::now();

        json my_message_js;
        my_message_js["message"] = "Hello World";
        my_message_js["my_custom data"] = 54;
        my_message_js["timestamp"] = std::chrono::duration_cast<std::chrono::seconds>(p1.time_since_epoch()).count();

        HubClient::publishOnTopic(topic_name, my_message_js);
        HubClient::sendLog("Message published", LOG_LEVEL::INFO);

        sleep_ms(10000); // 10 seconds
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
