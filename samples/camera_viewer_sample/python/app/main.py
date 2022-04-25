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


def main():
    # initialize the communication to zed hub, with a zed camera.
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

    depth = sl.Mat()
    
    # Main loop
    while True:
        status_zed = zed.grab()
        if status == sl.ERROR_CODE.SUCCESS:

            # Do what you want with the data from the camera.
            # For examples of what you can do with the zed camera, visit https://github.com/stereolabs/zed-examples

            # For example, you can retrieve a depth image.
            # zed.retrieve_measure(depth, sl.MEASURE.DEPTH);

            # Always update IoT at the end of the grab loop
            # sliot.HubClient.update(depth);
            

            # If you don't need an image, send update()
            # It will send the default image and update the cloud.
            sliot.HubClient.update()


        else:
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
