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

import argparse
import random
import requests
from datetime import datetime

def main():
    # Current timestamp in ms
    now = datetime.timestamp(datetime.now()) * 1000

    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", help="Workspace ID of the telemetry", required=True)
    parser.add_argument("--device", help="Device ID of the telemetry", required=True)
    parser.add_argument("--token", help="API token generated at https://hub.stereolabs.com/token", required=True)
    parser.add_argument("--start", help="Timestamp of the beginning of the interval to send telemetry, in milliseconds (default: 2 hours ago)", default=now - 7.2E6)
    parser.add_argument("--end", help="Timestamp of the end of the interval to send telemetry, in milliseconds (default: now)", default=now)
    args = parser.parse_args()

    try:
        start_int = int(args.start)
        end_int = int(args.end)
    except:
        print("Timestamps must be integers. They are", args.start, args.end)
    
    if end_int <= start_int:
        print("The start timestamp must be before the end timestamp")
        return

    start_datetime = datetime.fromtimestamp(start_int / 1000)
    end_datetime = datetime.fromtimestamp(end_int / 1000)
    
    print("Sending telemetry to workspace", args.workspace, "from", start_datetime.strftime("%m/%d/%Y, %H:%M:%S"), "to", end_datetime.strftime("%m/%d/%Y, %H:%M:%S"), "as device", args.device)

    # Authorization header
    headers = {
        "Authorization": "Bearer " + args.token,
    }
    
    # Telemetry url
    url = "https://hub.stereolabs.com/api/v1/workspaces/" + args.workspace + "/devices/" + args.device + "/telemetry"
    
    # Data to send
    data = {"label": "people detection", "payload": {}}

    for i in range(15):
        data["timestamp"] = random.randint(start_int, end_int)
        data["payload"]["people_count"] = random.randint(1, 5)
        data["payload"]["accuracy_percent"] = random.randint(80, 99)
        res = requests.post(url=url, headers=headers, json=data)
        
        if res.ok:
        	print("Request success with code", res.status_code)
        else:
        	print("Request fail with code", res.status_code)


if __name__ == "__main__":
    main()
