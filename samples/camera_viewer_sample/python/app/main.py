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
    recordVideoEvent = sliot.HubClient.get_parameter_bool(
        "recordVideoEvent", sliot.PARAMETER_TYPE.APPLICATION, recordVideoEvent)
    nbFramesNoDetBtw2Events = sliot.HubClient.get_parameter_int(
        "nbFramesNoDetBtw2Events", sliot.PARAMETER_TYPE.APPLICATION, nbFramesNoDetBtw2Events)
    sliot.HubClient.send_log(
        "New parameters : recordVideoEvent or nbFramesNoDetBtw2Events modified", sliot.LOG_LEVEL.INFO)


def on_telemetry_update(message_received):
    global recordTelemetry
    global telemetryFreq
    print("telemetry updated")
    recordTelemetry = sliot.HubClient.get_parameter_bool(
        "recordTelemetry", sliot.PARAMETER_TYPE.APPLICATION, recordTelemetry)
    telemetryFreq = sliot.HubClient.get_parameter_float(
        "telemetryFreq", sliot.PARAMETER_TYPE.APPLICATION, telemetryFreq)
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
# \brief Callback generated when led status have been changed on the cloud interface
# \param event from FunctionEvent
#
def on_led_status_update(event : sliot.FunctionEvent):
    global zed
    global sdk_guard    
    curr_led_status = zed.get_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS)
    led_status = sliot.HubClient.get_parameter_bool("led_status", sliot.PARAMETER_TYPE.APPLICATION, bool(curr_led_status))
    sliot.HubClient.report_parameter("led_status", sliot.PARAMETER_TYPE.APPLICATION, led_status)
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
    gamma = sliot.HubClient.get_parameter_int("camera_gamma", sliot.PARAMETER_TYPE.APPLICATION, int(curr_gamma))
    zed.set_camera_settings(sl.VIDEO_SETTINGS.GAMMA, gamma)
    sdk_guard.release();
    sliot.HubClient.purge_video_stream()
    sliot.HubClient.report_parameter("camera_gamma", sliot.PARAMETER_TYPE.APPLICATION, gamma);

#
# \brief Callback generated when GAMMA video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_gain_update(message_received):
    global sdk_guard
    global zed
    sdk_guard.acquire();
    curr_gain = zed.get_camera_settings(sl.VIDEO_SETTINGS.GAIN)
    gain = sliot.HubClient.get_parameter_int("camera_gain", sliot.PARAMETER_TYPE.APPLICATION, int(curr_gain))
    zed.set_camera_settings(sl.VIDEO_SETTINGS.GAIN, gain)
    sdk_guard.release();
    sliot.HubClient.purge_video_stream()
    sliot.HubClient.report_parameter("camera_gain", sliot.PARAMETER_TYPE.APPLICATION, gain)


#
# \brief Callback generated when AEC/AGC video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_autoexposure_update(message_received):

    global sdk_guard
    global zed
    sdk_guard.acquire()
    curr_auto_exposure = zed.get_camera_settings(sl.VIDEO_SETTINGS.AEC_AGC)
    auto_exposure = sliot.HubClient.get_parameter_bool("camera_auto_exposure", sliot.PARAMETER_TYPE.APPLICATION, bool(curr_auto_exposure));
    zed.set_camera_settings(sl.VIDEO_SETTINGS.AEC_AGC, auto_exposure)
    sdk_guard.release()
    sliot.HubClient.purge_video_stream()
    sliot.HubClient.report_parameter("camera_auto_exposure", sliot.PARAMETER_TYPE.APPLICATION, auto_exposure);


#
# \brief Callback generated when Exposure video settings has been changed on the cloud interface
# \param event from FunctionEvent
#
def on_exposure_update(message_received):
    global sdk_guard
    global zed
    sdk_guard.acquire()
    curr_exposure = zed.get_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE)
    exposure = sliot.HubClient.get_parameter_int("camera_exposure", sliot.PARAMETER_TYPE.APPLICATION, int(curr_exposure))
    zed.set_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE, exposure)
    sdk_guard.release()
    sliot.HubClient.purge_video_stream()
    sliot.HubClient.report_parameter("camera_exposure", sliot.PARAMETER_TYPE.APPLICATION, exposure)


#
# \brief Callback generated when the ap parameter local_stream has been modified in the interface.
# the stream mode of the zed is enabled or disabled depending on the value
# \param event from FunctionEvent
#
def on_local_stream_update(message_received):
    global sdk_guard
    global zed
    local_stream_change = True
    local_stream = sliot.HubClient.get_parameter_bool("local_stream", sliot.PARAMETER_TYPE.APPLICATION, False)

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
    reso_str = sliot.HubClient.get_parameter_string(
        "camera_resolution", sliot.PARAMETER_TYPE.APPLICATION, str(init_params.camera_resolution))
    if reso_str == "HD2K":
        init_params.camera_resolution = sl.RESOLUTION.HD2K
    elif reso_str == "HD720":
        init_params.camera_resolution = sl.RESOLUTION.HD720
    elif reso_str == "HD1080":
        init_params.camera_resolution = sl.RESOLUTION.HD1080
    elif reso_str == "WVGA":
        init_params.camera_resolution = sl.RESOLUTION.VGA

    sliot.HubClient.report_parameter(
        "camera_resolution", sliot.PARAMETER_TYPE.APPLICATION, reso_str)

    init_params.camera_image_flip = sl.FLIP_MODE(sliot.HubClient.get_parameter_int(
        "camera_image_flip", sliot.PARAMETER_TYPE.APPLICATION, int(init_params.camera_image_flip.value)))
    sliot.HubClient.report_parameter(
        "camera_image_flip", sliot.PARAMETER_TYPE.APPLICATION, int(init_params.camera_image_flip.value))

    init_params.camera_fps = sliot.HubClient.get_parameter_int(
        "camera_fps", sliot.PARAMETER_TYPE.APPLICATION, init_params.camera_fps)
    sliot.HubClient.report_parameter(
        "camera_fps", sliot.PARAMETER_TYPE.APPLICATION, (int)(init_params.camera_fps))


def main():
    global sdk_guard
    global zed
    global init_params

    # Initialize the communication to ZED Hub, with a zed camera.
    zed = sl.Camera()
    status_iot = sliot.HubClient.connect("camera_viewer_sample")

    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_iot)
        exit(1)

    status_iot = sliot.HubClient.register_camera(zed)
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status_iot)
        exit(1)

    status_iot = sliot.HubClient.load_application_parameters("parameters.json")
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("parameters.json file not found or malformated", status_iot)
        exit(1)

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

    # Setup callbacks for parameters
    # PARAMETER_TYPE.APPLICATION is only suitable for dockerized apps, like this sample.
    # If you want to test this on your machine, you'd better switch all your subscriptions to PARAMETER_TYPE.DEVICE.

    # general parameters
    callback_param_led = sliot.CallbackParameters()
    callback_param_led.set_parameter_callback("onLedStatusChange", "led_status", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_led_status_update, callback_param_led)

    callback_param_flip = sliot.CallbackParameters()
    callback_param_flip.set_parameter_callback("on_init_param_change", "camera_image_flip", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_init_param_change, callback_param_flip)

    callback_param_fps = sliot.CallbackParameters()
    callback_param_fps.set_parameter_callback("on_init_param_change", "camera_fps", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_init_param_change, callback_param_fps)

    callback_param_res = sliot.CallbackParameters()
    callback_param_res.set_parameter_callback("on_init_param_change", "camera_resolution", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_init_param_change, callback_param_res)

    # video parameters
    callback_param_autoexp = sliot.CallbackParameters()
    callback_param_autoexp.set_parameter_callback("on_autoexposure_update", "camera_auto_exposure", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_autoexposure_update, callback_param_autoexp)

    callback_param_exp = sliot.CallbackParameters()
    callback_param_exp.set_parameter_callback("on_exposure_update", "camera_exposure", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_exposure_update, callback_param_exp)

    callback_param_gain = sliot.CallbackParameters()
    callback_param_gain.set_parameter_callback("on_gain_update", "camera_gain", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_gain_update, callback_param_gain)

    callback_param_gamma = sliot.CallbackParameters()
    callback_param_gamma.set_parameter_callback("on_gamma_update", "camera_gamma", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_gamma_update, callback_param_gamma)

    callback_param_stream = sliot.CallbackParameters()
    callback_param_stream.set_parameter_callback("on_local_stream_update", "local_stream", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.APPLICATION)
    sliot.HubClient.register_function(on_local_stream_update, callback_param_stream)

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

    # Close the communication with ZED Hub properly.
    status = sliot.HubClient.disconnect()
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status)
        exit(1)

    return


if __name__ == "__main__":
    main()
