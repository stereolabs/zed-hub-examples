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
from time import perf_counter 

# Parameters, defined as global variables
global draw_bboxes
global recordVideoEvent
global nbFramesNoDetBtw2Events
global recordTelemetry
global telemetryFreq

def convert_np_to_sl_mat(initial_image : sl.Mat, a : np.ndarray, deep_copy = True) -> sl.Mat:
    height, width, layers = a.shape
    print("###################")
    if deep_copy:
        mat_type = sl.MAT_TYPE.U8_C4
        resolution = sl.Resolution()
        resolution.width = width
        resolution.height = height

        pointer, read_only_flag = a.__array_interface__['data']
        # pointer = a.data
        mat = sl.Mat()
        # mat.init_mat_type(width, height, sl.MAT_TYPE.U8_C4)
        # mat.init_mat_resolution_cpu(resolution, mat_type, str(pointer), a.itemsize * width)
        mat.init_mat_cpu(width, height, mat_type, str(pointer), a.itemsize * width)
        # mat.init_mat_cpu(width, height, mat_type, "helloworld", a.itemsize * width)
        print("c1mat : ", mat.get_value(206, 206)[1])
        return mat
    # else:
    #     mat = sl.Mat()
    #     mat.init_mat_type(width, height, sl.MAT_TYPE.U8_C4)
    #     for i in range(width):
    #         for j in range(height):
    #             mat.set_value(i,j, a[j][i])
        
    #     print("c2mat : ", mat.get_value(0, 0)[1])
    #     return mat

def on_display_parameters_update():
    print("NOT IMPLEMENTED")
    exit(1)
    # event.status = 0;
    # draw_bboxes = HubClient::getParameter<bool>("draw_bboxes", PARAMETER_TYPE::APPLICATION, draw_bboxes);
    # HubClient::sendLog("New parameter : draw_bboxes modified",LOG_LEVEL::INFO);


def on_videoEvent_update():
    print("NOT IMPLEMENTED")
    exit(1)
    # event.status = 0;
    # recordVideoEvent = HubClient::getParameter<bool>("recordVideoEvent", PARAMETER_TYPE::APPLICATION, recordVideoEvent);
    # nbFramesNoDetBtw2Events = HubClient::getParameter<int>("nbFramesNoDetBtw2Events", PARAMETER_TYPE::APPLICATION, nbFramesNoDetBtw2Events);
    # HubClient::sendLog("New parameters : recordVideoEvent or nbFramesNoDetBtw2Events modified",LOG_LEVEL::INFO);


def on_telemetry_update():
    print("NOT IMPLEMENTED")
    exit(1)
    # event.status = 0;
    # recordTelemetry = HubClient::getParameter<bool>("recordTelemetry", PARAMETER_TYPE::APPLICATION, recordTelemetry);
    # telemetryFreq = HubClient::getParameter<float>("telemetryFreq", PARAMETER_TYPE::APPLICATION, telemetryFreq);
    # HubClient::sendLog("New parameters : recordTelemetry or telemetryFreq modified",LOG_LEVEL::INFO);


def main():

    draw_bboxes = True
    recordVideoEvent = True
    nbFramesNoDetBtw2Events = 30  # number of frame
    recordTelemetry = True
    telemetryFreq = 10.0  # in seconds

    # initialize the communication to zed hub, with a zed camera.
    zed = sl.Camera()
    status = sliot.HubClient.connect("object_app")

    if status != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status)
        exit()

    status = sliot.HubClient.register_camera(zed)
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status)
        exit()

    sliot.HubClient.set_log_level_threshold(
        sliot.LOG_LEVEL.DEBUG, sliot.LOG_LEVEL.INFO)

    # Open the zed camera
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD720
    init_params.depth_mode = sl.DEPTH_MODE.PERFORMANCE

    status = zed.open(init_params)

    if status != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log(
            "Camera initialization error : " + str(status), sliot.LOG_LEVEL.ERROR)
        exit(1)

    # Enable Position tracking (mandatory for object detection)
    track_params = sl.PositionalTrackingParameters()
    track_params.set_as_static = False
    status = zed.enable_positional_tracking(track_params)
    if status != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log(
            "Positionnal tracking initialization error : " + str(status), sliot.LOG_LEVEL.ERROR)
        exit(1)

    # Enable the Objects detection module
    object_detection_params = sl.ObjectDetectionParameters()
    object_detection_params.image_sync = True
    object_detection_params.enable_tracking = True
    object_detection_params.detection_model = sl.DETECTION_MODEL.MULTI_CLASS_BOX
    status = zed.enable_object_detection(object_detection_params)
    if status != sl.ERROR_CODE.SUCCESS:
        sliot.HubClient.send_log(
            "Object detection initialization error : " + str(status), sliot.LOG_LEVEL.ERROR)
        exit(1)

    # Object Detection runtime parameters : detect person only
    # see  the ZED Doc for the other available classes https://www.stereolabs.com/docs/api/group__Object__group.html#ga13b0c230bc8fee5bbaaaa57a45fa1177
    object_detection_runtime_params = sl.ObjectDetectionRuntimeParameters()
    object_detection_runtime_params.detection_confidence_threshold = 50
    object_detection_runtime_params.object_class_filter = []
    object_detection_runtime_params.object_class_filter.append(
        sl.OBJECT_CLASS.PERSON)

    runtime_params = sl.RuntimeParameters()
    runtime_params.measure3D_reference_frame = sl.REFERENCE_FRAME.CAMERA

    # get values defined by the CMP interface.
    # Last argument is default value in case of failuredraw_bboxes = sliot.HubClient.get_parameter_bool("draw_bboxes", sliot.PARAMETER_TYPE.APPLICATION, draw_bboxes)
    recordVideoEvent = sliot.HubClient.get_parameter_bool(
        "recordVideoEvent", sliot.PARAMETER_TYPE.APPLICATION, recordVideoEvent)
    nbFramesNoDetBtw2Events = sliot.HubClient.get_parameter_int(
        "nbFramesNoDetBtw2Events", sliot.PARAMETER_TYPE.APPLICATION, nbFramesNoDetBtw2Events)
    recordTelemetry = sliot.HubClient.get_parameter_bool(
        "recordTelemetry", sliot.PARAMETER_TYPE.APPLICATION, recordTelemetry)
    telemetryFreq = sliot.HubClient.get_parameter_float(
        "telemetryFreq", sliot.PARAMETER_TYPE.APPLICATION, telemetryFreq)

    counter_no_detection = 0
    objects = sl.Objects()
    event_reference = ""
    first_event_sent = False
    prev_timestamp = zed.get_timestamp(sl.TIME_REFERENCE.CURRENT)

    image_left_custom = sl.Mat(1280, 720, sl.MAT_TYPE.U8_C4)
    image_raw_res = zed.get_camera_information().camera_resolution

    # Main loop
    while True:
        status_zed = zed.grab(runtime_params)
        if status == sl.ERROR_CODE.SUCCESS:

            zed.retrieve_objects(objects, object_detection_runtime_params)
            # /*******     Define event   *********/
            # /*
            # Let's define a video event as a video on wich you can detect someone at least every 10 frames.
            # If nobody is detected for 10 frames, a new event is defined next time someone is detected.
            # Cf README.md to understand how to use the event_reference to define a new event.
            # */
            current_ts = objects.timestamp

            counter_reliable_objects = 0
            for obj in objects.object_list:
                if obj.tracking_state == sl.OBJECT_TRACKING_STATE.OK:
                    counter_reliable_objects = counter_reliable_objects + 1

            if (recordVideoEvent and counter_reliable_objects >= 1):
                is_new_event = True
                if (not first_event_sent) or (counter_no_detection >= nbFramesNoDetBtw2Events):
                    event_reference = "detected_person_" + \
                        str(current_ts.get_milliseconds())
                    sliot.HubClient.send_log(
                        "New Video Event defined", sliot.LOG_LEVEL.INFO)

                else:
                    # Do nothing, keep previous event reference --> The current frame will be defined as being part of the previous video event
                    is_new_event = False

                event_params = sliot.EventParameters()
                event_params.timestamp = current_ts.get_milliseconds()
                event_params.reference = event_reference
                event_label = "People Detection"  # or the label of your choice
                # Use to store all the data associated to the video event.
                event2send = {}
                event2send["message"] = "Current event as reference " + \
                    event_reference
                event2send["nb_detected_personn"] = len(objects.object_list)

                if (is_new_event or not first_event_sent):
                    sliot.HubClient.start_video_event(event_label, event2send, event_params)
                    first_event_sent = True

                #  update every 10 s
                elif current_ts.get_seconds() - prev_timestamp.get_seconds() >= 10:
                    sliot.HubClient.update_video_event(
                        event_label, event2send, event_params)
                # else do nothing

                counter_no_detection = 0  # reset counter as someone as been detected

            else:
                counter_no_detection = counter_no_detection + 1

            #  /*******************************/

            # /*******     Define and send Telemetry   *********/
            # // In this exemple we send every second the number of people detected and there mean distance to the camera
            if recordTelemetry and (current_ts.get_seconds() >= prev_timestamp.get_seconds() + telemetryFreq):
                mean_distance = 0.0
                # compute objects ( = people)  mean distance from camera. This value will be sent as telemetry
                for obj in objects.object_list:
                    mean_distance += np.linalg.norm(obj.position)

                if (len(objects.object_list) > 0):
                    mean_distance = mean_distance / \
                        (float)(len(objects.object_list))

                # Send Telemetry
                position_telemetry = {}
                position_telemetry["number_of_detection"] = len(
                    objects.object_list)
                position_telemetry["mean_distance_from_cam"] = mean_distance
                sliot.HubClient.send_telemetry(
                    "object_detection", position_telemetry)
                prev_timestamp = current_ts

            #    /*******************************/
            #     /*******     Custom stream : Draw bboxes on custom stream   *********/
            if(draw_bboxes):
                zed.retrieve_image(image_left_custom, sl.VIEW.LEFT,
                                   sl.MEM.CPU, image_left_custom.get_resolution())
                
                # Retrieve the image in a numpy array sharing the same pointer than the sl.Mat
                # So that the modifications we'll do will persist when giving back the sl.Mat to the update() method
                image_left_ocv = image_left_custom.get_data(sl.MEM.CPU, False)

                alpha_channel = image_left_ocv[:,:,3]
                rgb_channels = image_left_ocv[:,:,:3]
                rows, cols, layers = image_left_ocv.shape
                ratio_x = (float)(cols/(float)(image_raw_res.width))
                ratio_y = (float)(rows/(float)(image_raw_res.height))

                for obj in objects.object_list:
                    if (obj.tracking_state == sl.OBJECT_TRACKING_STATE.OK):
                        tl = obj.bounding_box_2d[0];
                        br = obj.bounding_box_2d[2];
                        cv2.rectangle(image_left_ocv
                                        , ((int)(tl[0]*ratio_x), (int)(tl[1]*ratio_y))
                                        ,((int)(br[0]*ratio_x), (int)(br[1]*ratio_y))
                                        , (50, 200, 50)
                                        , 4)

                image_left_custom.timestamp = sl.get_current_timestamp()
                print(image_left_custom.timestamp.get_milliseconds())
                sliot.HubClient.update(image_left_custom)

            else:
                # Always update IoT at the end of the grab loop
                sliot.HubClient.update()


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
