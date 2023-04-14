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


def main():
    # Initialize the communication to ZED Hub, with a zed camera.
    zed = sl.Camera() 
    status_hub = hub.HubClient.connect("streaming_app")

    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_hub)
        exit(1)

    # Open the zed camera
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD2K
    init_params.depth_mode = sl.DEPTH_MODE.PERFORMANCE
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

    depth = sl.Mat()
    
    # Main loop
    while True:
        status_zed = zed.grab()
        if status_zed != sl.ERROR_CODE.SUCCESS:
            break

        # Do what you want with the data from the camera.
        # For examples of what you can do with the zed camera, visit https://github.com/stereolabs/zed-examples
        # For example, you can retrieve a depth image.
        zed.retrieve_image(depth, sl.VIEW.DEPTH)

        # Always update Hub at the end of the grab loop
        # without giving a sl.Mat, it will retrieve the RGB image automatically.
        # without giving a registered camera, it will try to update all registered cameras.
        hub.HubClient.update(zed, depth)

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
