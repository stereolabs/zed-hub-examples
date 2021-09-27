#!/bin/bash

green_log="\033[32m"
normal_log="\033[0m"
red_log="\033[31m"
yellow_log="\e[1;33m"

# Configuration environment (sl_iot version, target etc)
if [[ -f "/tmp/sl_iot.profile" ]]; then
    source /tmp/sl_iot.profile
fi

# Check if docker is accessible from $USER
if [ -x "$(command -v docker)" ]; then
    grep -q docker /etc/group
    dock_a=$?
    getent group docker | grep -q "\b${USER}\b"
    dock_b=$?
    if [[ ${dock_a} -eq 1 || ${dock_b} -eq 1 ]]; then
        echo -e "${green_log}> Docker is only accessible in root. Adding user $USER to docker group...${normal_log}"
        if [[ dock_a -eq 1 ]]; then
            sudo groupadd docker
        fi
        sudo usermod -aG docker $USER
        echo -e "${green_log}> Done.${normal_log}"
        if [ $(id -gn) != "docker" ]; then
            exec sg docker "$0 $*"
        fi
    fi
else
    echo -e "${yellow_log}WARNING: Docker is not installed on your device. To be able to build this application, you need to install docker.\nMore info on how to install docker on https://docs.docker.com/get-docker/${normal_log}"
    exit 1
fi

arch=$(uname -m)

# Configure target (sl_iot version, jetpack, ubuntu version, cuda version etc)
reset_variables=0
if [[ -z $SL_IOT_VERSION ]] || [[ -z $SL_IOT_PLATFORM ]] || [[ -z $SL_IOT_CUDA_VERSION ]]; then
    reset_variables=1
else
    echo -e "${green_log}> Your current build configuration is :${normal_log}"
    echo "    - sl_iot version : $SL_IOT_VERSION"
    echo "    - target platform : $SL_IOT_PLATFORM"
    echo "    - cuda version : $SL_IOT_CUDA_VERSION"
    read -r -p "Do you want to redefine it? (y/N)" response
    response=${response,,} #to lower
    if [[ $response =~ ^(no|n| ) ]] || [[ -z $response  ]]; then
        reset_variables=0
    else
        reset_variables=1
    fi
fi

use_jetson=0
if [[ $reset_variables -eq 1 ]]; then
    if [[ "$arch" == "x86_64" ]]; then
    PS3='Do you want to build your application for running on NVIDIA Jetsons or x86_64 Ubuntu desktops? : '
        options=("NVIDIA Jetson" "x86_64 Ubuntu")
        select opt in "${options[@]}"
        do
            case $opt in
                "NVIDIA Jetson")
                    echo -e "${green_log}> NVIDIA Jetson selected.${normal_log}"
                    use_jetson=1
                    break
                    ;;
                "x86_64 Ubuntu")
                    echo -e "${green_log}> x86_64 Ubuntu selected.${normal_log}"
                    use_jetson=0
                    break
                    ;;
                *)
                    echo "Invalid option. Type \"1\" for NVIDIA Jetson and \"2\" for x86_64 Ubuntu."
                    ;;
            esac
        done
    else
        use_jetson=1
    fi
    if [[ $use_jetson -eq 1  ]]; then
        PS3='For which release of Jetpack do you want to build your application? : '
        options=("4.3" "4.4" "4.5")
        select opt in "${options[@]}"
        do
            case $opt in
                "4.3")
                    echo -e "${green_log}> Jetpack 4.3 selected.${normal_log}"
                    export SL_IOT_PLATFORM="jp4.3"
                    break
                    ;;
                "4.4")
                    echo -e "${green_log}> Jetpack 4.4 selected.${normal_log}"
                    export SL_IOT_PLATFORM="jp4.4"
                    break
                    ;;
                "4.5")
                    echo -e "${green_log}> Jetpack 4.5 selected.${normal_log}"
                    export SL_IOT_PLATFORM="jp4.5"
                    break
                    ;;
                *)
                    echo "Invalid option. Type \"1\" for Jetpack 4.3, \"2\" for Jetpack 4.4 and \"3\" for Jetpack 4.4."
                    ;;
            esac
        done
    else
        PS3='For which release of Ubuntu do you want to build your application? : '
        options=("18" "20")
        select opt in "${options[@]}"
        do
           case $opt in
              "18")
                    echo -e "${green_log}> Ubuntu 18 selected.${normal_log}"
                    export SL_IOT_PLATFORM="ubuntu18"
                    break
                    ;;
              "20")
                    echo -e "${green_log}> Ubuntu 20 selected.${normal_log}"
                    export SL_IOT_PLATFORM="ubuntu20"
                    break
                    ;;
              *)
                    echo "Invalid option. Type \"1\" for Ubuntu 18 and \"2\" for Ubuntu 20."
                    ;;
            esac
        done
    fi
    if [[ $SL_IOT_PLATFORM == "ubuntu18" ]]; then
        PS3='Which version of CUDA your application will be using? : '
        options=("10.0" "10.2" "11.0" "11.1")
        select opt in "${options[@]}"
        do
            case $opt in
                "10.0")
                    echo -e "${green_log}> CUDA 10.0 selected.${normal_log}"
                    export SL_IOT_CUDA_VERSION="10.0"
                    break
                    ;;
                "10.2")
                    echo -e "${green_log}> CUDA 10.2 selected.${normal_log}"
                    export SL_IOT_CUDA_VERSION="10.2"
                    break
                    ;;
                "11.0")
                    echo -e "${green_log}> CUDA 11.0 selected.${normal_log}"
                    export SL_IOT_CUDA_VERSION="11.0"
                    break
                    ;;
                "11.1")
                    echo -e "${green_log}> CUDA 11.1 selected.${normal_log}"
                    export SL_IOT_CUDA_VERSION="11.1"
                    break
                    ;;
                *)
                    echo "Invalid option. Type \"1\" for 10.0, \"2\" for 10.2, \"3\" for 11.0 and \"4\" for 11.1."
                    ;;
                esac
        done
    elif [[ $SL_IOT_PLATFORM == "ubuntu20" ]]; then
        PS3='Which version of CUDA your application will be using? : '
        options=("11.0" "11.1")
        select opt in "${options[@]}"
        do
            case $opt in
                "11.0")
                    echo -e "${green_log}> CUDA 11.0 selected.${normal_log}"
                    export SL_IOT_CUDA_VERSION="11.0"
                    break
                    ;;
                "11.1")
                    echo -e "${green_log}> CUDA 11.1 selected.${normal_log}"
                    export SL_IOT_CUDA_VERSION="11.1"
                    break
                    ;;
                *)
                    echo "Invalid option. Type \"1\" for 11.0 and \"2\" 11.1."
                    ;;
                esac
        done
    elif [[ $SL_IOT_PLATFORM == "jp4.3" ]]; then
        export SL_IOT_CUDA_VERSION="10.0"
    elif [[ $SL_IOT_PLATFORM == "jp4.4" ]]; then
        export SL_IOT_CUDA_VERSION="10.2"
    elif [[ $SL_IOT_PLATFORM == "jp4.5" ]]; then
        export SL_IOT_CUDA_VERSION="10.2"
    fi
    read -p "Which version of the sl_iot library your application will be using (ex : 0.23.0)?" choice
    export SL_IOT_VERSION=$choice
    echo -e "${green_log}> sl_iot v$SL_IOT_VERSION selected.${normal_log}"
    rm -rf /tmp/sl_iot.profile
    touch /tmp/sl_iot.profile
    chmod 777 /tmp/sl_iot.profile
    echo "export SL_IOT_VERSION=$SL_IOT_VERSION" >> /tmp/sl_iot.profile
    echo "export SL_IOT_PLATFORM=$SL_IOT_PLATFORM" >> /tmp/sl_iot.profile
    echo "export SL_IOT_CUDA_VERSION=$SL_IOT_CUDA_VERSION" >> /tmp/sl_iot.profile
fi

# Configure base docker image that is used for build and runtime
if [[ $SL_IOT_PLATFORM == "ubuntu"* ]]; then
    BASE_IMAGE_BUILD="stereolabs/iot:$SL_IOT_VERSION-devel-$SL_IOT_PLATFORM-cu$SL_IOT_CUDA_VERSION"
    BASE_IMAGE_RUNTIME="stereolabs\\/iot:$SL_IOT_VERSION-runtime-$SL_IOT_PLATFORM-cu$SL_IOT_CUDA_VERSION"
else
    use_jetson=1
    BASE_IMAGE_BUILD="stereolabs/iot:$SL_IOT_VERSION-build-jetson-$SL_IOT_PLATFORM"
    BASE_IMAGE_RUNTIME="stereolabs\\/iot:$SL_IOT_VERSION-runtime-jetson-$SL_IOT_PLATFORM"
fi

# If target is jetson and host is x86, activate emulation
if [[ "$arch" == "x86_64" && $use_jetson -eq 1 ]]; then
    echo -e "${green_log}> To build your application for Jetson's architecture aarch64, emulation for it must be activated on your device.${normal_log}"
    echo -e "${green_log}> Testing emulation for Jetson's architecture aarch64...${normal_log}"
    docker run --rm -t arm64v8/ubuntu:18.04 uname -m
    emu_activated=$?
    if [[ emu_activated -eq 0 ]]; then
        echo -e "${green_log}> Emulation for Jetson's architecture aarch64 is activated.${normal_log}"
    else
        echo -e "${green_log}> Emulation not activated, activating emulation for Jetson's architecture aarch64...${normal_log}"
        docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
        echo -e "${green_log}> Testing emulation for Jetson's architecture aarch64...${normal_log}"
        docker run --rm -t arm64v8/ubuntu:18.04 uname -m
        emu_activated=$?
        if [[ emu_activated -eq 0 ]]; then
            echo -e "${green_log}> Emulation for Jetson's architecture aarch64 is activated.${normal_log}"
        else
            echo -e "${red_log}ERROR: An error happened during emulation for Jetson's architecture aarch64 activation.${normal_log}"
            exit 1
        fi
    fi
fi


echo -e "${green_log}> Building your application... (pulling the docker images can take a bit of time)${normal_log}"
# Build the application in a docker container and copy the output result into the app folder
docker build -t mybuildimage --build-arg BASE_IMAGE=${BASE_IMAGE_BUILD} --file sources/Dockerfile ./../
build_success=$?

if [[ $build_success -eq 0 ]]; then
    docker create --name extract mybuildimage
    docker cp extract:/app_executable ./app
    docker rm extract
    echo -e "${green_log}> Your application has been successfully built.${normal_log}"
    echo -e "${green_log}> Packaging your application...${normal_log}"
    ## zip the data into a zip file
    if [ ! -f app.json  ]; then
        echo -e "${red_log}ERROR: Missing application manifest app.json, cannot package application.${normal_log}"
        exit 1
    fi
    if [ ! -f docker-compose.yml  ]; then
        echo -e "${red_log}ERROR: Missing docker-compose.yml, cannot package application.${normal_log}"
        exit 1
    fi
    echo -e "${green_log}> Updating your docker-compose.yml with runtime image...${normal_log}"
    # Update the docker-compose with the good base runtime image
    sed -r -i "s/^(\s*)(BASE\_IMAGE\s*:\s*stereolabs.+)/\\1BASE_IMAGE: ${BASE_IMAGE_RUNTIME}/" docker-compose.yml
    echo -e "${green_log}> Done.${normal_log}"
    # Package the application in a zip
    zip -r app.zip docker-compose.yml \
                   app.json \
                   app/* \
                   images/* \
                   README.md
    success_zip=$?
    if [[ $success_zip -eq 0 ]]; then
        echo -e "${green_log}> Your application has been successfully packaged in \"app.zip\".\n> You can now upload it on the application panel in the CMP interface.${normal_log}"
    else
        echo -e "${red_log}ERROR: An error happened during the packaging of the application, using zip.${normal_log}"
        exit 1
    fi
else
    echo -e "${red_log}ERROR: An error happened during your application build, please fix it before deploying your application.${normal_log}"
    exit 1
fi


