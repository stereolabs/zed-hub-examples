// ########################################################################
// #
// # Copyright (c) 2023, STEREOLABS.
// #
// # All rights reserved.
// #
// # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// # A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// # OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// # SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// # LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// # DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// # THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
// #
// ########################################################################

#include <sl/Camera.hpp>
#include <sl_hub/HubClient.hpp>
#include <opencv2/opencv.hpp>

using namespace std;
using namespace sl;
using namespace sl_hub;
using json = sl_hub::json;

// Parameters, defined as global variables
bool draw_bboxes = true;
bool recordVideoEvent = true;
int nbFramesNoDetBtw2Events = 30; // number of frame
bool recordTelemetry = true;
float telemetryFreq = 10.f; // in seconds

cv::Mat slMat2cvMat(Mat &input)
{
    // Mapping between MAT_TYPE and CV_TYPE
    int cv_type = -1;
    switch (input.getDataType())
    {
    case MAT_TYPE::F32_C1:
        cv_type = CV_32FC1;
        break;
    case MAT_TYPE::F32_C2:
        cv_type = CV_32FC2;
        break;
    case MAT_TYPE::F32_C3:
        cv_type = CV_32FC3;
        break;
    case MAT_TYPE::F32_C4:
        cv_type = CV_32FC4;
        break;
    case MAT_TYPE::U8_C1:
        cv_type = CV_8UC1;
        break;
    case MAT_TYPE::U8_C2:
        cv_type = CV_8UC2;
        break;
    case MAT_TYPE::U8_C3:
        cv_type = CV_8UC3;
        break;
    case MAT_TYPE::U8_C4:
        cv_type = CV_8UC4;
        break;
    default:
        break;
    }

    return cv::Mat(input.getHeight(), input.getWidth(), cv_type, input.getPtr<sl::uchar1>(MEM::CPU));
}

// Parameter callbacks
void onDisplayParametersUpdate(FunctionEvent &event)
{
    event.status = 0;
    draw_bboxes = HubClient::getParameter<bool>("draw_bboxes", PARAMETER_TYPE::APPLICATION, draw_bboxes);
    HubClient::sendLog("New parameter : draw_bboxes modified", LOG_LEVEL::INFO);
}

void onVideoEventUpdate(FunctionEvent &event)
{
    event.status = 0;
    recordVideoEvent = HubClient::getParameter<bool>("recordVideoEvent", PARAMETER_TYPE::APPLICATION, recordVideoEvent);
    nbFramesNoDetBtw2Events = HubClient::getParameter<int>("nbFramesNoDetBtw2Events", PARAMETER_TYPE::APPLICATION, nbFramesNoDetBtw2Events);
    HubClient::sendLog("New parameters : recordVideoEvent or nbFramesNoDetBtw2Events modified", LOG_LEVEL::INFO);
}

void onTelemetryUpdate(FunctionEvent &event)
{
    event.status = 0;
    recordTelemetry = HubClient::getParameter<bool>("recordTelemetry", PARAMETER_TYPE::APPLICATION, recordTelemetry);
    telemetryFreq = HubClient::getParameter<float>("telemetryFreq", PARAMETER_TYPE::APPLICATION, telemetryFreq);
    HubClient::sendLog("New parameters : recordTelemetry or telemetryFreq modified", LOG_LEVEL::INFO);
}

int main(int argc, char **argv)
{
    // Create camera object
    auto p_zed = std::make_shared<sl::Camera>();

    // Initialize the communication to ZED Hub, with a zed camera.
    STATUS_CODE status_hub;
    status_hub = HubClient::connect("object_app");
    if (status_hub != STATUS_CODE::SUCCESS)
    {
        std::cout << "Initialization error " << status_hub << std::endl;
        exit(EXIT_FAILURE);
    }

    // Load application parameter file in development mode
    char *application_token = getenv("SL_APPLICATION_TOKEN");
    if (!application_token)
    {
        status_hub = HubClient::loadApplicationParameters("parameters.json");
        if (status_hub != STATUS_CODE::SUCCESS)
        {
            std::cout << "parameters.json file not found or malformated" << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    HubClient::setLogLevelThreshold(LOG_LEVEL::DEBUG, LOG_LEVEL::INFO);
    // Open the ZED camera
    sl::InitParameters initParameters;
    initParameters.camera_resolution = RESOLUTION::HD2K;
    initParameters.depth_mode = DEPTH_MODE::NEURAL;

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
    std::cout << "Enable Positional Tracking " << std::endl;
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
    zed_error = p_zed->enableObjectDetection(obj_det_params);
    if (zed_error != ERROR_CODE::SUCCESS)
    {
        std::cout << sl::toVerbose(zed_error) << "\nExit program." << std::endl;
        p_zed->close();
        return 1;
    }

    // Object Detection runtime parameters : detect person only
    // see the ZED Doc for the other available classes https://www.stereolabs.com/docs/api/group__Object__group.html#ga13b0c230bc8fee5bbaaaa57a45fa1177
    ObjectDetectionRuntimeParameters objectTracker_parameters_rt;
    objectTracker_parameters_rt.detection_confidence_threshold = 50;
    objectTracker_parameters_rt.object_class_filter.clear();
    objectTracker_parameters_rt.object_class_filter.push_back(sl::OBJECT_CLASS::PERSON);

    // Runtime parameters
    sl::RuntimeParameters rt_param;
    rt_param.measure3D_reference_frame = sl::REFERENCE_FRAME::CAMERA;

    /*********    App parameters      *************/

    CallbackParameters callback_display_param;
    callback_display_param.setParameterCallback("onDisplayParametersUpdate", "draw_bboxes", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
    HubClient::registerFunction(onDisplayParametersUpdate, callback_display_param);

    CallbackParameters callback_event_param;
    callback_event_param.setParameterCallback("onVideoEventUpdate", "recordVideoEvent|nbFramesNoDetBtw2Events", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
    HubClient::registerFunction(onVideoEventUpdate, callback_event_param);

    CallbackParameters callback_telemetry_param;
    callback_telemetry_param.setParameterCallback("onTelemetryUpdate", "recordTelemetry|telemetryFreq", CALLBACK_TYPE::ON_PARAMETER_UPDATE, PARAMETER_TYPE::APPLICATION);
    HubClient::registerFunction(onTelemetryUpdate, callback_telemetry_param);

    // get values defined by the ZED Hub interface.
    // Last argument is default value in case of failure
    draw_bboxes = HubClient::getParameter<bool>("draw_bboxes", PARAMETER_TYPE::APPLICATION, draw_bboxes);
    recordVideoEvent = HubClient::getParameter<bool>("recordVideoEvent", PARAMETER_TYPE::APPLICATION, recordVideoEvent);
    nbFramesNoDetBtw2Events = HubClient::getParameter<int>("nbFramesNoDetBtw2Events", PARAMETER_TYPE::APPLICATION, nbFramesNoDetBtw2Events);
    recordTelemetry = HubClient::getParameter<bool>("recordTelemetry", PARAMETER_TYPE::APPLICATION, recordTelemetry);
    telemetryFreq = HubClient::getParameter<float>("telemetryFreq", PARAMETER_TYPE::APPLICATION, telemetryFreq);

    /****************************/

    // Main loop
    int counter_no_detection = 0;
    sl::Objects objects;
    std::string event_reference = "";
    bool first_event_sent = false;
    sl::Timestamp prev_timestamp = p_zed->getTimestamp(TIME_REFERENCE::CURRENT);

    // Images
    sl::Mat imgLeftCustom(1280, 720, sl::MAT_TYPE::U8_C4);
    cv::Mat leftImageCpuCV;
    leftImageCpuCV = slMat2cvMat(imgLeftCustom);

    sl::Resolution image_raw_res = p_zed->getCameraInformation().camera_configuration.resolution;

    while (true)
    {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab(rt_param);
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

        int counter_reliable_objects = 0;
        for (int i = 0; i < objects.object_list.size(); i++)
        {
            if (objects.object_list[i].tracking_state == sl::OBJECT_TRACKING_STATE::OK)
            {
                counter_reliable_objects++;
            }
        }

        if (recordVideoEvent && counter_reliable_objects >= 1)
        {
            bool is_new_event = true;
            if (!first_event_sent || counter_no_detection >= nbFramesNoDetBtw2Events)
            {
                event_reference = "detected_person_" + std::to_string(current_ts.getMilliseconds());
                HubClient::sendLog("New Video Event defined", LOG_LEVEL::INFO);
            }
            else
            {
                // Do nothing, keep previous event reference --> The current frame will be defined as being part of the previous video event
                is_new_event = false;
            }

            EventParameters event_params;
            event_params.timestamp = current_ts.getMilliseconds();
            event_params.reference = event_reference;
            std::string event_label = "People Detection"; // or label of your choice
            json event2send;                              // Use to store all the data associated to the video event.
            event2send["message"] = "Current event as reference " + event_reference;
            event2send["nb_detected_person"] = objects.object_list.size();

            if (is_new_event || !first_event_sent)
            {
                HubClient::startVideoEvent(p_zed, event_label, event2send, event_params);
                first_event_sent = true;
            }
            // update every 10 s
            else if ((uint64)(current_ts.getMilliseconds() >= (uint64)(prev_timestamp.getMilliseconds() + (uint64)10 * 1000ULL)))
            {
                HubClient::updateVideoEvent(p_zed, event_label, event2send, event_params);
            }
            // else do nothing

            counter_no_detection = 0; // reset counter as someone as been detected
        }
        else
        {
            counter_no_detection++;
        }

        /*******************************/

        /*******     Define and send Telemetry   *********/
        // In this example we send every second the number of people detected and there mean distance to the camera

        if (recordTelemetry && (uint64)(current_ts.getMilliseconds() >= (uint64)(prev_timestamp.getMilliseconds() + (uint64)telemetryFreq * 1000ULL)))
        {
            float mean_distance = 0;
            // compute objects ( = people)  mean distance from camera. This value will be sent as telemetry
            for (int i = 0; i < objects.object_list.size(); i++)
            {
                mean_distance += (objects.object_list[i].position).norm();
            }

            if (objects.object_list.size() > 0)
            {
                mean_distance /= (float)objects.object_list.size();
            }

            // Send Telemetry
            sl_hub::json position_telemetry;
            position_telemetry["number_of_detection"] = objects.object_list.size();
            position_telemetry["mean_distance_from_cam"] = mean_distance;
            HubClient::sendTelemetry("object_detection", position_telemetry);
            prev_timestamp = current_ts;
        }

        /*******************************/
        /*******     Custom stream : Draw bboxes on custom stream   *********/
        if (draw_bboxes)
        {
            p_zed->retrieveImage(imgLeftCustom, sl::VIEW::LEFT, sl::MEM::CPU, imgLeftCustom.getResolution());

            float ratio_x = (float)leftImageCpuCV.cols / (float)image_raw_res.width;
            float ratio_y = (float)leftImageCpuCV.rows / (float)image_raw_res.height;

            for (int i = 0; i < objects.object_list.size(); i++)
            {
                if (objects.object_list[i].tracking_state == sl::OBJECT_TRACKING_STATE::OK)
                {
                    sl::uint2 tl = objects.object_list[i].bounding_box_2d[0];
                    sl::uint2 br = objects.object_list[i].bounding_box_2d[2];
                    cv::Rect ROI = cv::Rect(cv::Point2i(tl.x * ratio_x, tl.y * ratio_y), cv::Point2i(br.x * ratio_x, br.y * ratio_y));
                    cv::Scalar color = cv::Scalar(50, 200, 50, 255);
                    cv::rectangle(leftImageCpuCV, ROI, color, 2);
                }
            }

            HubClient::update(p_zed, imgLeftCustom);
        }

        else
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
