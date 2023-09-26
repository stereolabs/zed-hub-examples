 
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
import threading
import time

run_zeds = True
zeds = []

# Streams' loop to grab image
def stream_loop(zed : sl.Camera):
    global run_zeds

    zed_image = sl.Mat(1280, 720, sl.MAT_TYPE.U8_C4)

    while run_zeds:
        # grab current image
        if zed.grab() == sl.ERROR_CODE.SUCCESS:
            zed.retrieve_image(zed_image, sl.VIEW.LEFT, sl.MEM.CPU, zed_image.get_resolution())
            hub.HubClient.update(zed, zed_image)
        else:
            run_zeds = False

def main():
    global run_zeds

    # Initialize the communication to ZED Hub
    status_hub = hub.HubClient.connect("multi_stream_tutorial")
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_hub)
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
    for i in range(nb_detected_zed):
        init_params.set_from_camera_id(i)
        zed = sl.Camera()
        zeds.append(zed)
        err = zed.open(init_params)

        if err == sl.ERROR_CODE.SUCCESS:
            cam_info = zed.get_camera_information()
            print("serial number:", cam_info.serial_number, ", model:", cam_info.camera_model, ", status: opened")
        else:
            print("Error on camera", i, ":", err )
            zed.close()
    
        # Register the camera once it's open
        updateParameters = hub.UpdateParameters()

        # On Ubuntu desktop, on consumer-level GPUs, you don't have enough hardware encoder to stream multiple devices
        # and to record at the same time. https://en.wikipedia.org/wiki/Nvidia_NVENC
        # On Jetsons or on business-grade gpus, you can do whatever you want.
        updateParameters.enable_recording = False
        status_hub = hub.HubClient.register_camera(zeds[i], updateParameters)
        if status_hub != hub.STATUS_CODE.SUCCESS:
            print("Camera registration error ", status_hub)
            exit(1)
    
    # Thread loops for all streams
    thread_pool = {}
    for zed in zeds:
        if zed.is_opened():
            print("Starting a thread for zed", i, zed.get_camera_information().serial_number)
            thread_pool[zed] = threading.Thread(target=stream_loop, args=(zed,))
            thread_pool[zed].start()
    
    # Idle loop
    while run_zeds:
        time.sleep(1)
    
    # Wait for every thread to be stopped
    for zed in zeds:
        if zed.is_opened():
            thread_pool[zed].join()
            zed.close()

    # Close the communication with ZED Hub properly.
    status_hub = hub.HubClient.disconnect()
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Terminating error ", status_hub)
        exit(1)
    
    return


if __name__ == "__main__":
    main()
