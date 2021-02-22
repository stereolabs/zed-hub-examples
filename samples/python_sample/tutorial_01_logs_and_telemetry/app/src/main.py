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
telemetry_topic = "/v1/devices/" + device_id + "/telemetry"


## Logs and telemetry MQTT Client
'''
client that send logs to the cloud
'''
client_id = "tuto_1_service"
client = mqttClient.Client(client_id)  # create new instance


####### alert MQTT #######
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT service connected to broker")
        # client.subscribe(my_subscribed_topic)
        # client.subscribe(my_subscribed_topic_2)
        
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

    # if message.topic in [my_subscribed_topic, my_subscribed_topic_2]:
    my_received_message = json.loads(str(message.payload.decode()))
    print("message received : ", my_received_message)


### message generation

def generate_log_message(level, message):
    message_dict = {}
    message_dict["timestamp"] = int(time.time() * 1000) # timestamp in ms
    message_dict["label"] = "Python log test"
    message_dict["level"] = level
    message_dict["payload"] = {} 
    message_dict["payload"]["message"] = message
    message_dict["application_name"] = app_name
    message_dict["application_token"] = app_token 
    json_message = json.dumps(message_dict)
    return json_message


def generate_telemetry_message(label = "python tuto test", message = "test succeeded"):
    message_dict = {}
    message_dict["timestamp"] = int(time.time() * 1000) # timestamp in ms
    message_dict["label"] = label
    message_dict["payload"] = {} #contains your data
    message_dict["payload"]["message"] = message 
    message_dict["payload"]["other data"] = 25 
    message_dict["application_name"] = app_name 
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
        current_time = time.time() # seconds

        log_message = generate_log_message(level = "INFO", message = "test succeeded")
        client.publish(logs_topic, log_message)

        telemetry_message = generate_telemetry_message(label = "python tuto test", message = "test succeeded")
        client.publish(telemetry_topic, telemetry_message)

    return 0



if __name__ == '__main__':
    main()