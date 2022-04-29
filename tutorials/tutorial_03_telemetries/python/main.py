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
    # initialize the communication to ZED Hub, with a zed camera.
    zed = sl.Camera() 
    status_iot = sliot.HubClient.connect("telemetry_app")

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
    
    status_zed = zed.open(init_params)
    if status_zed != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log("Camera initialization error : " + str(status_zed), sliot.LOG_LEVEL.ERROR)
        exit(1)

    # Enable the positionnal tracking and setup the loop
    positionnal_tracking_params = sl.PositionalTrackingParameters()
    positionnal_tracking_params.enable_area_memory = True
    status_zed = zed.enable_positional_tracking(positionnal_tracking_params)
    if status_zed != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log("Enabling positional tracking failed : " + str(status_zed), sliot.LOG_LEVEL.ERROR)
        exit(1)    

    cam_pose = sl.Pose()
    runtime_parameters = sl.RuntimeParameters()
    runtime_parameters.measure3D_reference_frame = sl.REFERENCE_FRAME.WORLD
    previous_timestamp = sl.Timestamp()
    previous_timestamp.set_milliseconds(0)

    # Main loop
    while True:
        status_zed = zed.grab()
        if status_zed != sl.ERROR_CODE.SUCCESS:
            break

        # Collect data
        current_timestamp = zed.get_timestamp(sl.TIME_REFERENCE.IMAGE)
        if current_timestamp.get_milliseconds() >= previous_timestamp.get_milliseconds() + 1000:
            zed.get_position(cam_pose)
            translation = cam_pose.get_translation()
            rot = cam_pose.get_rotation_vector()

            # Send the telemetry
            position_telemetry = {}
            position_telemetry["tx"] = translation.get()[0]
            position_telemetry["ty"] = translation.get()[1]
            position_telemetry["tz"] = translation.get()[2]
            position_telemetry["rx"] = rot[0]
            position_telemetry["ry"] = rot[1]
            position_telemetry["rz"] = rot[2]

            sliot.HubClient.send_telemetry("camera_position", position_telemetry)
            previous_timestamp = current_timestamp

        # Insert custom code here

        # In the end of a grab(), always call a update() on the cloud.
        sliot.HubClient.update()
        time.sleep(0.001)

    zed.disable_positional_tracking()

    # Cloe the camera
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
