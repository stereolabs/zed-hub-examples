import os
import sys
import json
import random
import paho.mqtt.client as mqttClient
import time
import requests
import socket
import datetime
import time




##########################
#   MQTT configuration   #
##########################

broker_address = os.environ.get("SL_MQTT_HOST")  # Broker address
mqtt_port = int(os.environ.get("SL_MQTT_PORT"))  # Broker port
mqtt_user = "application"  # Connection username
app_token = os.environ.get("SL_APPLICATION_TOKEN")  # Connection password


app_name = os.environ.get("SL_APPLICATION_NAME")  # Connection password
device_id = str(os.environ.get("SL_DEVICE_ID"))
logs_topic = "/v1/devices/" + device_id + "/logs"


## Topic where the cloud publishes parameter modifications
app_ID = str(os.environ.get("SL_APPLICATION_ID"))
update_app_param_topic = "/v1/devices/" + device_id + "/apps/"+ app_ID + "/twin/update"


## Logs and telemetry MQTT Client
'''
client that listen to the app parameter modifications
'''
client_id = "tuto_2_service"
client = mqttClient.Client(client_id)  # create new instance




## Parameters 
"""
Get the values of the parameters defined in the app.json file. These parameters are accessible in the CMp interface and are modifiable.
"""

first_param = os.environ.get("SL_PARAM_APP_my_first_param")
second_param = float(os.environ.get("SL_PARAM_APP_my_second_param"))


def update_parameters(new_app_parameters):
    '''
    On new parameters, modify the environment variable value. 
    Then get the new environment variable value.
    '''
    for key, value in new_app_parameters.items():
        if "deployment.parameters.requested" in key:
            param_name = "SL_PARAM_APP_" + key.split("parameters.requested.")[-1]
            param_value = str(value)
            os.environ[param_name] = param_value
            print(param_name, "set to", param_value)
        else:
            print("the key",  key, " has been modified but is not an app parameter")

    ## get new value
    global first_param, second_param
    first_param = os.environ.get("SL_PARAM_APP_my_first_param")
    second_param = float(os.environ.get("SL_PARAM_APP_my_second_param"))

    ## send a log to notify new values
    my_message = "New values for parameters are first_param = "+ str(first_param) + " and second_param = " + str(second_param)
    log_message = generate_log_message(level = "INFO", message = my_message)
    client.publish(logs_topic, log_message)



####### alert MQTT #######
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT service connected to broker")
        client.subscribe(update_app_param_topic) 
        
    else:
        print("MQTT service Connection failed")


def on_disconnect(client, userdata,rc=0):
    print("MQTT service disconnected")


def on_publish(client, userdata, result):  # create function for callback
    print("message published")
    pass


def on_message(client, inference_thread_manager, message):
    '''
    Note that you must subscribe a topic to be able to receive messages (and of course a message must be published on this topic)
    '''

    if message.topic == update_app_param_topic:
        print("New parameter update received")
        new_app_parameters = json.loads(str(message.payload.decode()))
        update_parameters(new_app_parameters)


### message generation
def generate_log_message(level, message):
    message_dict = {}
    message_dict["timestamp"] = int(time.time() * 1000) # timestamp in ms
    message_dict["label"] = "Python param test"
    message_dict["level"] = level
    message_dict["payload"] = {} 
    message_dict["payload"]["message"] = message
    message_dict["application_name"] = app_name
    message_dict["application_token"] = app_token 
    json_message = json.dumps(message_dict)
    return json_message


def main():
    #################       MQTT           ##################
    ## Starts alert mqtt client
    client.username_pw_set(mqtt_user, password=app_token)  # set username and password

    client.on_connect = on_connect  # attach function to callback
    client.on_disconnect = on_disconnect  # attach function to callback
    client.on_message = on_message  # attach function to callback
    client.on_publish = on_publish  # attach function to callback

    print("Connecting to broker")
    client.connect(broker_address, port=mqtt_port)  # connect to broker

    #################        start MQTT CLIENT thread            ##################
    client.loop_start()

    #################                   ##################
    while True:
        time.sleep(10)



    return 0



if __name__ == '__main__':
    main()