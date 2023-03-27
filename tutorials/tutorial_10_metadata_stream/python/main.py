 
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
import cv2

colors = [
    [232, 176, 244],
    [175, 208, 25],
    [102, 205, 105],
    [185, 0, 255],
    [99, 107, 252],
    [252, 225, 8],
    [167, 130, 141],
    [194, 72, 113]
 ]

def cvt(pt, scale):
    return[pt[0] * scale[0], pt[1] * scale[1]]


def main():
    global colors

    # Initialize the connection to ZED Hub
    status_iot = sliot.HubClient.connect("skeleton_tutorial")
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_iot)
        exit(1)

    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD720
    init_params.depth_mode = sl.DEPTH_MODE.ULTRA
    init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP
    init_params.coordinate_units = sl.UNIT.METER
    init_params.camera_fps = 20
    
    # Open the ZED camera
    zed = sl.Camera()
    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        print("Error:", err)
        zed.close()
    
    # Register the camera once it's open
    update_params = sliot.UpdateParameters()
    status_iot = sliot.HubClient.register_camera(zed, update_params)
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Camera registration error:", status_iot)
        exit(1)
    
    # Enable Position tracking (mandatory for object detection)
    print("Enable Position Tracking Module")
    track_params = sl.PositionalTrackingParameters()
    track_params.enable_pose_smoothing = True
    track_params.set_as_static = False
    track_params.set_floor_as_origin = True
    err = zed.enable_positional_tracking(track_params)
    if err != sl.ERROR_CODE.SUCCESS:
        print("Error:", err)
        print("Exit program.")
        zed.close()
        exit(1)
    
    # Enable the Body Tracking module
    print("Enable Body Tracking Module")
    body_track_params = sl.BodyTrackingParameters()
    body_track_params.enable_tracking = True
    body_track_params.enable_body_fitting = False; # smooth skeletons moves
    body_track_params.body_format = sl.BODY_FORMAT.BODY_38
    body_track_params.detection_model = sl.BODY_TRACKING_MODEL.HUMAN_BODY_ACCURATE
    err = zed.enable_body_tracking(body_track_params)
    if err != sl.ERROR_CODE.SUCCESS:
        print("Error:", err)
        print("Exit program.")
        zed.close()
        exit(1)
        
    # Runtime parameters
    rt_params = sl.RuntimeParameters()
    rt_params.measure3D_reference_frame = sl.REFERENCE_FRAME.WORLD

    # Body Tracking runtime parameters
    body_track_rt_params = sl.BodyTrackingRuntimeParameters()
    body_track_rt_params.detection_confidence_threshold = 50
    
    # Image
    image = sl.Mat(1280, 720, sl.MAT_TYPE.U8_C4)
    cv_image = image.get_data()

    # 2D Drawing helpers
    camera_resolution = zed.get_camera_information().camera_configuration.resolution
    img_scale = [cv_image.shape[1] / camera_resolution.width, cv_image.shape[0] / camera_resolution.height]

    # Bodies to be streamed to ZED Hub
    bodies = sl.Bodies()

    # Main loop
    while True:
        # Grab a new frame from the ZED
        status_zed = zed.grab()

        if status_zed != sl.ERROR_CODE.SUCCESS:
            break

        # Retrieve left image
        zed.retrieve_image(image, sl.VIEW.LEFT)

        # Retrieve bodies
        zed.retrieve_bodies(bodies, body_track_rt_params)

        # Draw 2D skeletons
        for body in bodies.body_list:
            if body.tracking_state == sl.OBJECT_TRACKING_STATE.OK:
                color = colors[body.id % len(colors)]
                
                # Skeleton joints
                for kp in body.keypoint_2d:
                    cv_kp = cvt(kp, img_scale)
                
                    if cv_kp[0] < cv_image.shape[1] and cv_kp[1] < cv_image.shape[0]:
                        cv2.circle(cv_image, (int(cv_kp[0]), int(cv_kp[1])), 3, color, -1)

                # Skeleton bones
                for limb in sl.BODY_38_BONES:
                    kp_a = cvt(body.keypoint_2d[sl.get_idx_34(limb[0])], img_scale)
                    kp_b = cvt(body.keypoint_2d[sl.get_idx_34(limb[1])], img_scale)

                    if 0 < kp_a[0] < cv_image.shape[1] and 0 < kp_a[1] < cv_image.shape[0] and 0 < kp_b[0] < cv_image.shape[1] and 0 < kp_b[1] < cv_image.shape[0]:
                        cv2.line(cv_image, (int(kp_a[0]), int(kp_a[1])), (int(kp_b[0]), int(kp_b[1])), color, 1)

        # Always update Hub at the end of the grab loop to stream data to ZED Hub
        # Update the video stream/recording
        sliot.HubClient.update(zed, image)

        # Update the sl.Bodies stream
        sliot.HubClient.update_bodies(zed, bodies)
    
    # Handling camera error
    if status_zed != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log("Grab failed, restarting camera. " + str(status_zed), sliot.LOG_LEVEL.ERROR)
        zed.close()
        sl.Camera.reboot(zed.get_camera_information().serial_number)
    
    # Close the camera
    elif zed.is_opened():
        zed.close()

    # Close the communication with ZED Hub properly.
    status_iot = sliot.HubClient.disconnect()
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status_iot)
        exit(1)


if __name__ == "__main__":
    main()
