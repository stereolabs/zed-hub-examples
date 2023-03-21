#!/bin/python3
import json
import requests
import time
import pymongo
from pymongo import MongoClient
from time import sleep

def get_current_milliseconds_round():
    return round(time.time() * 1000)

def load_config() :
    f = open('config_export_telemetry.json')
    if f.closed:
        print("Cannot open config file config_export_telemetry.json.")
        exit (1)
    config = json.load(f)
    global cloud_url
    cloud_url = config["cloud_url"]
    if cloud_url == "" :
        print("Wrong \"cloud_url\" value in config. Check config_export_telemetry.json.")
        exit(1)
    global cloud_url
    cloud_url = config["cloud_url"]
    if cloud_url == "" :
        print("Wrong \"cloud_url\" value in config. Check config_export_telemetry.json.")
        exit(1)
    global api_token
    api_token = config["api_token"]
    if api_token == "" :
        print("Wrong \"api_token\" value in config. Check config_export_telemetry.json.")
        exit(1)
    global workspace_id
    workspace_id = config["workspace_id"]
    if workspace_id == 0 :
        print("Wrong \"workspace_id\" value in config. Check config_export_telemetry.json.")
        exit(1)
    global http
    http = config["protocol"]
    if http != "http://" or http != "https://" :
        print("Wrong \"protocol\" value in config. Check config_export_telemetry.json.")
        exit(1)

def main() :
    # Load config file to get all the parameters to make requests to the server
    load_config()

    # Setup MongoDB Client
    client = MongoClient('localhost', 27017)
    db = client["telemetry"]
    collection = db["telemetry_ws_"+str(workspace_id)]
    # Make telemetry id unique index
    collection.create_index([("id",pymongo.ASCENDING)],unique=True)

    # Construct request
    headers = {'Content-Type' : 'application/json', 'Authorization': api_token}
    telemetry_url = http+cloud_url+'/api/v1/workspaces/'+str(workspace_id)+'/telemetry'

    # Get telemetries between now and 30 days before
    now = get_current_milliseconds_round()
    start = now - 30 * 24 * 60 * 60 * 1000
    end = now
    telemetry_url_parameter =telemetry_url + "?start=" + str(start) + "&end=" + str(end)
    
    # Pagination loop, we don't get telemetries all at once so we have to get them using multiple requests with the page parameter
    page = 1
    finished = False
    print("Retrieving telemetries from workspace "+str(workspace_id)+"...")
    while (not finished) :
        # Get request
        telemetry_url_page = telemetry_url_parameter + "&page=" + str(page)
        r = requests.get(telemetry_url_page, headers=headers)
        if r.status_code != 200 :
            print("Cannot get telemetries, error",r.status_code)
            print(r.text)
            finished = True
            exit(1)
        else :
            telemetry_data = r.json()
            telemetry_array = telemetry_data["telemetry"]
            # If telemetry array is empty there are no more telemetries to get (last page), exit
            if len(telemetry_array) == 0 :
                finished = True
            else :
                # Add telemetries to local db
                for telemetry_element in telemetry_array :
                    try :
                        collection.insert_one(telemetry_element)
                    except pymongo.errors.DuplicateKeyError :
                        print("Telemetry of id ",str(telemetry_element["id"])," was already inserted.")
        # Increment page
        page = page +1
        # Sleep 100ms to not be rate limited
        sleep(0.1)

    client.close()
    print("Done")

if __name__ == "__main__":
    main()