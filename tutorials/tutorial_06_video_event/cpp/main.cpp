#include <stdio.h>
#include <string.h>
#include <chrono>

#include <sl/Camera.hpp>
#include <sl_hub/HubClient.hpp>

using namespace std;
using namespace sl;
using namespace sl_hub;
using json = sl_hub::json;

int main(int argc, char **argv)
{
    // Create camera object
    std::shared_ptr<sl::Camera> p_zed;
    p_zed.reset(new sl::Camera());

    // Initialize the communication to ZED Hub, with a zed camera.
    STATUS_CODE status_hub = HubClient::connect("event_app");
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "HubClient " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    // Open the ZED camera
    sl::InitParameters initParameters;
    initParameters.camera_resolution = RESOLUTION::HD2K;
    initParameters.depth_mode = DEPTH_MODE::PERFORMANCE;
    sl::ERROR_CODE status_zed = p_zed->open(initParameters);
    if (status_zed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Camera initialization error : " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    // Register the camera once it's open
    UpdateParameters updateParameters;
    status_hub = HubClient::registerCamera(p_zed, updateParameters);
    if (status_hub != STATUS_CODE::SUCCESS) {
        std::cout << "Camera registration error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    // Enable Position tracking (mandatory for object detection)
    sl::PositionalTrackingParameters track_params;
    track_params.set_as_static = false;
    auto zed_error = p_zed->enablePositionalTracking(track_params);
    if (zed_error != ERROR_CODE::SUCCESS)
    {
        std::cout << sl::toVerbose(zed_error) << "\nExit program." << std::endl;
        p_zed->close();
        return 1;
    }

    // Enable the Objects detection module
    std::cout << "Enable Object Detection Module" << std::endl;
    sl::ObjectDetectionParameters obj_det_params;
    obj_det_params.image_sync = true;
    obj_det_params.enable_tracking = false;
    obj_det_params.detection_model = sl::OBJECT_DETECTION_MODEL::MULTI_CLASS_BOX_FAST;
    zed_error = p_zed->enableObjectDetection(obj_det_params);
    if (zed_error != ERROR_CODE::SUCCESS)
    {
        std::cout << sl::toVerbose(zed_error) << "\nExit program." << std::endl;
        p_zed->close();
        return 1;
    }

    // Object Detection runtime parameters : detect person only
    ObjectDetectionRuntimeParameters objectTracker_parameters_rt;
    objectTracker_parameters_rt.detection_confidence_threshold = 50;
    objectTracker_parameters_rt.object_class_filter.clear();
    objectTracker_parameters_rt.object_class_filter.push_back(sl::OBJECT_CLASS::PERSON);

    // Main loop
    int counter_no_detection = 0;
    sl::Objects objects;
    std::string event_reference = "";
    bool first_event_sent = false;
    sl::Timestamp last_ts = 0;
    while (true)
    {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab();
        if (status_zed != ERROR_CODE::SUCCESS)
            break;

        p_zed->retrieveObjects(objects, objectTracker_parameters_rt);

        /*******     Define event   *********/
        /*
        Let's define a video event as a video on which you can detect someone at least every 10 frames.
        If nobody is detected for 10 frames, a new event is defined next time someone is detected.
        Cf README.md to understand how to use the event_reference to define a new event.
        */

        sl::Timestamp current_ts = objects.timestamp;
        if (objects.object_list.size() >= 1 && current_ts.getSeconds() - last_ts.getSeconds() >= 2)
        {
            bool new_event = true;
            if (counter_no_detection >= 10 || !first_event_sent)
            {
                event_reference = "detected_person_" + std::to_string(current_ts.getMilliseconds());
            }
            else
            {
                // keep previous event reference --> The current frame will be defined as being part of the previous video event
                new_event = false;
            }
            EventParameters event_params;
            event_params.timestamp = current_ts.getMilliseconds();
            event_params.reference = event_reference;
            std::string event_label = "People Detection"; // or label of your choice
            json event2send;                              // Use to store all the data associated to the video event.
            event2send["message"] = "Current event as reference " + event_reference;
            event2send["nb_detected_person"] = objects.object_list.size();

            if (new_event || !first_event_sent)
            {
                HubClient::startVideoEvent(p_zed, event_label, event2send, event_params);
                first_event_sent = true;
                std::cout << "Event started" << std::endl;
            }
            else
            {
                HubClient::updateVideoEvent(p_zed, event_label, event2send, event_params);
                std::cout << "Event updated" << std::endl;
            }
            counter_no_detection = 0; // reset counter as someone as been detected
            last_ts = current_ts;
        }
        else if (current_ts.getSeconds() - last_ts.getSeconds() >= 2)
        {
            counter_no_detection++;
        }
        /*******************************/

        // Always update Hub at the end of the grab loop
        HubClient::update(p_zed);
    }

    // Handling camera error
    if (status_zed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Grab failed, restarting camera. " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        p_zed->close();
        sl::ERROR_CODE e = sl::Camera::reboot(p_zed->getCameraInformation().serial_number);
    }

    // Close the camera
    if (p_zed->isOpened())
        p_zed->close();

    status_hub = HubClient::disconnect();
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Terminating error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    return 0;
}
