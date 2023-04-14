########################################################################
#
# Copyright (c) 2023, STEREOLABS.
#
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
########################################################################

import pyzed.sl_hub as hub
import time


def addition_callback(event : hub.FunctionEvent):
    # Get the parameters of the remote function call
    print("function called !")
    params = event.parameters
    num1 = params["num1"]
    num2 = params["num2"]

    # Check if parameters are valid
    if isinstance(num1, int) and isinstance(num2, int):
        result = num1 + num2
        # Log your result
        log = "Addition called : " + \
            str(num1) + " + " + str(num2) + " = " + str(result)
        hub.HubClient.send_log(log, hub.LOG_LEVEL.INFO)
        event.status = 0
        event.result = result
        return result

    else:
        hub.HubClient.send_log("Addition remote function was used with wrong arguments.", hub.LOG_LEVEL.ERROR)
        event.status = 1
        event.result = "Addition remote function was used with wrong arguments."
    return None


def main():
    status_hub = hub.HubClient.connect("callback_app")
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_hub)
        exit(1)

    # Set your parameter callback
    callback_params = hub.CallbackParameters()
    callback_params.set_remote_callback("tuto05_add", hub.CALLBACK_TYPE.ON_REMOTE_CALL)
    my_callback = addition_callback
    # Register your callback function
    hub.HubClient.register_function(my_callback, callback_params)

    print("Waiting for remote function to be called.")
    
    # Main loop
    while True:
        time.sleep(1)
        pass

    # Close the communication with ZED Hub properly.
    status_hub = hub.HubClient.disconnect()
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Terminating error ", status_hub)
        exit(1)

    return


if __name__ == "__main__":
    main()
