########################################################################
#
# Copyright (c) 2022, STEREOLABS.
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

import pyzed.sl_iot as sliot
import time
import os
import json
import gc

# from typing import Callable

def addition_callback(event : sliot.FunctionEvent):
    params = event.parameters
    print(json.dumps(params))
    num1 = params["num1"]
    num2 = params["num2"]

    # Check if parameters are valid
    if isinstance(num1, int) and isinstance(num2, int):
        result = num1 + num2
        # Log your result
        log = "Addition called : " + \
            str(num1) + " + " + str(num2) + " = " + str(result)
        sliot.HubClient.send_log(log, sliot.LOG_LEVEL.INFO)
        event.status = 0
        event.result = result
        return result

    else:
        print("There was an issue with the parameters type.")
        event.status = 1
        event.result = "Error"
    return None


def main():
    status_iot = sliot.HubClient.connect("callback_app")

    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_iot)
        exit(1)

    # Set your parameter callback
    callback_params = sliot.CallbackParameters()
    callback_params.set_remote_callback("tuto05_add", sliot.CALLBACK_TYPE.ON_REMOTE_CALL)
    my_callback = addition_callback
    sliot.HubClient.register_function(my_callback, callback_params)
    gc.collect()

    print("Waiting for remote function to be called.")
    # Main loop
    while True:
        pass

    # Close the communication with ZED Hub properly.
    status = sliot.HubClient.disconnect()
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status)
        exit(1)

    return


if __name__ == "__main__":
    main()
