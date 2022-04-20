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
    # initialize the communication to zed hub, without a zed camera. 
    status = sliot.IoTCloud.init_no_zed("basic app")
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Initialization error ", status)
        exit()

    # set log level
    sliot.IoTCloud.set_log_level_threshold(
        sliot.LOG_LEVEL.INFO, sliot.LOG_LEVEL.INFO)
    
    # send a log
    sliot.IoTCloud.log("Initialization succeeded", sliot.LOG_LEVEL.INFO)

    # is your applicaiton connected to the cloud ?
    if sliot.IoTCloud.is_initialized() == sliot.STATUS_CODE.SUCCESS:
        sliot.IoTCloud.log("Application connected", sliot.LOG_LEVEL.INFO)

    # main loop : send a log every 15 secs
    i = 0
    while i < 10:
        sliot.IoTCloud.log("Log " + str(i) + " sent.", sliot.LOG_LEVEL.INFO)
        time.sleep(15)
        i = i + 1

    # Close the communication with zed hub properly.
    status = sliot.IoTCloud.stop()
    if status != sliot.STATUS_CODE.SUCCESS:
        print("Terminating error ", status)
        exit()
    
    return

if __name__ == "__main__":
    main()
