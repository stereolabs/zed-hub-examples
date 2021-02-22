# CMP-CLI

CMP-cli is a tool that allows you to use the cmp using command lines instead of the CMP interface.
The main feature consiste in running the packaged application with a command line


## Requirement



## Installation

- Make sure python3 is install on your device :

    ```
    sudo apt update
    sudo apt install python3-dev python3-pip
    ```

- Install the requirement packages :

    ```
    pip3 install -r requirements.txt
    ```

- Copy cmp-cli to **/usr/local/bin** :

    ```
    sudo cp cmp-cli /usr/local/bin
    ```


## Usage

### Deploy an app

Let's suppose you have a packaged app in a zip file. The following command lines allow to deploy the application as a **dev release** (meaning that the release is concidered as a test and not as a classic release) either on the current computer (if it is set up as a CMP device) or on any device of the local network:


On the host computer:
```
sudo cmp-cli run
```

Remotly on a device of the local network:

`$USER` : user name of the targeted device
`$IP` : IP of the targeted device

```
sudo cmp-cli run --host $USER@$IP
```

### Build the docker image

You can also use cmp-cli to test the build stage of your application. 

```
sudo cmp-cli build
```

Or emotly on a device of the local network:

`$USER` : user name of the targeted device
`$IP` : IP of the targeted device

```
sudo cmp-cli build --host $USER@$IP
```

