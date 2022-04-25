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
import time
import json
import paho.mqtt.client as mqttClient
import os
import json

led_status_updated = False
global mqtt


class slMqttClient:
    def __init__(self):
        f = open('/usr/local/sl_iot/settings/env.json')
        variables = json.load(f)
        for key in variables.keys():
            if(key in os.environ):
                print("Original : ", os.environ[key])
            os.environ[key] = variables[key]
            print(key, ", ", os.environ[key])

        #######################################################################
        #                                                                     #
        #   MQTT configuration   #
        #   The docs are at https://cloud.stereolabs.com/doc/mqtt-api/        #
        #                                                                     #
        #######################################################################
        broker_address = os.environ.get("SL_MQTT_HOST")  # Broker address
        mqtt_port = int(os.environ.get("SL_MQTT_PORT"))  # Broker port
        mqtt_user = "application"  # Connection username
        app_token = os.environ.get(
            "SL_APPLICATION_TOKEN")  # Connection password

        app_name = os.environ.get("SL_APPLICATION_NAME")  # Connection password
        device_id = str(os.environ.get("SL_DEVICE_ID"))

        app_ID = str(os.environ.get("SL_APPLICATION_ID"))

        self.function_topic_in = "/v1/devices/" + device_id + "/functions/in"
        self.function_topic_out = "/v1/devices/" + device_id + "/functions/out"
        self.subscriptions = {}
        """
        client that listen to the app parameter modifications
        """
        client_name = "tutorial_5_remote_functions"

        self.client = mqttClient.Client(client_name)  # create new instance

        print("Connecting MQTT")
        # the callback is handled directly with MQTT, unlike in C++
        #############     Get the environment variables      ##################
        # set username and password
        self.client.username_pw_set(mqtt_user, password=app_token)

        self.client.on_connect = self.on_connect  # attach function to callback
        self.client.on_disconnect = self.on_disconnect  # attach function to callback
        self.client.on_message = self.on_message  # attach function to callback
        self.client.on_publish = self.on_publish  # attach function to callback

        print("Connecting to broker")
        # connect to broker
        self.client.connect(broker_address, port=mqtt_port)

        #################        start MQTT CLIENT thread            ##################
        self.client.loop_start()
        print("Connected to MQTT")

    ####### alert MQTT #######
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT service connected to broker, subscription done.")

        else:
            print("MQTT service Connection failed")

    def on_disconnect(self, client, userdata, rc=0):
        print("MQTT service disconnected")

    def on_publish(self, client, userdata, result):  # create function for callback
        print("message published")
        pass

    def on_message(self, client, inference_thread_manager, message):
        '''
        Note that you must subscribe a topic to be able to receive messages (and of course a message must be published on this topic)
        '''
        if message.topic == self.function_topic_in:
            message_received = json.loads(str(message.payload.decode("utf-8")))
            if("name" in message_received):
                if message_received["name"] in self.subscriptions:
                    # We subscribed to this. We can run the callback that is attached to that name.
                    b = globals()[self.subscriptions[message_received["name"]]](
                        message_received["parameters"])
                    response = {
                        "name": message_received["name"],
                        "call_id": message_received["id"],
                        "status": 0,
                        "result": {
                            "success": b
                        }
                    }
                    self.client.publish(self.function_topic_out, json.dumps(response))

    def subscribe_callback(self, remote_name: str, callback_name: str):
        self.client.subscribe(self.function_topic_in)
        self.subscriptions[remote_name] = callback_name
        print("Subcribed to topic ")


def addition_callback(params: dict):
    num1 = params["num1"]
    num2 = params["num2"]

    if(isinstance(num1, int) and isinstance(num2, int)):
        result = num1 + num2
        log = "Addition called : " + \
            str(num1) + " + " + str(num2) + " = " + str(result)
        sliot.HubClient.send_log(log, sliot.LOG_LEVEL.INFO)
        return True

    else:
        print("There was an issue with the parameters type.")
    return False


def main():
    # initialize the communication to zed hub, with a zed camera.
    mqtt = slMqttClient()
    zed = sl.Camera()
    status = sliot.HubClient.connect("streaming_app")

    if status != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status)
        exit()

    status = sliot.HubClient.register_camera(zed)
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status)
        exit()

    # Open the zed camera
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD2K
    init_params.depth_mode = sl.DEPTH_MODE.NONE

    status = zed.open(init_params)

    if status != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log(
            "Camera initialization error : " + str(status), sliot.LOG_LEVEL.ERROR)
        exit(1)

    # MQTT subscription
    mqtt.subscribe_callback("tuto05_add", "addition_callback")

    # Main loop
    while True:
        status_zed = zed.grab()
        if status == sl.ERROR_CODE.SUCCESS:

            # In the end of a grab(), always call a update() on the cloud.
            sliot.HubClient.update()
        else:
            break

    print("Grab error ", status)
    if zed.is_opened():
        zed.close()

    # Close the communication with zed hub properly.
    status = sliot.HubClient.disconnect()
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status)
        exit()

    return


if __name__ == "__main__":
    main()
