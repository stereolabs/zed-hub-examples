 
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
import threading
import time
import json

run_zeds = True
zeds = []

def secondary_stream_loop(id, stream_name):
    global run_zeds

    print("Secondary stream (" + stream_name + ") opened")
    zed_image = sl.Mat(1280, 720, sl.MAT_TYPE.U8_C4)

    while run_zeds:
        # grab current image
        if zeds[id].grab() == sl.ERROR_CODE.SUCCESS:
            zeds[id].retrieve_image(zed_image, sl.VIEW.LEFT, sl.MEM.CPU, zed_image.get_resolution())
            status_code = sliot.HubClient.add_secondary_stream(stream_name, zed_image)
        else:
            run_zeds = False

def main():
    global run_zeds

    # Initialize the communication to ZED Hub
    status_iot = sliot.HubClient.connect("multi_stream_tutorial")
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_iot)
        exit(1)

    # Get detected cameras
    devList = sl.Camera.get_device_list()
    nb_detected_zed = len(devList)
    
    if nb_detected_zed == 0:
        print("No ZED Detected, exit program")
        exit(1)
    
    print(nb_detected_zed, "ZED detected")

    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD2K
    init_params.camera_fps = 30
    init_params.depth_mode = sl.DEPTH_MODE.NONE
    
    # Open every detected cameras
    for z in range(nb_detected_zed):
        init_params.set_from_camera_id(z)
        zeds.append(sl.Camera())
        err = zeds[z].open(init_params)

        if err == sl.ERROR_CODE.SUCCESS:
            cam_info = zeds[z].get_camera_information()
            print("serial number:", cam_info.serial_number, ", model:", cam_info.camera_model, ", status: opened")
        else:
            print(" Error:", err )
            zeds[z].close()
    
    # Register the first camera as the main one
    status_iot = sliot.HubClient.register_camera(zeds[0])
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Camera registration error ", status_iot)
        exit(1)
    
    # Thread loops for secondary streams
    thread_pool = [nb_detected_zed - 1]
    for z in range(1, nb_detected_zed):
        if zeds[z].is_opened():
            cam_info = zeds[z].get_camera_information()
            thread_pool[z - 1] = threading.Thread(target=secondary_stream_loop, args=(z, str(cam_info.serial_number)))
            thread_pool[z - 1].start()
    
    # Main loop
    while run_zeds:
        # Grab a new frame from the ZED
        status_zed = zeds[0].grab()
        
        if status_zed != sl.ERROR_CODE.SUCCESS:
            break

        # Always update IoT at the end of the grab loop
        sliot.HubClient.update()
    
    # Close the camera
    if zeds[0].is_opened():
        zed[0].close()
    
    # Wait for every thread to be stopped
    for z in range(1, nb_detected_zed):
        if zeds[z].is_opened():
            thread_pool[z - 1].join()
            zeds[z].close()

    # Close the communication with ZED Hub properly.
    status_iot = sliot.HubClient.disconnect()
    if status_iot != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status_iot)
        exit(1)
    
    return


if __name__ == "__main__":
    main()
