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

class slMqttClient:
    def __init__(self):
        f = open('/usr/local/sl_iot/settings/env.json')
        variables = json.load(f)
        # print(json.dumps(variables, indent=4, sort_keys=False))
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
        app_token = os.environ.get("SL_APPLICATION_TOKEN")  # Connection password

        app_name = os.environ.get("SL_APPLICATION_NAME")  # Connection password
        device_id = str(os.environ.get("SL_DEVICE_ID"))
        logs_topic = "/v1/devices/" + device_id + "/logs"

        ## Topic where the cloud publishes parameter modifications
        app_ID = str(os.environ.get("SL_APPLICATION_ID"))
        # self.update_app_param_topic = "/v1/devices/" + device_id + "/apps/"+ app_ID + "/twin/update"
        self.update_app_param_topic = "/v1/devices/" + device_id + "/twin/update"

        """
        client that listen to the app parameter modifications
        """
        client_id = "tutorial_4_applications_parameters"

        self.client = mqttClient.Client(client_id)  # create new instance

        print("Connecting MQTT")
        # the callback is handled directly with MQTT, unlike in C++
        #############     Get the environment variables      ##################
        self.client.username_pw_set(mqtt_user, password=app_token)  # set username and password

        self.client.on_connect = self.on_connect  # attach function to callback
        self.client.on_disconnect = self.on_disconnect  # attach function to callback
        self.client.on_message = self.on_message  # attach function to callback
        self.client.on_publish = self.on_publish  # attach function to callback

        print("Connecting to broker")
        self.client.connect(broker_address, port=mqtt_port)  # connect to broker

        #################        start MQTT CLIENT thread            ##################
        self.client.loop_start()
        print("Connected to MQTT")

    ####### alert MQTT #######
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT service connected to broker. Subscribing...")
            self.client.subscribe(self.update_app_param_topic) 
            
        else:
            print("MQTT service Connection failed")


    def on_disconnect(self, client, userdata,rc=0):
        print("MQTT service disconnected")


    def on_publish(self, client, userdata, result):  # create function for callback
        print("message published")
        pass


    def on_message(self, client, inference_thread_manager, message):
        '''
        Note that you must subscribe a topic to be able to receive messages (and of course a message must be published on this topic)
        '''

        if message.topic == self.update_app_param_topic:
            # print("New parameter update received")
            new_app_parameters = json.loads(str(message.payload.decode()))
            # print (new_app_parameters)
            if "parameters.requested.led_status" in new_app_parameters:
                global led_status_updated
                led_status_updated = True
            # update_parameters(new_app_parameters)

def main():
    # initialize the communication to zed hub, with a zed camera.
    global led_status_updated
    led_status_updated = False
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
        sliot.HubClient.send_log("Camera initialization error : " + str(status), sliot.LOG_LEVEL.ERROR)
        exit(1)

    # Main loop
    while True:
        status_zed = zed.grab()
        if status == sl.ERROR_CODE.SUCCESS:

            if(led_status_updated):
                curr_led_status = zed.get_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS)
                led_status = sliot.HubClient.get_parameter_bool("led_status", sliot.PARAMETER_TYPE.DEVICE, curr_led_status)
                sliot.HubClient.report_parameter("led_status", sliot.PARAMETER_TYPE.DEVICE, led_status)
                zed.set_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS, led_status)
                led_status_updated = False
                print("updated to ", led_status)

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
