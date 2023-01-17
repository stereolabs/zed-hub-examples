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

led_status_updated = False


def on_led_status_update(event):
    global led_status_updated
    led_status_updated = True
    print("led status updated !")


def main():
    # Initialize the communication to ZED Hub, with a zed camera.
    global led_status_updated
    led_status_updated = True
    zed = sl.Camera() 
    status_iot = sliot.HubClient.connect("parameter_app")

    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_iot)
        exit(1)

    status_iot = sliot.HubClient.register_camera(zed)
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status_iot)
        exit(1)

    # Open the zed camera
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD2K
    init_params.depth_mode = sl.DEPTH_MODE.NONE
    
    status_zed = zed.open(init_params)
    if status_zed != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log("Camera initialization error : " + str(status_zed), sliot.LOG_LEVEL.ERROR)
        exit(1)

    # Set your parameter callback
    callback_param_led = sliot.CallbackParameters()
    callback_param_led.set_parameter_callback("onLedStatusChange", "led_status", sliot.CALLBACK_TYPE.ON_PARAMETER_UPDATE, sliot.PARAMETER_TYPE.DEVICE)
    sliot.HubClient.register_function(on_led_status_update, callback_param_led)

    # Main loop
    while True:
        status_zed = zed.grab()
        if status_zed != sl.ERROR_CODE.SUCCESS:
            break

        if led_status_updated:
            curr_led_status = zed.get_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS)
            led_status = sliot.HubClient.get_parameter_bool("led_status", sliot.PARAMETER_TYPE.DEVICE, bool(curr_led_status))
            sliot.HubClient.report_parameter("led_status", sliot.PARAMETER_TYPE.DEVICE, led_status)
            zed.set_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS, led_status)
            led_status_updated = False

        # In the end of a grab(), always call a update() on the cloud.
        sliot.HubClient.update()

    print("Grab error ", status_zed)
    # Close the camera
    if zed.is_opened():
        zed.close()

    # Close the communication with ZED Hub properly.
    status_iot = sliot.HubClient.disconnect()
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status_iot)
        exit(1)
    
    return
    

if __name__ == "__main__":
    main()
