 
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

import argparse
import requests
import datetime
import json
import paramiko
import subprocess

def main():
    print('Hello ZED')
    hub_url = 'http://192.168.1.6'
    parser = argparse.ArgumentParser()
    parser.add_argument("--hosts", help="Path to a json list containings the devices, with 3 fields : ip, username, password", required=True)
    parser.add_argument("--workspace", help="Workspace ID of the devices", required=True)
    parser.add_argument("--token", help="API token generated at https://hub.stereolabs.com/token", required=True)
    args = parser.parse_args()

    host_conf_file = args.hosts

    with open(host_conf_file, "r") as f:
        hosts = json.loads(f.read())
    print('Creating devices from ', hosts)

    # Authorization header
    headers = {
        "Authorization": "Bearer " + args.token,
    }
    
    counter = 3

    # remove devices
    device_ids = []
    devices_url = hub_url + '/api/v1/workspaces/' + args.workspace + '/devices'
    devices_get = requests.get(url=devices_url, headers=headers)
    print(devices_get.text)
    devices_json = devices_get.json()
    for device in devices_get.json()["devices"]:
        if(device['name'].startswith('device_')):
            device_ids.append(device['id'])

    for device_id in device_ids:
        devices_delete_url = hub_url + '/api/v1/workspaces/' + args.workspace + '/devices/' + str(device_id)
        devices_delete = requests.delete(url=devices_delete_url, headers=headers)
        delete_json = devices_delete.text
        print('deleted', device_id, ':', delete_json)


    for device in hosts:
        counter = counter +1
        # Create the devices in the workspace
        devices_url = hub_url + '/api/v1/workspaces/' + args.workspace + '/devices'
        device_body = { 'name' : 'device_' + str(counter), 'description' : 'bulk creation sample'}
        devices_post = requests.post(url=devices_url, headers=headers, json=device_body)
        devices_json = devices_post.json()

        if not 'id' in devices_json:
            print('Invalid devices response from ' + devices_url)
            print(devices_post.text)
            continue

        device['id'] = devices_json["id"]
        device['install_token'] = devices_json["install_token"]
        print('Devices id created :', device['id'], " with install token", device['install_token'])

        ls = 'ls'
        one_liner = 'wget -O- ' + hub_url + '/api/v1/setup/' + device['install_token'] + ' > one_liner.sh'
        chmod_one_liner = 'sudo -S chmod +x ./one_liner.sh'
        silent_one_liner_install = 'sudo -S ls && ./one_liner.sh silent'
        ll = 'ls -l ./one_liner.sh'
        rem = 'rm ./one_liner.sh'

        ssh_client=paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=device['ip'],username=device['username'],password=device['password'])

        stdin,stdout,stderr=ssh_client.exec_command(rem)
        stdin,stdout,stderr=ssh_client.exec_command(one_liner)
        print(one_liner)
        print('download :',stdout.read().decode())


        stdin,stdout,stderr=ssh_client.exec_command(chmod_one_liner)
        stdin.write(device['password'] + '\n')
        stdin.flush()
        print('chmod :',stdout.read().decode(), stderr.read().decode())


        stdin,stdout,stderr=ssh_client.exec_command(silent_one_liner_install)
        stdin.write(device['password'] + '\n')
        lines = stdout.read().decode()
        for line in lines.split("\n"):
            print(line)
        print('installation :',stdout.read().decode(), stderr.read().decode())


if __name__ == "__main__":
    main()


