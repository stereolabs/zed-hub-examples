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

import pyzed.sl as sl
import pyzed.sl_iot as sliot
import json
import os
import random

# Constants, defined as global variables
latitude = 48.818737
longitude = 2.318206
altitude = 0

# Parameters, defined as global variables
telemetryFreq = 1.0

def on_telemetry_update(message_received):
    global telemetryFreq
    print("Telemetry updated")
    telemetryFreq = sliot.HubClient.get_parameter_float(
        "telemetryFreq", sliot.PARAMETER_TYPE.APPLICATION, telemetryFreq)
    sliot.HubClient.send_log(
        "New parameters : telemetryFreq modified", sliot.LOG_LEVEL.INFO)

def main():
    global telemetryFreq
    global latitude
    global longitude
    global altitude

    sliot.HubClient.load_application_parameters("parameters.json")

    telemetryFreq = 1.0  # in seconds

    # Initialize the communication to ZED Hub, with a zed camera.
    zed = sl.Camera()
    status_iot = sliot.HubClient.connect("gps_app")

    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_iot)
        exit(1)

    status_iot = sliot.HubClient.register_camera(zed)
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status_iot)
        exit(1)

    sliot.HubClient.set_log_level_threshold(
        sliot.LOG_LEVEL.DEBUG, sliot.LOG_LEVEL.INFO)

    # Open the zed camera
    init_params = sl.InitParameters()
    status_zed = zed.open(init_params)

    if status_zed != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log(
            "Camera initialization error : " + str(status_zed), sliot.LOG_LEVEL.ERROR)
        exit(1)

    runtime_params = sl.RuntimeParameters()

    # PARAMETER_TYPE.APPLICATION is only suitable for dockerized apps, like this sample.
    # If you want to test this on your machine, you'd better switch all your subscriptions to PARAMETER_TYPE.DEVICE.

    callback_telemetry_param = sliot.CallbackParameters()
    callback_telemetry_param.set_parameter_callback("onTelemetryUpdate", "telemetryFreq",  sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE,  sliot.PARAMETER_TYPE.APPLICATION);
    sliot.HubClient.register_function(on_telemetry_update, callback_telemetry_param);

    # get values defined by the ZED Hub interface.

    telemetryFreq = sliot.HubClient.get_parameter_float(
        "telemetryFreq", sliot.PARAMETER_TYPE.APPLICATION, telemetryFreq)

    prev_timestamp = zed.get_timestamp(sl.TIME_REFERENCE.CURRENT)

    # Main loop
    while True:
        status_zed = zed.grab(runtime_params)
        if status_zed == sl.ERROR_CODE.SUCCESS:

            current_ts = zed.get_timestamp(sl.TIME_REFERENCE.IMAGE)

            # /*******     Define and send Telemetry   *********/
            
            if current_ts.get_seconds() >= prev_timestamp.get_seconds() + telemetryFreq:
                # Update coordinate
                latitude += random.random() / 10000 - .00005
                latitude = min(90.0, latitude)
                latitude = max(-90.0, latitude)
                longitude += random.random() / 10000 - .00005
                longitude = min(180.0, longitude)
                longitude = max(-180.0, longitude)
                altitude += random.random() / 10000 - .00005

                # Send Telemetry
                gps = {}
                gps["layer_type"] = "geolocation"
                gps["position"] = {}
                gps["position"]["latitude"] = latitude
                gps["position"]["longitude"] = longitude
                gps["position"]["altitude"] = altitude
                gps["position"]["uncertainty"] = {}
                gps["position"]["uncertainty"]["eph"] = None
                gps["position"]["uncertainty"]["epv"] = None
                gps["velocity"] = {}
                gps["velocity"]["x"] = None
                gps["velocity"]["y"] = None
                gps["velocity"]["z"] = None
                gps["rotation"] = {}
                gps["rotation"]["x"] = None
                gps["rotation"]["y"] = None
                gps["rotation"]["z"] = None
                gps["epoch_timestamp"] = current_ts.get_milliseconds()
                
                sliot.HubClient.send_telemetry("GPS_data", gps)
                prev_timestamp = current_ts

            # Always update IoT at the end of the grab loop
            sliot.HubClient.update()
        
    if zed.is_opened():
        zed.close()

    # Close the communication with Zed Hub properly.
    status = sliot.HubClient.disconnect()
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status)
        exit(1)

    return


if __name__ == "__main__":
    main()
