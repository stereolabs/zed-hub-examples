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
import pyzed.sl_hub as hub
import os
from threading import Lock

# Parameters, defined as global variables
draw_bboxes = False
recordVideoEvent = True
nbFramesNoDetBtw2Events = 30
recordTelemetry = True
telemetryFreq = 10.0
sdk_guard = Lock()
zed = sl.Camera()
init_params = sl.InitParameters()



def on_video_event_update(message_received):
    global recordVideoEvent
    global nbFramesNoDetBtw2Events
    print("Video event updated")
    recordVideoEvent = hub.HubClient.get_parameter_bool(
        "recordVideoEvent", hub.PARAMETER_TYPE.APPLICATION, recordVideoEvent)
    nbFramesNoDetBtw2Events = hub.HubClient.get_parameter_int(
        "nbFramesNoDetBtw2Events", hub.PARAMETER_TYPE.APPLICATION, nbFramesNoDetBtw2Events)
    hub.HubClient.send_log(
        "New parameters : recordVideoEvent or nbFramesNoDetBtw2Events modified", hub.LOG_LEVEL.INFO)


def on_telemetry_update(message_received):
    global recordTelemetry
    global telemetryFreq
    print("telemetry updated")
    recordTelemetry = hub.HubClient.get_parameter_bool(
        "recordTelemetry", hub.PARAMETER_TYPE.APPLICATION, recordTelemetry)
    telemetryFreq = hub.HubClient.get_parameter_float(
        "telemetryFreq", hub.PARAMETER_TYPE.APPLICATION, telemetryFreq)
    hub.HubClient.send_log(
        "New parameters : recordTelemetry or telemetryFreq modified", hub.LOG_LEVEL.INFO)


#
# \brief Callback generated when init parameters have been changed on the cloud interface
# \param event from FunctionEvent
#
def on_init_param_change(message_received):
    global sdk_guard
    global zed
    global init_params

    hub.HubClient.send_log("Init parameters update. Re-opening the camera.", hub.LOG_LEVEL.INFO)
    sdk_guard.acquire()
    zed.close()
    update_init_params_from_cloud(init_params)
    zed.open(init_params)
    sdk_guard.release()
#
# \brief Callback generated when led status have been changed on the cloud interface
# \param event from FunctionEvent
#
def on_led_status_update(event : hub.FunctionEvent):
    global zed
    global sdk_guard    
    curr_led_status = zed.get_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS)
    led_status = hub.HubClient.get_parameter_bool("led_status", hub.PARAMETER_TYPE.APPLICATION, bool(curr_led_status))
    hub.HubClient.report_parameter("led_status", hub.PARAMETER_TYPE.APPLICATION, led_status)
    zed.set_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS, led_status)

#
# \brief Callback generated when GAMMA video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_gamma_update(message_received):
    global sdk_guard
    global zed
    sdk_guard.acquire()
    curr_gamma = zed.get_camera_settings(sl.VIDEO_SETTINGS.GAMMA)
    gamma = hub.HubClient.get_parameter_int("camera_gamma", hub.PARAMETER_TYPE.APPLICATION, int(curr_gamma))
    zed.set_camera_settings(sl.VIDEO_SETTINGS.GAMMA, gamma)
    sdk_guard.release();
    hub.HubClient.purge_video_stream()
    hub.HubClient.report_parameter("camera_gamma", hub.PARAMETER_TYPE.APPLICATION, gamma);

#
# \brief Callback generated when GAMMA video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_gain_update(message_received):
    global sdk_guard
    global zed
    sdk_guard.acquire();
    curr_gain = zed.get_camera_settings(sl.VIDEO_SETTINGS.GAIN)
    gain = hub.HubClient.get_parameter_int("camera_gain", hub.PARAMETER_TYPE.APPLICATION, int(curr_gain))
    zed.set_camera_settings(sl.VIDEO_SETTINGS.GAIN, gain)
    sdk_guard.release();
    hub.HubClient.purge_video_stream()
    hub.HubClient.report_parameter("camera_gain", hub.PARAMETER_TYPE.APPLICATION, gain)


#
# \brief Callback generated when AEC/AGC video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_autoexposure_update(message_received):

    global sdk_guard
    global zed
    sdk_guard.acquire()
    curr_auto_exposure = zed.get_camera_settings(sl.VIDEO_SETTINGS.AEC_AGC)
    auto_exposure = hub.HubClient.get_parameter_bool("camera_auto_exposure", hub.PARAMETER_TYPE.APPLICATION, bool(curr_auto_exposure));
    zed.set_camera_settings(sl.VIDEO_SETTINGS.AEC_AGC, auto_exposure)
    sdk_guard.release()
    hub.HubClient.purge_video_stream()
    hub.HubClient.report_parameter("camera_auto_exposure", hub.PARAMETER_TYPE.APPLICATION, auto_exposure);


#
# \brief Callback generated when Exposure video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_exposure_update(message_received):
    global sdk_guard
    global zed
    sdk_guard.acquire()
    curr_exposure = zed.get_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE)
    exposure = hub.HubClient.get_parameter_int("camera_exposure", hub.PARAMETER_TYPE.APPLICATION, int(curr_exposure))
    zed.set_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE, exposure)
    sdk_guard.release()
    hub.HubClient.purge_video_stream()
    hub.HubClient.report_parameter("camera_exposure", hub.PARAMETER_TYPE.APPLICATION, exposure)


#
# \brief Callback generated when the ap parameter local_stream has been modified in the interface.
# the stream mode of the zed is enabled or disabled depending on the value
# \param event from FunctionEvent
#
def on_local_stream_update(message_received):
    global sdk_guard
    global zed
    local_stream_change = True
    local_stream = hub.HubClient.get_parameter_bool("local_stream", hub.PARAMETER_TYPE.APPLICATION, False)

    if local_stream:
        stream_param = sl.StreamingParameters()
        stream_param.codec = sl.STREAMING_CODEC.H264

        # restart streaming with new parameters
        zed.disable_streaming()
        zed_error = zed.enable_streaming(stream_param)
        if (zed_error != sl.ERROR_CODE.SUCCESS):
            print("[onAppStreamParamUpdate] " + str(zed_error) + "\nExit program.");
            zed.close()
            exit(1)
    else:
        zed.disable_streaming()


def update_init_params_from_cloud(init_params: sl.InitParameters):
    reso_str = hub.HubClient.get_parameter_string(
        "camera_resolution", hub.PARAMETER_TYPE.APPLICATION, str(init_params.camera_resolution))
    if reso_str == "HD2K":
        init_params.camera_resolution = sl.RESOLUTION.HD2K
    elif reso_str == "HD720":
        init_params.camera_resolution = sl.RESOLUTION.HD720
    elif reso_str == "HD1080":
        init_params.camera_resolution = sl.RESOLUTION.HD1080
    elif reso_str == "WVGA":
        init_params.camera_resolution = sl.RESOLUTION.VGA

    hub.HubClient.report_parameter(
        "camera_resolution", hub.PARAMETER_TYPE.APPLICATION, reso_str)

    init_params.camera_image_flip = sl.FLIP_MODE(hub.HubClient.get_parameter_int(
        "camera_image_flip", hub.PARAMETER_TYPE.APPLICATION, int(init_params.camera_image_flip.value)))
    hub.HubClient.report_parameter(
        "camera_image_flip", hub.PARAMETER_TYPE.APPLICATION, int(init_params.camera_image_flip.value))

    init_params.camera_fps = hub.HubClient.get_parameter_int(
        "camera_fps", hub.PARAMETER_TYPE.APPLICATION, init_params.camera_fps)
    hub.HubClient.report_parameter(
        "camera_fps", hub.PARAMETER_TYPE.APPLICATION, (int)(init_params.camera_fps))


def main():
    global sdk_guard
    global zed
    global init_params

    # Create ZED Object
    zed = sl.Camera()

    # Initialize the communication to ZED Hub, with a zed camera.
    status_hub = hub.HubClient.connect("camera_viewer_sample")
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_hub)
        exit(1)

    # Load application parameter file in development mode
    application_token = os.getenv("SL_APPLICATION_TOKEN")
    if application_token == None:
        status_hub = hub.HubClient.load_application_parameters("parameters.json")
        if status_hub != hub.STATUS_CODE.SUCCESS:
            print("parameters.json file not found or malformated")
            exit(1)

    # Init logger (optional)
    hub.HubClient.set_log_level_threshold(hub.LOG_LEVEL.DEBUG, hub.LOG_LEVEL.DEBUG)

    # Setup Init Parameters
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD2K
    init_params.depth_mode = sl.DEPTH_MODE.NONE
    init_params.sdk_verbose = True
    init_params.sdk_gpu_id = -1

    # Get Init Parameters from cloud parameters
    update_init_params_from_cloud(init_params)

    # Override parameters
    init_params.sdk_verbose = True
    init_params.sensors_required = True

    # Open the ZED camera
    status = zed.open(init_params)
    if status != sl.ERROR_CODE.SUCCESS:
        hub.HubClient.send_log(
            "Camera initialization error : " + str(status), hub.LOG_LEVEL.ERROR)
        exit(1)

    # Register the camera once it's open
    update_params = hub.UpdateParameters()
    status_hub = hub.HubClient.register_camera(zed, update_params)
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status_hub)
        exit(1)

    # Setup callbacks for parameters
    # PARAMETER_TYPE.APPLICATION is only suitable for dockerized apps, like this sample.
    # If you want to test this on your machine, you'd better switch all your subscriptions to PARAMETER_TYPE.DEVICE.

    # general parameters
    callback_param_led = hub.CallbackParameters()
    callback_param_led.set_parameter_callback("onLedStatusChange", "led_status", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_led_status_update, callback_param_led)

    callback_param_flip = hub.CallbackParameters()
    callback_param_flip.set_parameter_callback("on_init_param_change", "camera_image_flip", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_init_param_change, callback_param_flip)

    callback_param_fps = hub.CallbackParameters()
    callback_param_fps.set_parameter_callback("on_init_param_change", "camera_fps", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_init_param_change, callback_param_fps)

    callback_param_res = hub.CallbackParameters()
    callback_param_res.set_parameter_callback("on_init_param_change", "camera_resolution", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_init_param_change, callback_param_res)

    # video parameters
    callback_param_autoexp = hub.CallbackParameters()
    callback_param_autoexp.set_parameter_callback("on_autoexposure_update", "camera_auto_exposure", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_autoexposure_update, callback_param_autoexp)

    callback_param_exp = hub.CallbackParameters()
    callback_param_exp.set_parameter_callback("on_exposure_update", "camera_exposure", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_exposure_update, callback_param_exp)

    callback_param_gain = hub.CallbackParameters()
    callback_param_gain.set_parameter_callback("on_gain_update", "camera_gain", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_gain_update, callback_param_gain)

    callback_param_gamma = hub.CallbackParameters()
    callback_param_gamma.set_parameter_callback("on_gamma_update", "camera_gamma", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_gamma_update, callback_param_gamma)

    callback_param_stream = hub.CallbackParameters()
    callback_param_stream.set_parameter_callback("on_local_stream_update", "local_stream", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_local_stream_update, callback_param_stream)

    # local stream initial setting
    local_stream = hub.HubClient.get_parameter_bool(
        "local_stream", hub.PARAMETER_TYPE.APPLICATION, False)
    if (local_stream):
        stream_param = sl.StreamingParameters()
        stream_param.codec = sl.STREAMING_CODEC.H264
        zed.enable_streaming(stream_param)

    hub.HubClient.report_parameter("local_stream", hub.PARAMETER_TYPE.APPLICATION, local_stream)

    # Main loop
    while True:

        # the callback on_init_param_change might close and reopen the camera to load new init params
        # this mutex block the grab until the callback releases it
        sdk_guard.acquire()
        status_zed = zed.grab()
        sdk_guard.release()

        if status_zed == sl.ERROR_CODE.SUCCESS:
            hub.HubClient.update(zed)
        else:
            size_devices = len(sl.Camera.get_device_list())
            hub.HubClient.send_log("Camera grab error: " + str(status_zed) +
                                     ". ( Number of camera detected : " + str(size_devices) + " ) ", hub.LOG_LEVEL.ERROR)
            break

    if zed.is_opened():
        zed.close()

    # Close the communication with ZED Hub properly.
    status = hub.HubClient.disconnect()
    if status != hub.STATUS_CODE.SUCCESS:
        print("Terminating error ", status)
        exit(1)

    return


if __name__ == "__main__":
    main()
