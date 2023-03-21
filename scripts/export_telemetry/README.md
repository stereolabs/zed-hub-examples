# ZED Hub Telemetry Export Plug

**Telemetries** sent on ZED Hub have a default maximum retention of 30 days. After that limit they are deleted from [hub.stereolabs.com](https://hub.stereolabs.com).

Here is a sample plug using Python and MongoDB that allows you to export those telemetry in your local database using **ZED Hub REST API**.

It exports telemetry between now and 30 days before from a workspace of yours in a MongoDB collection.

## Requirements

- Install [**MongoDB**](https://docs.mongodb.com/manual/installation/)
- Install python3 ([**on Linux**](https://docs.python-guide.org/starting/install3/linux/) or [**on Windows**](https://www.python.org/downloads/windows/))
- Install python modules requirements

```
pip3 install -r requirements.txt
```

## Config file

You first need to fill the `config_export_telemetry.json` configuration file to use the sample.

- `cloud_url` : The web address of the cloud server requested by the REST API (IP for local instances).
- `protocol` : Wether the server you're using uses http or https (http for local instances)
- `api_token` : The access token that you'll need  to use the REST API. Generate it by clicking on the account button in **ZED Hub** interface and **Create Token**.
- `workspace_id` : The ID of the workspace where you want to retrieve your telemetries from. Get it from the **Camera panel** URL (example: https://hub.stereolabs.com/workspaces/**1234567**/cameras)

## Run the sample

Run the sample with :
```
python3 export_telemetry.py
```

You can check your telemetries using `mongosh telemetry`.

## Sample Code Explanation

First, setup the MongoDB client using pymongo :
```python
    client = MongoClient('localhost', 27017)
```

Create the database and the collection named `telemetry_ws_yourworkspaceid` :
```python
    db = client["telemetry"]
    collection = db["telemetry_ws_"+str(workspace_id)]
```

To avoid duplicates if you use the program regularly, add a unique constraint on id :
```python
    collection.create_index([("id",pymongo.ASCENDING)],unique=True)
```

Construct your REST request on telemetry URL and headers, using start and end parameters. Check the [**REST API documentation**](https://www.stereolabs.com/docs/cloud/rest-api/telemetry/) if you want to add more parameters.
```python
    headers = {'Content-Type' : 'application/json', 'Authorization': api_token}
    telemetry_url = http+cloud_url+'/api/v1/workspaces/'+str(workspace_id)+'/telemetry'

    # Get telemetries between now and 30 days before
    now = get_current_milliseconds_round()
    start = now - 30 * 24 * 60 * 60 * 1000
    end = now
    telemetry_url_parameter =telemetry_url + "?start=" + str(start) + "&end=" + str(end)
```

We don't get telemetries all at once so we have to get them using multiple requests with the `page` parameter. You have to create a loop while incrementing `page` at each get request and store the results using pymongo. When we receive an empty array of telemetry we can stop requesting the telemetry server :
```python
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
```
