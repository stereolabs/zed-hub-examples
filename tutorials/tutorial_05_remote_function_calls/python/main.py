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
import paho.mqtt.client as mqttClient
import os
import json

from typing import Callable


class slMqttClient:
    def __init__(self):
        if os.path.exists('/usr/local/sl_iot/settings/env.json'):
            f = open('/usr/local/sl_iot/settings/env.json')
            variables = json.load(f)
            for key in variables.keys():
                if key in os.environ:
                    print("Original : ", os.environ[key])
                else:
                    os.environ[key] = variables[key]
                print(key, ", ", os.environ[key])

        else:
            print("No env file found in /usr/local/sl_iot/settings/env.json")

        #######################################################################
        #                                                                     #
        #   MQTT configuration   #
        #   The docs are at https://cloud.stereolabs.com/doc/mqtt-api/        #
        #                                                                     #
        #######################################################################
        broker_address = os.environ.get("SL_MQTT_HOST")  # Broker address
        mqtt_port = int(os.environ.get("SL_MQTT_PORT"))  # Broker port
        mqtt_user = "application"  # Connection username
        app_token = os.environ.get("SL_APPLICATION_TOKEN")  # Connection password

        app_name = os.environ.get("SL_APPLICATION_NAME")  # Connection password
        self.device_id = str(os.environ.get("SL_DEVICE_ID"))
        logs_topic = "/v1/devices/" + self.device_id + "/logs"

        # Topic where the cloud publishes parameter modifications
        self.app_ID = str(os.environ.get("SL_APPLICATION_ID"))

        self.subscriptions = {}
        # Client that listens to the app parameter modifications
        client_id = "tutorial_5_remote_function"

        self.client = mqttClient.Client(client_id)  # create new instance

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
            print("MQTT service connected to broker. Subscribing...")
        else:
            print("MQTT service Connection failed")

    def on_disconnect(self, client, userdata, rc=0):
        print("MQTT service disconnected")

    def on_publish(self, client, userdata, result):  # create function for callback
        print("message published")
        pass

    def subscribe_callback(self, remote_name: str, callback: Callable, callback_type: sliot.CALLBACK_TYPE, parameter_type: sliot.PARAMETER_TYPE):
        topic = ""
        parameter_type_addition = ""

        if parameter_type == sliot.PARAMETER_TYPE.APPLICATION:
            parameter_type_addition = "/apps/" + self.app_ID

        if callback_type == sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE:
            topic = "/v1/devices/" + self.device_id + \
                parameter_type_addition + "/twin/update"
        elif callback_type == sliot.CALLBACK_TYPE.ON_REMOTE_CALL:
            topic = "/v1/devices/" + self.device_id + \
                parameter_type_addition + "/functions/in"

        if topic != "":
            self.client.subscribe(topic)
            if topic not in self.subscriptions:
                self.subscriptions[topic] = {}
            self.subscriptions[topic][remote_name] = callback
            print("Subcribed to topic ")

    def on_message(self, client, inference_thread_manager, message):
        """
        Note that you must subscribe a topic to be able to receive messages
        (and of course a message must be published on this topic)
        """
        if message.topic in self.subscriptions:
            message_received = json.loads(str(message.payload.decode()))
            # Check all subscriptions
            for remote_name in self.subscriptions[message.topic].keys():
                # If a subscription fits with the remote name we received
                if ("parameters.requested." + remote_name in message_received) or ('name' in message_received and message_received['name'] == remote_name):
                    # Call the stored callback
                    print(message_received)
                    callback = self.subscriptions[message.topic][remote_name]
                    b = callback(message_received)

                    # If it's a remote call, we need to respond.
                    if message.topic.endswith("/functions/in"):
                        response = {
                            "name": message_received["name"],
                            "call_id": message_received["id"],
                            "status": 0,
                            "result": b
                        }
                        self.client.publish(message.topic.replace("/functions/in", "/functions/out"), json.dumps(response))


def addition_callback(params: dict):
    num1 = params["parameters"]["num1"]
    num2 = params["parameters"]["num2"]

    # Check if parameters are valid
    if isinstance(num1, int) and isinstance(num2, int):
        result = num1 + num2
        # Log your result
        log = "Addition called : " + \
            str(num1) + " + " + str(num2) + " = " + str(result)
        sliot.HubClient.send_log(log, sliot.LOG_LEVEL.INFO)
        return result

    else:
        print("There was an issue with the parameters type.")
    return None


def main():
    mqtt = slMqttClient()
    status_iot = sliot.HubClient.connect("callback_app")

    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_iot)
        exit(1)

    # Setup callback
    # PARAMETER_TYPE.APPLICATION is only suitable for dockerized apps, like this sample.
    # If you want to test this on your machine, you'd better switch all your subscriptions to PARAMETER_TYPE.DEVICE.
    mqtt.subscribe_callback("tuto05_add", addition_callback,
                            sliot.CALLBACK_TYPE.ON_REMOTE_CALL, sliot.PARAMETER_TYPE.DEVICE)

    print("Waiting for remote function to be called.")
    # Main loop
    while True:
        time.sleep(1)

    # Close the communication with ZED Hub properly.
    status = sliot.HubClient.disconnect()
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status)
        exit(1)

    return


if __name__ == "__main__":
    main()
