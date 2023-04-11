///////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2023, STEREOLABS.
//
// All rights reserved.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
///////////////////////////////////////////////////////////////////////////

#include <sl_iot/HubClient.hpp>
#include <opencv2/opencv.hpp>

using namespace std;
using namespace sl;
using namespace sl_iot;
using json = sl_iot::json;

template<typename T>
inline cv::Point2f cvt(T pt, sl::float2 scale) {
    return cv::Point2f(pt.x * scale.x, pt.y * scale.y);
}

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

vector<cv::Scalar> colors = {
    cv::Scalar(232, 176, 244, 255),
    cv::Scalar(175, 208, 25, 255),
    cv::Scalar(102, 205, 105, 255),
    cv::Scalar(185, 0, 255, 255),
    cv::Scalar(99, 107, 252, 255),
    cv::Scalar(252, 225, 8, 255),
    cv::Scalar(167, 130, 141, 255),
    cv::Scalar(194, 72, 113, 255)
};

int main(int argc, char **argv)
{
    // Create camera object
    std::shared_ptr<sl::Camera> p_zed;
    p_zed.reset(new sl::Camera());

    // Initialize the connection to ZED Hub
    STATUS_CODE status_iot = HubClient::connect("skeleton_app");
    if (status_iot != STATUS_CODE::SUCCESS)
    {
        std::cout << "HubClient " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    // Open the ZED camera
    sl::InitParameters init_params;
    init_params.camera_resolution = RESOLUTION::HD720;
    init_params.depth_mode = DEPTH_MODE::ULTRA;
    init_params.coordinate_system = COORDINATE_SYSTEM::RIGHT_HANDED_Y_UP;
    init_params.coordinate_units = UNIT::METER;
    init_params.depth_stabilization = 20;

    sl::ERROR_CODE status_zed = p_zed->open(init_params);
    if (status_zed != ERROR_CODE::SUCCESS)
    {
        HubClient::sendLog("Camera initialization error : " + std::string(toString(status_zed)), LOG_LEVEL::ERROR);
        exit(EXIT_FAILURE);
    }

    // Register the camera once it's open
    UpdateParameters update_params;
    status_iot = HubClient::registerCamera(p_zed, update_params);
    if (status_iot != STATUS_CODE::SUCCESS) {
        std::cout << "Camera registration error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    // Enable Position tracking (mandatory for object detection)
    std::cout << "Enable Position Tracking Module" << std::endl;
    sl::PositionalTrackingParameters track_params;
    track_params.enable_pose_smoothing = true;
    track_params.set_as_static = false;
    track_params.set_floor_as_origin = true;
    auto zed_error = p_zed->enablePositionalTracking(track_params);
    if (zed_error != ERROR_CODE::SUCCESS)
    {
        std::cout << sl::toVerbose(zed_error) << "\nExit program." << std::endl;
        p_zed->close();
        exit(EXIT_FAILURE);
    }

    // Enable the Body Tracking module
    std::cout << "Enable Body Tracking Module" << std::endl;
    sl::BodyTrackingParameters body_track_params;
    body_track_params.enable_tracking = true;
    body_track_params.enable_body_fitting = false; // smooth skeletons moves
    body_track_params.body_format = BODY_FORMAT::BODY_38;
    body_track_params.detection_model = BODY_TRACKING_MODEL::HUMAN_BODY_ACCURATE;
    zed_error = p_zed->enableBodyTracking(body_track_params);
    if (zed_error != ERROR_CODE::SUCCESS)
    {
        std::cout << sl::toVerbose(zed_error) << "\nExit program." << std::endl;
        p_zed->close();
        exit(EXIT_FAILURE);
    }

    // Runtime parameters
    RuntimeParameters rt_params;
    rt_params.measure3D_reference_frame = REFERENCE_FRAME::WORLD;

    // Body Tracking runtime parameters
    BodyTrackingRuntimeParameters body_track_rt_params;
    body_track_rt_params.detection_confidence_threshold = 50;

    // Images
    sl::Mat image(1280, 720, MAT_TYPE::U8_C4);
    cv::Mat cv_image;
    cv_image = slMat2cvMat(image);

    // 2D Drawing helpers
    Resolution camera_resolution = p_zed->getCameraInformation().camera_configuration.resolution;
    sl::float2 img_scale((float)cv_image.cols / (float)camera_resolution.width, (float)cv_image.rows / (float)camera_resolution.height);
    cv::Rect roi_render(0, 0, cv_image.cols, cv_image.rows);

    // Bodies to be streamed to ZED Hub
    sl::Bodies bodies;

    // Main loop
    while (true)
    {
        // Grab a new frame from the ZED
        status_zed = p_zed->grab(rt_params);
        if (status_zed != ERROR_CODE::SUCCESS)
            break;

        // Retrieve left image
        p_zed->retrieveImage(image, VIEW::LEFT, MEM::CPU, image.getResolution());
        
        // Retrieve bodies
        p_zed->retrieveBodies(bodies, body_track_rt_params);

        // Draw 2D skeletons
        for (int i = 0; i < bodies.body_list.size(); i++)
        {
            sl::BodyData& body = (bodies.body_list[i]);
            if (body.tracking_state == sl::OBJECT_TRACKING_STATE::OK)
            {
                cv::Scalar color = colors[body.id % colors.size()];

                // Skeleton joints
                for (auto& kp : body.keypoint_2d)
                {
                    auto cv_kp = cvt(kp, img_scale);
                    if (roi_render.contains(cv_kp))
                        cv::circle(cv_image, cv_kp, 3, color, -1);
                }

                // Skeleton bones
                for (auto& limb : BODY_38_BONES)
                {
                    auto kp_a = cvt(body.keypoint_2d[getIdx(limb.first)], img_scale);
                    auto kp_b = cvt(body.keypoint_2d[getIdx(limb.second)], img_scale);
                    if (roi_render.contains(kp_a) && roi_render.contains(kp_b))
                        cv::line(cv_image, kp_a, kp_b, color, 1);                                
                }
            }
        }

        // Always update Hub at the end of the grab loop to stream data to ZED Hub
        // Update the video stream/recording
        HubClient::update(p_zed, image);

        // Update the sl::Bodies stream
        HubClient::update(p_zed, bodies);
    }

    // Clear objects
    image.free();
    bodies.body_list.clear();
    
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

    status_iot = HubClient::disconnect();
    if (status_iot != STATUS_CODE::SUCCESS)
    {
        std::cout << "Terminating error " << status_iot << std::endl;
        exit(EXIT_FAILURE);
    }

    return 0;
}
