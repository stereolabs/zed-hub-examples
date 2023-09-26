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

import pyzed.sl_hub as hub
import time


def main():
    # Initialize the communication to ZED Hub, without a zed camera.
    status_hub = hub.HubClient.connect("basic_app")
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Initialization error ", status_hub)
        exit(1)

    # Set log level
    hub.HubClient.set_log_level_threshold(
        hub.LOG_LEVEL.INFO, hub.LOG_LEVEL.INFO)
    
    # Send a log
    hub.HubClient.send_log("Initialization succeeded", hub.LOG_LEVEL.INFO)

    # is your application connected to the cloud ?
    if hub.HubClient.is_initialized() == hub.STATUS_CODE.SUCCESS:
        hub.HubClient.send_log("Application connected", hub.LOG_LEVEL.INFO)

    # Main loop : send a log every 15 secs
    i = 0
    while True:
        hub.HubClient.send_log("Log " + str(i) + " sent.", hub.LOG_LEVEL.INFO)
        time.sleep(15)
        i += 1

    # Close the communication with ZED Hub properly.
    status_hub = hub.HubClient.disconnect()
    if status_hub != hub.STATUS_CODE.SUCCESS:
        print("Terminating error ", status_hub)
        exit(1)
    
    return


if __name__ == "__main__":
    main()
