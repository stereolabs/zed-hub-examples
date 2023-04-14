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

import os
import pyzed.sl as sl
import pyzed.sl_hub as hub

led_status_updated = True
app_param = ""


# Callback on led status update, it sets a boolean to true to turn off/on the led status in the main loop.
def on_led_status_update(event):
    global led_status_updated
    event.status = 0
    led_status_updated = True
    print("led status updated !")

# Callback on app_param update, it log its new value
def on_app_param_update(event):
    global app_param
    event.status = 0
    app_param = hub.HubClient.get_parameter_string("app_param", hub.PARAMETER_TYPE.APPLICATION, app_param)
    print("App Param updated:", app_param)


def main():
    # Initialize the communication to ZED Hub, with a zed camera.
    global led_status_updated
    led_status_updated = True
    zed = sl.Camera() 
    status_hub = hub.HubClient.connect("parameter_app")

    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_hub)
        exit(1)

    # Open the zed camera
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD2K
    init_params.depth_mode = sl.DEPTH_MODE.NONE
    
    status_zed = zed.open(init_params)
    if status_zed != sl.ERROR_CODE.SUCCESS:
        hub.HubClient.send_log("Camera initialization error : " + str(status_zed), hub.LOG_LEVEL.ERROR)
        exit(1)

    # Register the camera once it's open
    update_params = hub.UpdateParameters()
    status_hub = hub.HubClient.register_camera(zed, update_params)
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status_hub)
        exit(1)

    # Load application parameter file in development mode
    application_token = os.getenv("SL_APPLICATION_TOKEN")
    if application_token == None:
        status_hub = hub.HubClient.load_application_parameters("parameters.json")
        if status_hub != hub.STATUS_CODE.SUCCESS:
            print("parameters.json file not found or malformated")
            exit(1)

    # Set your parameter callback
    callback_param_led = hub.CallbackParameters()
    callback_param_led.set_parameter_callback("on_led_status_update", "led_status", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.DEVICE)
    hub.HubClient.register_function(on_led_status_update, callback_param_led)

    callback_app_param = hub.CallbackParameters()
    callback_app_param.set_parameter_callback("on_app_param_update", "app_param", hub.CALLBACK_TYPE.ON_PARAMETER_UPDATE, hub.PARAMETER_TYPE.APPLICATION)
    hub.HubClient.register_function(on_app_param_update, callback_app_param)
    
    # Main loop
    while True:
        # Grab a new frame from the ZED
        status_zed = zed.grab()
        if status_zed != sl.ERROR_CODE.SUCCESS:
            break

        if led_status_updated:
            curr_led_status = zed.get_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS)
            led_status = hub.HubClient.get_parameter_bool("led_status", hub.PARAMETER_TYPE.DEVICE, bool(curr_led_status))
            hub.HubClient.report_parameter("led_status", hub.PARAMETER_TYPE.DEVICE, led_status)
            zed.set_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS, led_status)
            led_status_updated = False

        # Always update Hub at the end of the grab loop
        # without giving a sl::Mat, it will retrieve the RGB image automatically.
        hub.HubClient.update(zed)

    # Handling camera error
    if status_zed != sl.ERROR_CODE.SUCCESS:
        hub.HubClient.send_log("Grab failed, restarting camera. " + str(status_zed),
                                hub.LOG_LEVEL.ERROR)
        zed.close()
        sl.Camera.reboot(zed.get_camera_information().serial_number)
        
    # Close the camera
    if zed.is_opened():
        zed.close()

    # Close the communication with ZED Hub properly.
    status_hub = hub.HubClient.disconnect()
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Terminating error ", status_hub)
        exit(1)
    
    return
    

if __name__ == "__main__":
    main()
