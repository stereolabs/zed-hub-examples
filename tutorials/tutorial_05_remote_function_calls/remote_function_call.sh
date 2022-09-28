#!/bin/sh

if [ $# -ne 6 ]; then
    echo 'Wrong number of arguments, please use the script like this: '
    echo './remote_function_call.sh num1 num2 cloud_url workspace_id device_id api_token'
else
    num1=$1
    num2=$2
    cloud_url=$3
    workspace_id=$4
    device_id=$5
    api_token=$6
    echo 
    curl -s -H "Content-Type: application/json" \
       -H "Authorization: ${api_token}"\
       -X POST ${cloud_url}/workspaces/${workspace_id}/devices/${device_id}/functions/tuto05_add \
       -d "{ \
       \"parameters\": { \
         \"num1\": ${num1}, \
	 \"num2\": ${num2} \
         }\
       }"
fi
