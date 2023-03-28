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
dataFreq = 1.0

def on_date_freq_update(message_received):
    global dataFreq
    print("Data frequency updated")
    dataFreq = sliot.HubClient.get_parameter_float(
        "dataFreq", sliot.PARAMETER_TYPE.APPLICATION, dataFreq)


def on_waypoints(message_received):
    # Get the waypoints from the device parameters
    waypoints = sliot.HubClient.get_parameter_string(
        "waypoints", sliot.PARAMETER_TYPE.DEVICE, "[]")
    print("waypoints", waypoints)


def main():
    global dataFreq
    global latitude
    global longitude
    global altitude

    sliot.HubClient.load_application_parameters("parameters.json")

    dataFreq = 1.0  # in seconds

    # Create camera object
    zed = sl.Camera()

    # Initialize the communication to ZED Hub, with a zed camera.
    status_iot = sliot.HubClient.connect("gnss_app")
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_iot)
        exit(1)

    # Load application parameter file in development mode
    application_token = os.getenv("SL_APPLICATION_TOKEN")
    if application_token == None:
        status_iot = sliot.HubClient.load_application_parameters("parameters.json")
        if status_iot != sliot.STATUS_CODE.SUCCESS:
            print("parameters.json file not found or malformated")
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


    # Register the camera once it's open
    update_params = sliot.UpdateParameters()
    status_iot = sliot.HubClient.register_camera(zed, update_params)
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status_iot)
        exit(1)

    runtime_params = sl.RuntimeParameters()

    # PARAMETER_TYPE.APPLICATION is only suitable for dockerized apps, like this sample.
    # If you want to test this on your machine, you'd better switch all your subscriptions to PARAMETER_TYPE.DEVICE.

    callback_params = sliot.CallbackParameters()
    callback_params.set_parameter_callback("onDataFreqUpdate", "dataFreq",  sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE,  sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_date_freq_update, callback_params)

    callback_params.set_parameter_callback("onWaypoints", "waypoints",  sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE,  sliot.PARAMETER_TYPE.DEVICE)
    sliot.HubClient.register_function(on_waypoints, callback_params)

    # get values defined by the ZED Hub interface.

    dataFreq = sliot.HubClient.get_parameter_float(
        "dataFreq", sliot.PARAMETER_TYPE.APPLICATION, dataFreq)

    prev_timestamp = zed.get_timestamp(sl.TIME_REFERENCE.CURRENT)

    # Main loop
    while True:
        status_zed = zed.grab(runtime_params)
        if status_zed == sl.ERROR_CODE.SUCCESS:

            current_ts = zed.get_timestamp(sl.TIME_REFERENCE.IMAGE)

            # /*******     Define and send data   *********/
            
            if current_ts.get_seconds() >= prev_timestamp.get_seconds() + dataFreq:
                # Update coordinate
                latitude += random.random() / 10000 - .00005
                latitude = min(90.0, latitude)
                latitude = max(-90.0, latitude)
                longitude += random.random() / 10000 - .00005
                longitude = min(180.0, longitude)
                longitude = max(-180.0, longitude)
                altitude += random.random() / 10000 - .00005

                # Send data
                gnss = {}
                gnss["layer_type"] = "geolocation"
                gnss["label"] = "GNSS_data"
                gnss["position"] = {}
                gnss["position"]["latitude"] = latitude
                gnss["position"]["longitude"] = longitude
                gnss["position"]["altitude"] = altitude

                sliot.HubClient.send_data_to_peers("geolocation", json.dumps(gnss))
                prev_timestamp = current_ts

            # Always update Hub at the end of the grab loop
            sliot.HubClient.update()
        
    if zed.is_opened():
        zed.close()

    # Close the communication with ZED Hub properly.
    status = sliot.HubClient.disconnect()
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status)
        exit(1)

    return


if __name__ == "__main__":
    main()
