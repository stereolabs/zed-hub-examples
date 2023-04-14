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
import time


def main():
    # Initialize the communication to ZED Hub, with a zed camera.
    zed = sl.Camera() 
    status_hub = hub.HubClient.connect("telemetry_app")

    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_hub)
        exit(1)

    # Open the zed camera
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD2K
    
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

    # Enable Positional Tracking
    positional_tracking_params = sl.PositionalTrackingParameters()
    positional_tracking_params.enable_area_memory = True
    status_zed = zed.enable_positional_tracking(positional_tracking_params)
    if status_zed != sl.ERROR_CODE.SUCCESS:
        hub.HubClient.send_log("Enabling positional tracking failed : " + str(status_zed), hub.LOG_LEVEL.ERROR)
        exit(1)    

    cam_pose = sl.Pose()
    runtime_parameters = sl.RuntimeParameters()
    runtime_parameters.measure3D_reference_frame = sl.REFERENCE_FRAME.WORLD
    previous_timestamp = sl.Timestamp()
    previous_timestamp.set_milliseconds(0)

    # Main loop
    while True:
        # Grab a new frame from the ZED
        status_zed = zed.grab()
        if status_zed != sl.ERROR_CODE.SUCCESS:
            break

        current_timestamp = zed.get_timestamp(sl.TIME_REFERENCE.IMAGE)
        if current_timestamp.get_milliseconds() >= previous_timestamp.get_milliseconds() + 1000:
            # Retrieve camera position
            zed.get_position(cam_pose)
            translation = cam_pose.get_translation()
            rot = cam_pose.get_rotation_vector()

            # Send Telemetry
            position_telemetry = {}
            position_telemetry["tx"] = translation.get()[0]
            position_telemetry["ty"] = translation.get()[1]
            position_telemetry["tz"] = translation.get()[2]
            position_telemetry["rx"] = rot[0]
            position_telemetry["ry"] = rot[1]
            position_telemetry["rz"] = rot[2]

            hub.HubClient.send_telemetry("camera_position", position_telemetry)
            previous_timestamp = current_timestamp

        # Insert custom code here

        # In the end of a grab(), always call a update() on the cloud.
        hub.HubClient.update(zed)
        time.sleep(0.001)

    zed.disable_positional_tracking()

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
