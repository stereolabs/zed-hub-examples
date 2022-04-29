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
import cv2
import numpy as np
import paho.mqtt.client as mqttClient
import json
import os
from threading import Thread, Lock

# Parameters, defined as global variables
draw_bboxes = False
recordVideoEvent = True
nbFramesNoDetBtw2Events = 30
recordTelemetry = True
telemetryFreq = 10.0
sdk_guard = Lock()
zed = sl.Camera()
init_params = sl.InitParameters()

class slMqttClient:
    def __init__(self):
        if os.path.exists('/usr/local/sl_iot/settings/env.json'):
            f = open('/usr/local/sl_iot/settings/env.json')
            variables = json.load(f)
            # print(json.dumps(variables, indent=4, sort_keys=False))
            for key in variables.keys():
                if(key in os.environ):
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
        app_token = os.environ.get(
            "SL_APPLICATION_TOKEN")  # Connection password

        app_name = os.environ.get("SL_APPLICATION_NAME")  # Connection password
        self.device_id = str(os.environ.get("SL_DEVICE_ID"))
        logs_topic = "/v1/devices/" + self.device_id + "/logs"

        # Topic where the cloud publishes parameter modifications
        self.app_ID = str(os.environ.get("SL_APPLICATION_ID"))

        self.subscriptions = {}
        """
        client that listen to the app parameter modifications
        """
        client_id = "sample_object_detection"

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

    def subscribe_callback(self, remote_name: str, callback_name: str, callback_type: sliot.CALLBACK_TYPE, parameter_type: sliot.PARAMETER_TYPE):
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
            self.subscriptions[topic][remote_name] = callback_name
            print("Subcribed to topic ")


    def on_message(self, client, inference_thread_manager, message):
        '''
        Note that you must subscribe a topic to be able to receive messages (and of course a message must be published on this topic)
        '''
        if message.topic in self.subscriptions:
            message_received = json.loads(str(message.payload.decode()))
            # print(message_received)
            # check all subscriptions
            for remote_name in self.subscriptions[message.topic].keys():
                # if a subscription fits with the remote name we received
                if ("parameters.requested." + remote_name in message_received) or ('name' in message_received and message_received['name'] == remote_name):
                    # call the stored callback
                    print(message_received)
                    callback_name = self.subscriptions[message.topic][remote_name]
                    b = globals()[callback_name](message_received)

                    ## If it's a remote call, we need to respond.
                    if message.topic.endswith("/functions/in"):
                        response = {
                            "name": message_received["name"],
                            "call_id": message_received["id"],
                            "status": 0,
                            "result": {
                                "success": b
                            }
                        }
                        self.client.publish(message.topic.replace("/functions/in", "/functions/out"), json.dumps(response))

# def on_display_parameters_update():
#     global draw_bboxes
#     print("Display parameter updated.")
#     draw_bboxes = sliot.HubClient.get_parameter_bool(
#         "draw_bboxes", sliot.PARAMETER_TYPE.DEVICE)
#     sliot.HubClient.send_log(
#         "New parameter : draw_bboxes modified to " + str(draw_bboxes), sliot.LOG_LEVEL.INFO)
#     return True


def on_video_event_update(message_received):
    global recordVideoEvent
    global nbFramesNoDetBtw2Events
    print("Video event updated")
    recordVideoEvent = sliot.HubClient.get_parameter_bool(
        "recordVideoEvent", sliot.PARAMETER_TYPE.DEVICE, recordVideoEvent)
    nbFramesNoDetBtw2Events = sliot.HubClient.get_parameter_int(
        "nbFramesNoDetBtw2Events", sliot.PARAMETER_TYPE.DEVICE, nbFramesNoDetBtw2Events)
    sliot.HubClient.send_log(
        "New parameters : recordVideoEvent or nbFramesNoDetBtw2Events modified", sliot.LOG_LEVEL.INFO)


def on_telemetry_update(message_received):
    global recordTelemetry
    global telemetryFreq
    print("telemetry updated")
    recordTelemetry = sliot.HubClient.get_parameter_bool(
        "recordTelemetry", Psliot.PARAMETER_TYPE.DEVICE, recordTelemetry)
    telemetryFreq = sliot.HubClient.get_parameter_float(
        "telemetryFreq", sliot.PARAMETER_TYPE.DEVICE, telemetryFreq)
    sliot.HubClient.send_log(
        "New parameters : recordTelemetry or telemetryFreq modified", sliot.LOG_LEVEL.INFO)

#
# \brief Callback generated when init parameters have been changed on the cloud interface
# \param event from FunctionEvent
#
def on_init_param_change(message_received):
    global sdk_guard
    global zed
    global init_params

    sliot.HubClient.send_log("Init parameters update. Re-opening the camera.", sliot.LOG_LEVEL.INFO)
    sdk_guard.acquire()
    zed.close()
    update_init_params_from_cloud(init_params)
    zed.open(init_params)
    sdk_guard.release()

#
# \brief Callback generated when GAMMA video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_gamma_update(message_received):
    global sdk_guard
    global zed
    sdk_guard.acquire()
    curr_gamma = zed.get_camera_settings(sl.VIDEO_SETTINGS.GAMMA)
    gamma = sliot.HubClient.get_parameter_int("camera_gamma", sliot.PARAMETER_TYPE.DEVICE, int(curr_gamma))
    zed.set_camera_settings(sl.VIDEO_SETTINGS.GAMMA, gamma)
    sdk_guard.release();
    sliot.HubClient.purge_video_stream()
    sliot.HubClient.report_parameter("camera_gamma", sliot.PARAMETER_TYPE.DEVICE, gamma);

#
# \brief Callback generated when GAMMA video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_gain_update(message_received):
    global sdk_guard
    global zed
    sdk_guard.acquire();
    curr_gain = zed.get_camera_settings(sl.VIDEO_SETTINGS.GAIN)
    gain = sliot.HubClient.get_parameter_int("camera_gain", sliot.PARAMETER_TYPE.DEVICE, int(curr_gain))
    zed.set_camera_settings(sl.VIDEO_SETTINGS.GAIN, gain)
    sdk_guard.release();
    sliot.HubClient.purge_video_stream()
    sliot.HubClient.report_parameter("camera_gain", sliot.PARAMETER_TYPE.DEVICE, gain)

#
# \brief Callback generated when AEC/AGC video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_autoexposure_update(message_received):

    global sdk_guard
    global zed
    sdk_guard.acquire()
    curr_auto_exposure = zed.get_camera_settings(sl.VIDEO_SETTINGS.AEC_AGC)
    auto_exposure = sliot.HubClient.get_parameter_bool("camera_auto_exposure", sliot.PARAMETER_TYPE.DEVICE, bool(curr_auto_exposure));
    zed.set_camera_settings(sl.VIDEO_SETTINGS.AEC_AGC, auto_exposure)
    sdk_guard.release()
    sliot.HubClient.purge_video_stream()
    sliot.HubClient.report_parameter("camera_auto_exposure", sliot.PARAMETER_TYPE.DEVICE, auto_exposure);

#
# \brief Callback generated when Exposure video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_exposure_update(message_received):
    global sdk_guard
    global zed
    sdk_guard.acquire()
    curr_exposure = zed.get_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE)
    exposure = sliot.HubClient.get_parameter_int("camera_exposure", sliot.PARAMETER_TYPE.DEVICE, int(curr_exposure))
    zed.set_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE, exposure)
    sdk_guard.release()
    sliot.HubClient.purge_video_stream()
    sliot.HubClient.report_parameter("camera_exposure", sliot.PARAMETER_TYPE.DEVICE, exposure)

#
# \brief Callback generated when the ap parameter local_stream has been modified in the interface.
# the stream mode of the zed is enabled or disabled depending on the value
# \param event from FunctionEvent
#
def on_local_stream_update(message_received):
    global sdk_guard
    global zed
    local_stream_change = True
    local_stream = sliot.HubClient.get_parameter_bool("local_stream", PARAMETER_TYPE.APPLICATION, False)

    if (local_stream):
        stream_param = sl.StreamingParameters()
        stream_param.codec = sl.STREAMING_CODEC.H264

        # restart streaming with new parameters
        zed.disable_streaming()
        zed_error = zed.enable_streaming(stream_param);
        if (zed_error != sl.ERROR_CODE.SUCCESS):
            print("[onAppStreamParamUpdate] " << str(zed_error) << "\nExit program.");
            zed.close()
            exit(1)
    else:
        zed.disable_streaming()

def update_init_params_from_cloud(init_params: sl.InitParameters):
    reso_str = sliot.HubClient.get_parameter_string(
        "camera_resolution", sliot.PARAMETER_TYPE.DEVICE, str(init_params.camera_resolution))
    if (reso_str == "HD2K"):
        init_params.camera_resolution = sl.RESOLUTION.HD2K
    elif (reso_str == "HD720"):
        init_params.camera_resolution = sl.RESOLUTION.HD720
    elif (reso_str == "HD1080"):
        init_params.camera_resolution = sl.RESOLUTION.HD1080
    elif (reso_str == "WVGA"):
        init_params.camera_resolution = sl.RESOLUTION.VGA

    sliot.HubClient.report_parameter(
        "camera_resolution", sliot.PARAMETER_TYPE.DEVICE, reso_str)

    init_params.camera_image_flip = sl.FLIP_MODE(sliot.HubClient.get_parameter_int(
        "camera_image_flip", sliot.PARAMETER_TYPE.DEVICE, int(init_params.camera_image_flip.value)))
    sliot.HubClient.report_parameter(
        "camera_image_flip", sliot.PARAMETER_TYPE.DEVICE, int(init_params.camera_image_flip.value))

    init_params.camera_fps = sliot.HubClient.get_parameter_int(
        "camera_fps", sliot.PARAMETER_TYPE.DEVICE, init_params.camera_fps)
    sliot.HubClient.report_parameter(
        "camera_fps", sliot.PARAMETER_TYPE.DEVICE, (int)(init_params.camera_fps))


def main():
    global sdk_guard
    global zed
    global init_params

    mqtt = slMqttClient()

    # initialize the communication to zed hub, with a zed camera.
    zed = sl.Camera()
    status = sliot.HubClient.connect("camera_viewer_sample")

    if status != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status)
        exit()

    status = sliot.HubClient.register_camera(zed)
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status)
        exit()

    status = sliot.HubClient.load_application_parameters("parameters.json")
    if status != sliot.STATUS_CODE.SUCCESS:
        print("parameters.json file not found or malformated", status)
        exit()

    # Setup init parameters
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD2K
    init_params.depth_mode = sl.DEPTH_MODE.NONE
    init_params.sdk_verbose = True
    init_params.sdk_gpu_id = -1

    # Get Init Parameters from cloud parameters
    update_init_params_from_cloud(init_params)

    # Override parameters
    init_params.sensors_required = True

    status = zed.open(init_params)

    if status != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log(
            "Camera initialization error : " + str(status), sliot.LOG_LEVEL.ERROR)
        exit(1)

    # Setup callback for parameters
    # PARAMETER_TYPE.APPLICATION is only suitable for dockerized apps, like this sample.
    # If you want to test this on your machine, you'd better switch all your subscriptions to PARAMETER_TYPE.DEVICE.
    mqtt.subscribe_callback("camera_resolution", "on_init_param_change",
                            sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    mqtt.subscribe_callback("camera_fps", "on_init_param_change",
                            sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    mqtt.subscribe_callback("camera_image_flip", "on_init_param_change",
                            sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)

    mqtt.subscribe_callback(
        "camera_auto_exposure", "on_autoexposure_update", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    mqtt.subscribe_callback(
        "camera_exposure", "on_exposure_update", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    mqtt.subscribe_callback(
        "camera_gain", "on_gain_update", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    mqtt.subscribe_callback(
        "camera_gamma", "on_gamma_update", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    mqtt.subscribe_callback(
        "local_stream", "on_local_stream_update", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)

    # local stream initial setting
    local_stream = sliot.HubClient.get_parameter_bool(
        "local_stream", sliot.PARAMETER_TYPE.APPLICATION, False)
    if (local_stream):
        stream_param = sl.StreamingParameters()
        stream_param.codec = sl.STREAMING_CODEC.H264
        zed.enable_streaming(stream_param)

    sliot.HubClient.report_parameter("local_stream", sliot.PARAMETER_TYPE.APPLICATION, local_stream)

    # Main loop
    while True:

        # the callback on_init_param_change might close and reopen the camera to load new init params
        # this mutex block the grab until the callback releases it
        sdk_guard.acquire()
        status_zed = zed.grab()
        sdk_guard.release()

        if status_zed == sl.ERROR_CODE.SUCCESS:
            sliot.HubClient.update()
        else:
            size_devices = len(sl.Camera.get_device_list())
            sliot.HubClient.send_log("Camera grab error: " + str(status_zed) +
                                     ". ( Number of camera detected : " + str(size_devices) + " ) ", sliot.LOG_LEVEL.ERROR)
            break

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
